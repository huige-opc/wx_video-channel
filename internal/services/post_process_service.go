package services

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"wx_channel/internal/config"
	"wx_channel/internal/utils"
)

// PostProcessService 视频下载完成后的自动后处理服务：
//   - 步骤 1: 调用 extract_audio.py --file <mp4> 生成同名 mp3
//   - 步骤 2: 调用 transcribe.py    --file <mp3> 生成同名 md
//   - 步骤 3: 调用 clean.py         --file <md>  生成同名 _清洗版.md
//
// 通过 buffered channel + N 个 worker goroutine 消费，避免阻塞下载主流程。
// 是否启用由 config.AutoTranscribe 控制（默认 true）。
// 清洗步骤通过 cleanMu 全局互斥，避免多个 claude(node) 冷启并发烧 CPU。
type PostProcessService struct {
	queue    chan string
	stopOnce sync.Once
	stop     chan struct{}
	wg       sync.WaitGroup
	toolDir  string     // wx_video-channel 目录（含 extract_audio.py / transcribe.py / clean.py）
	cleanMu  sync.Mutex // 清洗互斥：同时只允许一个 claude 进程在跑
}

var (
	globalPostProcess     *PostProcessService
	globalPostProcessOnce sync.Once
)

// GetPostProcessService 返回单例。首次调用会启动 worker。
func GetPostProcessService() *PostProcessService {
	globalPostProcessOnce.Do(func() {
		globalPostProcess = newPostProcessService()
		globalPostProcess.start()
	})
	return globalPostProcess
}

func newPostProcessService() *PostProcessService {
	cfg := config.Get()
	workers := 2
	if cfg != nil && cfg.PostProcessWorker > 0 {
		workers = cfg.PostProcessWorker
	}

	// 队列容量按 worker 数放大，避免突发下载填满
	queueCap := workers * 32
	if queueCap < 64 {
		queueCap = 64
	}

	toolDir := resolveToolDir()

	svc := &PostProcessService{
		queue:   make(chan string, queueCap),
		stop:    make(chan struct{}),
		toolDir: toolDir,
	}
	_ = workers // start() 会再读一次配置
	return svc
}

// resolveToolDir 拿到 wx_video-channel 目录：
// 1) 优先用 exe 所在目录
// 2) 兜底用当前工作目录
func resolveToolDir() string {
	if exe, err := os.Executable(); err == nil {
		return filepath.Dir(exe)
	}
	wd, _ := os.Getwd()
	return wd
}

func (s *PostProcessService) start() {
	cfg := config.Get()
	workers := 2
	if cfg != nil && cfg.PostProcessWorker > 0 {
		workers = cfg.PostProcessWorker
	}
	utils.Info("✓ 自动后处理已启用 (workers=%d, tool_dir=%s)", workers, s.toolDir)
	for i := 0; i < workers; i++ {
		s.wg.Add(1)
		go s.worker(i + 1)
	}
}

// Enqueue 把 mp4 路径丢进队列。非阻塞：满时丢弃并打日志。
// 未启用（AutoTranscribe=false）时直接返回。
func (s *PostProcessService) Enqueue(videoPath string) {
	if s == nil {
		return
	}
	cfg := config.Get()
	if cfg == nil || !cfg.AutoTranscribe {
		return
	}
	if !strings.EqualFold(filepath.Ext(videoPath), ".mp4") {
		return
	}
	select {
	case s.queue <- videoPath:
		utils.Info("🎙️ [后处理] 已入队: %s", filepath.Base(videoPath))
	default:
		utils.Warn("⚠️ [后处理] 队列已满，跳过: %s", filepath.Base(videoPath))
	}
}

// Stop 优雅停止（关闭时调用）
func (s *PostProcessService) Stop() {
	if s == nil {
		return
	}
	s.stopOnce.Do(func() {
		close(s.stop)
		close(s.queue)
	})
	s.wg.Wait()
}

func (s *PostProcessService) worker(id int) {
	defer s.wg.Done()
	for {
		select {
		case <-s.stop:
			return
		case videoPath, ok := <-s.queue:
			if !ok {
				return
			}
			s.process(id, videoPath)
		}
	}
}

func (s *PostProcessService) process(workerID int, videoPath string) {
	name := filepath.Base(videoPath)
	// 提前检查视频文件是否存在（可能已被删/移走）
	if _, err := os.Stat(videoPath); err != nil {
		utils.Warn("⚠️ [后处理#%d] 视频不存在，跳过: %s", workerID, name)
		return
	}

	mdPath := replaceExt(videoPath, ".md")
	cleanedPath := replaceExt(videoPath, "_清洗版.md")

	// 清洗版已存在 → 全部完成，啥都不做
	if _, err := os.Stat(cleanedPath); err == nil {
		utils.Info("⏭️ [后处理#%d] 清洗版已存在，跳过: %s", workerID, name)
		return
	}

	mp3Path := replaceExt(videoPath, ".mp3")

	// Step 1: 抽音频
	if _, err := os.Stat(mp3Path); err != nil {
		utils.Info("🎧 [后处理#%d] 抽音频: %s", workerID, name)
		if err := s.runPython("extract_audio.py", videoPath); err != nil {
			utils.Warn("⚠️ [后处理#%d] 抽音频失败: %s (%v)", workerID, name, err)
			return
		}
	}

	// 二次校验 mp3
	if _, err := os.Stat(mp3Path); err != nil {
		utils.Warn("⚠️ [后处理#%d] 抽音频后仍找不到 mp3: %s", workerID, name)
		return
	}

	// Step 2: 转文字（若 md 已存在则跳过）
	if _, err := os.Stat(mdPath); err != nil {
		utils.Info("🗣️ [后处理#%d] 转文字: %s", workerID, name)
		if err := s.runPython("transcribe.py", mp3Path); err != nil {
			utils.Warn("⚠️ [后处理#%d] 转文字失败: %s (%v)", workerID, name, err)
			return
		}
	}

	// 二次校验 md
	if _, err := os.Stat(mdPath); err != nil {
		utils.Warn("⚠️ [后处理#%d] 转文字后仍找不到 md: %s", workerID, name)
		return
	}

	// Step 3: 清洗（全局互斥，同时只允许一个 claude 进程在跑）
	s.cleanMu.Lock()
	defer s.cleanMu.Unlock()
	utils.Info("🧹 [后处理#%d] 清洗: %s", workerID, name)
	if err := s.runPython("clean.py", mdPath); err != nil {
		utils.Warn("⚠️ [后处理#%d] 清洗失败（保留原逐字稿）: %s (%v)", workerID, name, err)
		return
	}
	utils.Info("✅ [后处理#%d] 完成: %s", workerID, name)
}

// runPython 调用 wx_video-channel/<script> --file <inputFile>
// 环境变量透传百度 Key（如果 config 里有）
func (s *PostProcessService) runPython(script string, inputFile string) error {
	cfg := config.Get()

	pythonExe := "python"
	if cfg != nil && cfg.PythonExe != "" {
		pythonExe = cfg.PythonExe
	}

	scriptPath := filepath.Join(s.toolDir, script)
	if _, err := os.Stat(scriptPath); err != nil {
		return err
	}

	cmd := exec.Command(pythonExe, scriptPath, "--file", inputFile)
	cmd.Dir = s.toolDir

	// 透传百度 Key（config 优先，为空则用 transcribe.py 内置默认值）
	env := os.Environ()
	if cfg != nil {
		if cfg.BaiduASRKey != "" {
			env = append(env, "WX_CHANNEL_BAIDU_ASR_KEY="+cfg.BaiduASRKey)
		}
		if cfg.BaiduASRSecret != "" {
			env = append(env, "WX_CHANNEL_BAIDU_ASR_SECRET="+cfg.BaiduASRSecret)
		}
			if cfg.LLMApiKey != "" {
				env = append(env, "WX_CHANNEL_LLM_API_KEY="+cfg.LLMApiKey)
			}
			if cfg.LLMApiBase != "" {
				env = append(env, "WX_CHANNEL_LLM_API_BASE="+cfg.LLMApiBase)
			}
			if cfg.LLMModel != "" {
				env = append(env, "WX_CHANNEL_LLM_MODEL="+cfg.LLMModel)
			}
	}
	// 强制 Python stdout/stderr 使用 UTF-8，避免中文文件名在 GBK 控制台报错
	env = append(env, "PYTHONIOENCODING=utf-8")
	cmd.Env = env

	out, err := cmd.CombinedOutput()
	if len(out) > 0 {
		// 逐行打印 Python 输出（前面已经加了标签，不再重复加）
		for _, line := range splitLines(string(out)) {
			if line != "" {
				utils.Info("    %s", line)
			}
		}
	}
	return err
}

func replaceExt(path, newExt string) string {
	ext := filepath.Ext(path)
	return strings.TrimSuffix(path, ext) + newExt
}

func splitLines(s string) []string {
	s = strings.ReplaceAll(s, "\r\n", "\n")
	return strings.Split(strings.TrimRight(s, "\n"), "\n")
}
