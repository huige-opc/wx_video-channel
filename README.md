# wx_video-channel · 蝴蝶号下载与转录工具

在微信**蝴蝶号**里点一下下载，自动得到 视频 + 音频 + AI 清洗后的逐字稿。

---

> **适用范围**
>
> | 场景 | 支持吗？ |
> |---|---|
> | **蝴蝶号**（侧边栏"蝴蝶号"入口的视频）| ✅ 本工具 |
> | 公众号文章里嵌的视频 | ❌ 使用 butterfly-article-dl |
> | 朋友圈视频 | ❌ |
> | 小程序视频 | ❌ |

---

## 快速上手（3 分钟）

```
蝴蝶号看到好视频
   ↓ ① 双击 start.vbs 启动下载器（UAC 点"是"）
   ↓ ② 在蝴蝶号播放页点"下载"按钮
   ↓ ③ 全自动：抽音频 → 转文字 → AI 洗稿
   ↓ ④ 每个视频目录最终留 3 个文件：mp4 + mp3 + _清洗版.md
```

全程无需手动操作。下载后后台自动完成抽音频、转文字、AI 清洗三步。

---

## 首次配置（只做一次）

### 环境要求

| 组件 | 要求 |
|---|---|
| Windows | Win10/11 x64 |
| Python | 3.9+ |
| 微信 PC 版 | 3.9+ |
| ffmpeg | 需自行下载放入 `bin/` 目录（[下载地址](https://ffmpeg.org/download.html)） |

### 启动下载器

1. 双击 `start.vbs`（UAC 弹窗点"是"——必须管理员启动）
2. 首次会弹出证书安装提示，全部选**是**
3. 3-5 秒后浏览器自动打开 `http://127.0.0.1:2025/console`

### 让微信生效

1. **完全退出微信**（右下角托盘 → 右键 → 退出，不是关闭窗口）
2. 重新打开微信并登录
3. 侧边栏点"**蝴蝶号**"
4. 播放任意视频 → 下方按钮栏应出现**下载**图标

### 百度语音识别（转文字必须）

在 `transcribe.py` 头部配置百度语音识别 API：

```bash
set WX_CHANNEL_BAIDU_ASR_KEY=你的Key
set WX_CHANNEL_BAIDU_ASR_SECRET=你的Secret
```

- 使用短语音识别 API（免费额度 5 万次/日）
- 长音频自动切成 55 秒一段循环调用

### AI 清洗（可选但推荐）

在 `config.yaml` 中配置 LLM API：

```yaml
llm_api_key: "sk-你的API密钥（支持DeepSeek/硅基流动等OpenAI兼容接口）"
llm_api_base: "https://api.deepseek.com/v1"
llm_model: "deepseek-chat"
```

---

## 日常使用

**Step 1：** 双击 `start.vbs` 启动下载器（已在运行则跳过）

**Step 2：** 微信蝴蝶号 → 打开视频 → 点**下载**按钮

**Step 3（自动）：** 文件保存到 `downloads/` → 自动抽 mp3 → 调百度 API 转文字

**Step 4（自动）：** AI 自动清洗逐字稿 → 生成 `xxx_清洗版.md`

最终每个视频目录：

```
downloads/{作者名}/
├── xxx.mp4          视频
├── xxx.mp3          音频
└── xxx_清洗版.md    AI 清洗后的可读文稿
```

### 手动停止

- 任务管理器结束 `蝴蝶号下载助手.exe`
- 或双击 `butterfly-stop.lnk`
- 直接关机也不会留下任何残留

---

## 目录结构

```
wx_video-channel/
├── cmd/                 # 命令行入口
├── internal/            # 核心逻辑
│   ├── api/             #   API 路由
│   ├── app/             #   应用主逻辑
│   ├── assets/          #   静态资源
│   ├── cloud/           #   云端管理
│   └── config/          #   配置读取
├── pkg/                 # Go 工具包
├── web/                 # Web 管理界面
├── scripts/             # 构建脚本
├── bin/                 # ffmpeg（需自行下载）
├── downloads/           # 下载文件输出目录
│
├── start.vbs            # 启动（管理员权限 + 打开控制台）
├── stop.vbs             # 停止
├── guard.vbs            # 后台看门狗
├── butterfly-start.lnk  # 桌面快捷方式（启动）
├── butterfly-stop.lnk   # 桌面快捷方式（停止）
│
├── config.yaml          # 配置文件
├── config.yaml.example  # 配置示例
│
├── transcribe.py        # 百度语音转文字
├── extract_audio.py     # 视频抽音频
├── clean.py             # AI 清洗逐字稿
├── 抽取音频.bat          # 批量抽音频
├── 转文字.bat            # 批量转文字
│
├── SKILL.md             # AI 清洗规则
├── go.mod / go.sum      # Go 依赖
└── main.go              # 入口
```

---

## 常见问题

### start.vbs 双击没反应？
1. UAC 弹窗要点"是"
2. 可能已经跑着，浏览器打开 `http://127.0.0.1:2025/console` 看看
3. `蝴蝶号下载助手.exe` 可能被杀毒软件删了，加白名单

### 蝴蝶号没有"下载"按钮？
1. `start.vbs` 是否以管理员启动？
2. 微信是否在下载器**之后**打开的？如果是，退出微信重开
3. 微信版本 3.9+？
4. 证书是否装成功？手动安装 `internal/assets/certs/SunnyRoot.cer` 到"受信任的根证书颁发机构"

### 如何手动跑后处理？
- 双击 `抽取音频.bat` 批量补 mp3
- 双击 `转文字.bat` 批量补 md
- `python clean.py` 手动批量清洗

---

## 开发者指引

### 技术栈

| 层级 | 技术 |
|---|---|
| 语言 | Go 1.23+ |
| 网络驱动 | SunnyNet（内核级流量拦截） |
| 前端 | 原生 HTML + JS（Web 控制台） |
| 语音转文字 | 百度语音识别 API |
| AI 清洗 | OpenAI 兼容接口（DeepSeek / 硅基流动等） |

### 核心架构

```
CLI 入口 (cmd/root.go)
    ↓
App 编排器 (internal/app/App)
    ↓
HTTP 代理 (SunnyNet 库)
    ↓
请求拦截链 → 解析蝴蝶号协议 → 解密 → 下载
    ↓
后处理流水线 → 抽音频 → 转文字 → AI 清洗
```

- 只注入 `WeChatAppEx.exe` 进程，不修改系统全局代理
- 后处理队列 2 并发，依次执行

### 目录结构详解

| 目录 | 说明 |
|------|------|
| `cmd/` | CLI 命令入口（root/proxy/web/uninstall/update/version） |
| `internal/app/` | 应用核心编排 |
| `internal/api/` | HTTP API 路由 |
| `internal/config/` | 配置读写（viper） |
| `internal/cloud/` | 云端管理（Hub WebSocket） |
| `internal/services/` | 后处理服务（post_process_service.go） |
| `internal/assets/` | 嵌入资源（证书、注入 JS） |
| `pkg/` | 工具包（下载引擎、解密、代理等） |
| `web/` | Web 控制台前端 |
| `scripts/` | 构建脚本 |

### 编译

```bash
# 安装 Go 1.23+（https://go.dev/dl/）
go build -o 蝴蝶号下载助手.exe .

# 编译（带版本信息，减小体积）
go build -ldflags="-s -w" -o 蝴蝶号下载助手.exe .
```

### 开发调试

```powershell
# 启动代理服务（需要管理员权限）
go run . proxy

# 启动 Web 控制台（默认端口 15800）
go run . web
```

### 二次开发

1. 修改代理拦截逻辑 → `internal/api/` 下的路由处理
2. 修改后处理流水线 → `internal/services/post_process_service.go`
3. 修改前端界面 → `web/` 下的 HTML/JS/CSS
4. 修改下载逻辑 → `internal/services/` 和 `pkg/` 下的下载引擎
5. 添加新功能 → 在 `cmd/` 下新增子命令

### 注意事项

- 需要 Windows 系统（依赖 Windows 网络驱动）
- 需要管理员权限运行
- 只注入蝴蝶号进程 `WeChatAppEx.exe`，不影响其他网络流量
- 编译前确保已安装 Go 1.23+ 和 gcc（用于网络驱动编译）
- 调试时可用 `go run . proxy --debug` 查看详细日志

---

## 开源协议

本项目基于 MIT 协议开源 - 详见 [LICENSE](LICENSE) 文件。

---

## 联系

有问题或建议欢迎联系：
- 微信：HgAiAgent（扫码添加，拉你进交流群）
- 邮箱：[szlihui801@gmail.com](mailto:szlihui801@gmail.com)<｜end▁of▁thinking｜>

把本工具文件夹拖到 AI 助手（Claude、ChatGPT 等），告诉它"帮我看下这个工具怎么用"，AI 会帮你搞定。
