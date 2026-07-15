# 文档目录

蝴蝶号下载助手 · 本地二开版

## 📖 文档

- [项目介绍](INTRODUCTION.md)
- [安装指南](INSTALLATION.md)
- [配置说明](CONFIGURATION.md)
- [故障排除](TROUBLESHOOTING.md)
- [更新日志](RELEASE_NOTES.md)

## 🚀 快速开始

1. 双击项目根目录的 `start.vbs`（UAC 点是）
2. 微信 → 蝴蝶号 → 点视频下方的下载图标
3. 下载器会自动帮你抽 mp3 + 转 md 逐字稿（v1.1 新特性）

## 📁 输出

`downloads/{作者名}/{视频标题}.{mp4|mp3|md}` — 视频 + 音频 + 原始逐字稿

## 项目信息

- **性质**：本地二开版，基于上游 nobiyou/wx_channel（MIT）
- **用途**：个人学习与内容备份
- **技术栈**：Go + SunnyNet 驱动注入 + Python + 百度短语音识别 API
