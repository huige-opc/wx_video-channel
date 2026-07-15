"""
把 wx_video-channel/downloads 里的视频转成 mp3 音频（就地生成，和视频同一目录）
依赖：ffmpeg（已在 tools/video/ffmpeg/ffmpeg.exe）

两种模式：
  1) 无参数：批量扫描 downloads/ 下所有视频（原有行为）
  2) --file <mp4路径>：只处理单个视频，静默、无交互（供 Go 后端调用）
"""
import argparse
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
FFMPEG = _HERE / "bin" / "ffmpeg.exe"
INPUT_DIR = _HERE / "downloads"

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".flv", ".webm"}


def extract_audio(video: Path, out_mp3: Path) -> bool:
    """把视频抽成 64kbps 单声道 mp3"""
    cmd = [
        str(FFMPEG),
        "-y",
        "-i", str(video),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-b:a", "64k",
        str(out_mp3),
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def process_single(video: Path) -> int:
    """处理单个视频文件，返回 exit code。供 Go 后端调用，无交互。"""
    if not FFMPEG.exists():
        print(f"[错误] 找不到 ffmpeg: {FFMPEG}", flush=True)
        return 1
    if not video.exists():
        print(f"[错误] 视频不存在: {video}", flush=True)
        return 1

    out_mp3 = video.with_suffix(".mp3")
    if out_mp3.exists():
        print(f"[跳过] mp3 已存在: {out_mp3.name}", flush=True)
        return 0

    print(f"[抽音频] {video.name}", flush=True)
    if extract_audio(video, out_mp3):
        size_mb = out_mp3.stat().st_size / (1024 * 1024)
        print(f"[抽音频] [OK] ({size_mb:.2f} MB)", flush=True)
        return 0
    else:
        print(f"[抽音频] [FAIL]", flush=True)
        return 2


def process_batch() -> None:
    """批量扫描模式，供用户手动双击运行。"""
    if not FFMPEG.exists():
        print(f"[错误] 找不到 ffmpeg: {FFMPEG}")
        sys.exit(1)
    if not INPUT_DIR.exists():
        print(f"[错误] 找不到输入目录: {INPUT_DIR}")
        sys.exit(1)

    videos = [p for p in INPUT_DIR.rglob("*") if p.is_file() and p.suffix.lower() in VIDEO_EXTS]
    if not videos:
        print(f"[提示] {INPUT_DIR} 下没找到视频文件")
        return

    print(f"找到 {len(videos)} 个视频")
    print("=" * 60)

    ok = 0
    skip = 0
    fail = 0
    for i, video in enumerate(videos, 1):
        # 就地生成同名 mp3
        out_mp3 = video.with_suffix(".mp3")

        print(f"[{i}/{len(videos)}] {video.parent.name}/{video.name}")

        if out_mp3.exists():
            print(f"    已存在，跳过")
            skip += 1
            continue

        if extract_audio(video, out_mp3):
            size_mb = out_mp3.stat().st_size / (1024 * 1024)
            print(f"    [OK] ({size_mb:.2f} MB)", flush=True)
            ok += 1
        else:
            print(f"    [FAIL]")
            fail += 1

    print("=" * 60)
    print(f"完成：{ok} 个成功, {skip} 个跳过, {fail} 个失败")


def main() -> None:
    parser = argparse.ArgumentParser(description="视频转 mp3 音频")
    parser.add_argument("--file", type=str, default=None, help="仅处理单个视频文件（Go 后端调用用，静默无交互）")
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
