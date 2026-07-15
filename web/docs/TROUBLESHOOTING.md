# 故障排除

按遇到问题的场景排查。

---

## 1️⃣ 蝴蝶号里没有下载按钮

这是最常见的问题，原因几乎都是**驱动注入没成功**。

### 排查步骤

1. **`start.vbs` 是不是以管理员启动的？**
   - UAC 弹窗必须点"是"
   - 直接双击 `蝴蝶号下载助手.exe`（不走 vbs）**没有提权**，肯定不行
2. **微信是不是在下载器之后打开的？**
   - 驱动只能拦截"注入完成之后启动的 WeChatAppEx.exe"
   - 如果微信是先开的，需要**完全退出微信**（右下角托盘 → 右键 → 退出）再重开
3. **微信版本够不够新？**
   - 需要 3.9+
4. **证书装了吗？**
   - 打开 `downloads\SunnyRoot.cer`，双击 → 安装到"受信任的根证书颁发机构"
5. **下载器控制台日志里有没有 `✓ 蝴蝶号注入引擎已就绪 (WeChatAppEx.exe)`？**
   - 浏览器打开 `http://127.0.0.1:2025/console` 看
   - 如果显示 `⚠️ 注入引擎启动失败：可能需要 [管理员权限]`，就是提权问题

---

## 2️⃣ 下载完成后没有 mp3 / md 自动生成

### 快速定位

1. 看控制台日志（`logs/wx_channel.log`）里有没有 `[后处理]` 相关行：
   - 有 `🎙️ [后处理] 已入队` → 队列在工作，看后续
   - 完全没有 → `auto_transcribe` 被关了或服务没启动
2. 看有没有 `✓ 自动后处理已启用 (workers=2, ...)` 日志（启动时打的）
3. 有 `⚠️ [后处理] 抽音频失败` → Python / ffmpeg 找不到，看下面

### 常见原因

**Python 找不到**
```
[后处理] 抽音频失败: exec: "python": executable file not found in %PATH%
```
→ 在 `config.yaml` 里配上绝对路径：
```yaml
python_exe: "C:\\Python312\\python.exe"
```

**ffmpeg 找不到**
```
[错误] 找不到 ffmpeg: D:\AI_bian_cheng\trae\tools\video\ffmpeg\ffmpeg.exe
```
→ 检查项目里的 ffmpeg 是否被杀软删掉，需要恢复到 `tools/video/ffmpeg/ffmpeg.exe`

**百度 API 报错 `err_no=3302 No permission to access data`**
→ 百度应用没开通"短语音识别"接口
→ 打开 <https://console.bce.baidu.com/ai/#/ai/speech/app/list> → 找应用 → 修改 → 勾选"短语音识别 - 中文普通话" → 保存

**百度 API 报错 `Open api daily request limit reached`**
→ 免费额度 5 万次/日用完了，等次日或换 Key

---

## 3️⃣ 端口 2025 被占用 / 代理无法启动

```powershell
# 看看谁占了 2025 端口
netstat -ano | findstr :2025
```

- 找到 PID，任务管理器里对应进程结束掉
- 或者改端口：`config.yaml` 里 `port: 8080`，重启后浏览器用 `http://127.0.0.1:8080/console`

---

## 4️⃣ 关机后其他软件上不了网 / Clash 突然失效

**本工具不会导致这个问题。** 它通过驱动只注入 `WeChatAppEx.exe`，从不修改系统全局代理。

如果确实出现，检查：
- 是不是 Clash 的系统代理模式被别的软件关了（去检查 `HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ProxyEnable`）
- 早期版本的 `guard.vbs` 会在退出时误写 `ProxyEnable=0`，v1.1 已经修复。如果你还在用旧版 guard.vbs，替换成项目里的最新版

---

## 5️⃣ 控制台文档打开是空的 / 404

前端的 Markdown 渲染器在 v1.1 已修好，如果还遇到：
- 浏览器按 **Ctrl+F5** 强制刷新（清缓存）
- F12 打开 Console 看有没有报错

---

## 6️⃣ 手误运行了好几次 start.vbs 会不会崩溃

**不会。** `start.vbs` 每次启动前会先杀掉已有的 `蝴蝶号下载助手.exe`（用 WMI `Terminate()`）再起新的，天然防双开。

副作用：
- 每次都会拉起一个新的 `guard.vbs` 看门狗（会累积但无害，微信关了 5 分钟会自动退出）
- 每次都要点一次 UAC

---

## 7️⃣ 视频下下来但没有声音 / 文件损坏

- 重新下载一次（多数是网络波动）
- 检查 `downloads/.uploads/` 有没有残留的分片临时目录
- 看日志里有没有 `解密失败` 相关错误

---

## 8️⃣ 转录结果错字很多 / 不通顺

**这是免费短语音识别的正常水平。** 免费模型对英文缩写、专有名词、语气词识别有硬伤。

**解决**：在你当前用的 AI 助手对话里发"清洗"（会触发项目里的 `SKILL.md`），AI 会做上下文修正、补标点、结构化排版。效果会大幅改善。

---

## 获取日志

看 `logs/wx_channel.log`，或在控制台首页看到实时日志。

- 启动日志：定位注入是否成功
- API 请求日志：定位下载失败点
- `[后处理]` 相关：定位自动转录失败原因

---

## 下一步

- 项目介绍 → [项目介绍](INTRODUCTION.md)
- 配置说明 → [配置说明](CONFIGURATION.md)
