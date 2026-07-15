# 蝴蝶号下载助手 目录结构

```
wx_video-channel/
│
├── bin/                       # ffmpeg 工具
├── cmd/                       # CLI 入口
│   ├── root.go
│   ├── sph.go
│   └── ...
│
├── docs/                      # 使用文档
│
├── internal/                  # 核心代码
│   ├── app/app.go             # 主应用入口
│   ├── config/config.go       # 配置管理
│   ├── services/
│   │   └── post_process_service.go  # 下载后自动处理流水线
│   ├── handlers/              # HTTP 处理器
│   ├── api/                   # API 接口
│   ├── cloud/                 # 云端管理
│   ├── database/              # SQLite 数据库
│   ├── router/                # 路由
│   ├── storage/               # 文件存储
│   ├── utils/                 # 工具函数
│   ├── websocket/             # WebSocket
│   └── ...
│
├── pkg/sunnynet/              # SunnyNet 内核驱动（CGo）
│
├── scripts/                   # 构建脚本
│
├── web/                       # Web 控制台
│   ├── console.html
│   ├── index.html
│   ├── about.html
│   ├── css/
│   ├── js/
│   └── docs/
│
├── winres/                    # 图标 & Windows 资源
│   ├── winres.json
│   └── icon.png
│
├── main.go                    # Go 入口
├── go.mod / go.sum
│
├── clean.py                   # AI 清洗（OpenAI 兼容 API）
├── transcribe.py              # 百度语音转文字
├── extract_audio.py           # 视频抽音频
│
├── start.vbs                  # 启动（提权）
├── stop.vbs                   # 停止
├── guard.vbs                  # 看门狗守护
├── auto_start.vbs             # 开机自启
│
├── config.yaml                # 配置文件
├── README.md
├── FILE_TREE.md               # 本文件
└── SKILL.md
```
