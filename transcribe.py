"""
把 wx_video-channel/downloads/**/*.mp3 用百度语音识别 API 转成同名 md（就地生成）
免费额度：短语音识别 5万次/日

两种模式：
  1) 无参数：批量扫描 downloads/ 下所有 mp3（原有行为）
  2) --file <mp3路径>：只处理单个音频，静默、无交互（供 Go 后端调用）

Key 可通过环境变量覆盖：
  WX_CHANNEL_BAIDU_ASR_KEY, WX_CHANNEL_BAIDU_ASR_SECRET
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode

# ============ 配置区（可被环境变量覆盖） ============
API_KEY = os.environ.get("WX_CHANNEL_BAIDU_ASR_KEY", "")
SECRET_KEY = os.environ.get("WX_CHANNEL_BAIDU_ASR_SECRET", "")
CHUNK_SECONDS = 55
DEV_PID = 1537  # 普通话（有标点）
# ==================================================

_HERE = Path(__file__).resolve().parent
FFMPEG = _HERE / "bin" / "ffmpeg.exe"
FFPROBE = _HERE / "bin" / "ffprobe.exe"
INPUT_DIR = _HERE / "downloads"

ASR_URL = "https://vop.baidu.com/server_api"
TOKEN_URL = "https://aip.baidubce.com/oauth/2.0/token"

SAMPLE_RATE = 16000
BYTES_PER_SAMPLE = 2


def get_access_token() -> str:
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY,
    }
    url = f"{TOKEN_URL}?{urlencode(params)}"
    with urlopen(url, timeout=15) as r:
        data = json.loads(r.read().decode("utf-8"))
    if "access_token" not in data:
        raise RuntimeError(f"取 access_token 失败: {data}")
    return data["access_token"]


def get_duration(audio: Path) -> float:
    cmd = [
        str(FFPROBE),
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio),
    ]
    out = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(out.stdout.strip())


def slice_audio(audio: Path, tmp_dir: Path, chunk_seconds: int) -> list:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    full_pcm = tmp_dir / "full.pcm"
    cmd = [
        str(FFMPEG),
        "-y",
        "-i", str(audio),
        "-vn",
        "-ac", "1",
        "-ar", str(SAMPLE_RATE),
        "-f", "s16le",
        "-acodec", "pcm_s16le",
        str(full_pcm),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    chunk_bytes = chunk_seconds * SAMPLE_RATE * BYTES_PER_SAMPLE
    chunks = []
    with full_pcm.open("rb") as f:
        idx = 0
        while True:
            data = f.read(chunk_bytes)
            if not data:
                break
            if len(data) < SAMPLE_RATE * BYTES_PER_SAMPLE // 2:
                break
            out = tmp_dir / f"chunk_{idx:04d}.pcm"
            out.write_bytes(data)
            chunks.append(out)
            idx += 1
    return chunks


def recognize_chunk(pcm: Path, token: str):
    audio_bytes = pcm.read_bytes()
    headers = {"Content-Type": "audio/pcm;rate=16000"}
    url = f"{ASR_URL}?dev_pid={DEV_PID}&cuid=wx_channel_local&token={token}"
    req = Request(url, data=audio_bytes, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return "", f"HTTP错误:{e}"
    if data.get("err_no") != 0:
        return "", f"err_no={data.get('err_no')} err_msg={data.get('err_msg')}"
    result = data.get("result") or []
    return (result[0] if result else ""), ""


def transcribe(audio: Path, token: str, quiet: bool = False) -> str:
    duration = get_duration(audio)
    n_chunks = int(duration // CHUNK_SECONDS) + 1
    if not quiet:
        print(f"    音频时长 {duration:.1f}s，切成 {n_chunks} 段")

    texts = []
    with tempfile.TemporaryDirectory(prefix="asr_", dir=str(_HERE)) as tmp:
        tmp_dir = Path(tmp)
        chunks = slice_audio(audio, tmp_dir, CHUNK_SECONDS)
        for i, chunk in enumerate(chunks, 1):
            try:
                text, err = recognize_chunk(chunk, token)
            except Exception as e:
                text, err = "", str(e)
            if text:
                texts.append(text)
                if not quiet:
                    print(f"    [段 {i}/{len(chunks)}] {text[:40]}{'...' if len(text) > 40 else ''}")
            else:
                if not quiet:
                    print(f"    [段 {i}/{len(chunks)}] (空) {err}")
            time.sleep(0.3)
    return "\n".join(texts)


def write_md(audio: Path, text: str) -> None:
    title = audio.stem
    author = audio.parent.name
    content = (
        f"# {title}\n\n"
        f"- **作者**：{author}\n"
        f"- **来源**：蝴蝶号\n"
        f"- **视频文件**：`{audio.with_suffix('.mp4').name}`\n\n"
        f"---\n\n"
        f"## 逐字稿\n\n"
        f"{text}\n"
    )
    audio.with_suffix(".md").write_text(content, encoding="utf-8")


def process_single(audio: Path) -> int:
    """处理单个 mp3，返回 exit code。供 Go 后端调用，静默。"""
    if not FFMPEG.exists() or not FFPROBE.exists():
        print(f"[错误] 找不到 ffmpeg/ffprobe: {FFMPEG.parent}", flush=True)
        return 1
    if not audio.exists():
        print(f"[错误] 音频不存在: {audio}", flush=True)
        return 1

    out_md = audio.with_suffix(".md")
    if out_md.exists():
        print(f"[跳过] md 已存在: {out_md.name}", flush=True)
        return 0

    print(f"[转文字] {audio.name}", flush=True)
    try:
        token = get_access_token()
    except Exception as e:
        print(f"[转文字] [FAIL] 取 token 失败：{e}", flush=True)
        return 1

    try:
        text = transcribe(audio, token, quiet=True)
    except Exception as e:
        print(f"[转文字] [FAIL] 识别失败：{e}", flush=True)
        return 2

    if not text.strip():
        print(f"[转文字] [FAIL] 识别结果为空", flush=True)
        return 3

    write_md(audio, text)
    print(f"[转文字] [OK] 完成 ({len(text)} 字)", flush=True)
    return 0


def process_batch() -> None:
    """批量扫描模式，供用户手动双击运行。"""
    if not FFMPEG.exists() or not FFPROBE.exists():
        print(f"[错误] 找不到 ffmpeg/ffprobe: {FFMPEG.parent}")
        sys.exit(1)
    if not INPUT_DIR.exists():
        print(f"[错误] 找不到输入目录: {INPUT_DIR}")
        sys.exit(1)

    mp3s = sorted(INPUT_DIR.rglob("*.mp3"))
    if not mp3s:
        print(f"[提示] {INPUT_DIR} 下没有 mp3")
        return

    print(f"找到 {len(mp3s)} 个音频")
    print("=" * 60)

    print("正在获取百度 access_token …")
    try:
        token = get_access_token()
    except Exception as e:
        print(f"[错误] {e}")
        sys.exit(1)
    print("[OK] Token 获取成功\n")

    ok = 0
    skip = 0
    fail = 0
    for i, audio in enumerate(mp3s, 1):
        out_md = audio.with_suffix(".md")
        print(f"[{i}/{len(mp3s)}] {audio.parent.name}/{audio.name}")
        if out_md.exists():
            print(f"    已存在，跳过")
            skip += 1
            continue
        try:
            text = transcribe(audio, token, quiet=False)
        except Exception as e:
            print(f"    [FAIL] 失败：{e}")
            fail += 1
            continue
        if text.strip():
            write_md(audio, text)
            print(f"    [OK] 完成（{len(text)} 字）\n")
            ok += 1
        else:
            print(f"    [FAIL] 识别结果为空\n")
            fail += 1

    print("=" * 60)
    print(f"完成：{ok} 个成功, {skip} 个跳过, {fail} 个失败")


def main() -> None:
    parser = argparse.ArgumentParser(description="mp3 音频转 md 逐字稿")
    parser.add_argument("--file", type=str, default=None, help="仅处理单个 mp3 文件（Go 后端调用用，静默无交互）")
    args = parser.parse_args()

    if args.file:
        sys.exit(process_single(Path(args.file)))
    else:
        try:
            process_batch()
        finally:
            input("\n按回车键关闭...")


if __name__ == "__main__":
    main()
