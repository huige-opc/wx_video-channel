# 配置说明

配置文件：`d:\AI_bian_cheng\trae\tools\wx_video-channel\config.yaml`

修改后**重启下载器**（任务管理器结束 `蝴蝶号下载助手.exe` → 双击 `start.vbs`）才生效。

---

## 常用配置

### 基础

```yaml
# 代理端口（默认 2025，被占用可改）
port: 2025

# 下载目录（默认 downloads，可改绝对路径）
download_dir: downloads

# 日志文件（默认 logs/wx_channel.log，5MB 自动滚动）
log_file: logs/wx_channel.log
max_log_size_mb: 5
```

### 自动转录（v1.1 二开新增，重点）

```yaml
# 是否启用自动后处理（默认 true）
# false 时退回旧的手动流程：需要自己双击 抽取音频.bat / 转文字.bat
auto_transcribe: true

# 后处理并发 worker 数（默认 2，百度免费 API 有 QPS 限制，建议 1~3）
post_process_worker: 2

# 百度短语音识别 Key（可选）
# 留空时使用 transcribe.py 内置的默认 Key（有免费额度 5 万次/日）
# 想用自己的 Key 请去 https://console.bce.baidu.com/ai/#/ai/speech/app/list 申请
baidu_asr_key: ""
baidu_asr_secret: ""

# Python 可执行文件路径（默认 python）
# 如果系统 PATH 里没有 python，请填绝对路径，如 "C:\\Python312\\python.exe"
python_exe: "python"
```

### 并发与限流

```yaml
# 批量下载：同时下载几个文件（默认 5）
download_concurrency: 5

# 单文件多线程连接数（默认 8）
download_connections: 8

# 单文件下载超时（默认 30 分钟）
download_timeout: 30m
```

### 文件名模板（可选）

```yaml
# 支持变量：{date} {datetime} {author} {title} {duration} {video_id} {size}
# 留空使用默认（作者名/标题.mp4）
download_filename_template: ""
```

---

## 自动转录工作机制

1. 每次视频 mp4 落盘（含单文件下载、分片合并、批量下载 3 种入口）都会往队列丢一条任务
2. worker 依次调用：
   - `extract_audio.py --file <mp4路径>` → 生成同名 mp3
   - `transcribe.py --file <mp3路径>` → 生成同名 md 逐字稿
3. 遇到已存在的 mp3 / md 自动跳过，重复触发安全
4. 控制台日志会打 `[后处理#1] 抽音频 / 转文字 / 完成` 便于追踪
5. **不阻塞下载主流程**，队列积压时会依次消化

---

## 关闭自动转录

在 `config.yaml` 加一行：

```yaml
auto_transcribe: false
```

保存后重启下载器。此后下载只出 mp4，需要手动双击 `抽取音频.bat` 和 `转文字.bat` 批处理补齐。

---

## 端口冲突处理

如果 2025 端口被占用（比如另一个开发服务器）：

```yaml
port: 8080
```

改完重启，浏览器改用 `http://127.0.0.1:8080/console`。

---

## 完整字段索引

所有可用字段在 `config.yaml.example` 里有完整注释。程序启动时会自动读取该文件的默认值，你只需要覆盖想改的字段即可。

---

## 下一步

- 遇到问题 → [故障排除](TROUBLESHOOTING.md)
- 项目介绍 → [项目介绍](INTRODUCTION.md)
