# 更新日志

本地二开版本历史。

## v1.2 (2026-07-11) — 全自动流水线

### 🧹 自动洗稿
- Go 后处理自动调用 clean.py，通过 OpenAI 兼容 API（需配置 llm_api_key）清洗逐字稿
- 自动生成 _清洗版.md（结构化排版、修正错字、补标点、分小节）
- 自动删除原始稿，最终只留 mp4 + mp3 + _清洗版.md

### 🔧 全链路修复
- Gopeed 下载路径补 Enqueue 调用，Go 后处理即时触发
- 优雅关闭时停 PostProcessService，避免任务丢失
- Python 脚本 Unicode 兼容，解决 GBK 终端报错
- guard 每 2 分钟自动扫描 + 锁防冲突 + 退出补跑
- VBS 去除 UTF-8 BOM，修复双击报错
- 编译兼容 winlibs GCC，成功编译 exe

---

## v1.1（2026-07-11）— 下载即转录

### 🎙️ 视频下载完成后自动抽 mp3 + 转 md

- **零操作闭环**：下载器内置 `PostProcessService`，每次 mp4 落盘后自动在后台完成"抽 mp3 → 调百度短语音识别 API 生成 md 逐字稿"，不再需要手动跑批处理脚本
- **2 worker 并发**：默认起 2 个后台 worker 依次消化队列，不阻塞下载主流程
- **默认开启可关**：`config.yaml` 新增 `auto_transcribe`（默认 `true`），改成 `false` 就回到旧的手动流程
- **智能跳过**：已存在 `.mp3` / `.md` 的视频自动跳过，重复触发安全
- **Python 脚本双模式**：`extract_audio.py` / `transcribe.py` 新增 `--file <path>` 单文件静默模式（供 Go 后端调用），保留原批量交互模式，双击 `抽取音频.bat` / `转文字.bat` 仍可用

### 🔧 新增配置项

| 字段 | 默认 | 说明 |
|---|---|---|
| `auto_transcribe` | `true` | 是否启用自动后处理 |
| `post_process_worker` | `2` | 后处理 worker 并发数 |
| `baidu_asr_key` | `""` | 百度 API_KEY（空时用内置默认） |
| `baidu_asr_secret` | `""` | 百度 SECRET_KEY |
| `python_exe` | `python` | Python 可执行文件路径 |

### 🖥️ 控制台改进

- 修复 Markdown 渲染器：支持 `#### / ##### / ######` 标题；修复列表贪婪匹配吞并全文的问题；代码块隔离处理
- 帮助文档相对链接改成内部切换，不再新窗口打开 404
- 帮助菜单精简为 6 项（目录 / 项目介绍 / 安装指南 / 配置说明 / 故障排除 / 更新日志）
- 更新所有文档，去除上游仓库 v5.x 时代的过时内容

### 🛡️ 稳定性补丁

- `/api/stats` 增加 nil 守卫，防止统计服务未就绪时接口崩溃
- `internal/database/database.go` 的 `db.Ping()` 增加 5 次退避重试，应对"杀进程后立即重启导致 WAL 句柄未释放"的竞态
- `guard.vbs` 移除 `ProxyEnable=0` 写入，不再影响 Clash / Mihomo 等系统代理

### 📚 文档更新

- 外层 `README.md`、`web/docs/*.md` 全部按当前实际情况重写
- 明确 v1.1 是**基于 nobiyou/wx_channel 上游的本地二开版**，仅用于个人学习与内容备份

---

## v1.0（2026-07-10）— 二开初版

基于 nobiyou/wx_channel（MIT License）二次开发。

### 新增

- 视频抽音频脚本 `extract_audio.py`（ffmpeg）
- 百度短语音识别转录脚本 `transcribe.py`
- AI 逐字稿清洗 Skill（`SKILL.md`）
- 静默启动脚本 `start.vbs`（管理员自动提权、隐藏窗口、自动打开控制台）
- 看门狗脚本 `guard.vbs`（微信完全退出满 5 分钟自动关闭下载器）
- 配套使用手册 `README.md`
- 完整闭环打通：下载 → 音频 → 文字 → 清洗

### 上游合并

- 保留上游 v5.6.9 全部下载/批量/雷达功能
- 保留上游云端管理、Prometheus 指标等能力（默认关闭）
