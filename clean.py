"""
自动清洗逐字稿 — 调用 OpenAI 兼容 API（不再依赖 claude CLI）

通过环境变量配置（由 Go 后端传递）：
  WX_CHANNEL_LLM_API_KEY    — API Key（必填才清洗）
  WX_CHANNEL_LLM_API_BASE   — API 地址（默认 https://api.openai.com/v1）
  WX_CHANNEL_LLM_MODEL      — 模型名（默认 gpt-4o-mini）

两种模式：
  1) 无参数：批量扫描 downloads/ 下所有原始 md（跳过已清洗的）
  2) --file <md路径>：只处理单个文件（供 Go 后端调用）
"""
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

_HERE = Path(__file__).resolve().parent
INPUT_DIR = _HERE / "downloads"

# ============ LLM 配置（从环境变量读取） ============
LLM_API_KEY = os.environ.get("WX_CHANNEL_LLM_API_KEY", "")
LLM_API_BASE = os.environ.get("WX_CHANNEL_LLM_API_BASE", "https://api.openai.com/v1")
LLM_MODEL = os.environ.get("WX_CHANNEL_LLM_MODEL", "gpt-4o-mini")
# ==================================================

CLEAN_PROMPT = """你是一个专业的语音识别逐字稿清洗助手。请直接输出清洗结果，不要加额外说明。

清洗规则：

一、必须做的修正
1. 错字修正（基于上下文推断）
   - 「哎呀」「ar」「ai」「Ai」→「AI」（几乎肯定是 AI）
   - 拟声重复（「扣扣扣扣」等）→ 保留一次或删除
   - 字母缩写乱码 → 结合上下文推断，不确定则保留原文加脚注「[原音频含糊]」
   - 数字误识（「9」→「就」、「900」→「就有多」等）

2. 补标点
   - 长句子拆成短句
   - 排比结构用列表
   - 反问句加问号

3. 段落结构化
   - 有编号或「第一/第二/第三」的地方，用「### 一、」「### 二、」
   - 列举内容用有序列表或无序列表
   - 核心观点用 **加粗**
   - 金句放 > 引用块

二、必须保留
- 所有事实内容（观点、案例、数据）
- 说话人的原意（口语可以调整为半书面，但核心表达要在）
- 不确定的专有名词（保留原文加脚注，不瞎猜）

三、严禁
- ❌ 添加原文没有的内容
- ❌ 删除原文的观点/事实
- ❌ 用自己的话完全改写
- ❌ 添加评论或点评"""


def split_header(text: str):
    """把 md 切成 (头部, 正文)。
    头部 = 从开头到 '## 逐字稿' 标题（不含）之前的所有内容。
    正文 = '## 逐字稿' 标题之后的所有内容。
    """
    m = re.search(r"^##\s*逐字稿.*$", text, re.MULTILINE)
    if not m:
        return "", text
    header = text[: m.start()].rstrip() + "\n"
    body = text[m.end():].lstrip("\n")
    return header, body


def cleaned_path(md_path: Path) -> Path:
    return md_path.with_name(md_path.stem + "_清洗版.md")


def call_llm(text: str) -> str:
    """调用 OpenAI 兼容 API 清洗文本，返回清洗结果。失败返回空字符串。"""
    if not LLM_API_KEY:
        return ""

    api_base = LLM_API_BASE.rstrip("/")
    url = f"{api_base}/chat/completions"

    payload = json.dumps({
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": CLEAN_PROMPT},
            {"role": "user", "content": text},
        ],
        "temperature": 0.3,
        "max_tokens": 8192,
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}",
    }

    req = Request(url, data=payload, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode("utf-8"))
    except HTTPError as e:
        status = e.code
        body = e.read().decode("utf-8", errors="replace")[:300]
        if status in (401, 403):
            print(f"[清洗] API Key 认证失败 ({status})，检查 llm_api_key 配置", flush=True)
        elif status in (402, 429) or "insufficient" in body.lower() or "quota" in body.lower() or "balance" in body.lower():
            print(f"[清洗] API 余额不足/欠费，保留原始逐字稿 ({status}: {body})", flush=True)
        else:
            print(f"[清洗] API 错误 ({status}): {body}", flush=True)
        return ""
    except URLError as e:
        print(f"[清洗] 网络错误 (请检查 llm_api_base 地址): {e.reason}", flush=True)
        return ""
    except json.JSONDecodeError:
        print(f"[清洗] API 返回格式错误，非 JSON", flush=True)
        return ""
    except Exception as e:
        print(f"[清洗] 未知错误: {e}", flush=True)
        return ""

    # 解析返回
    choices = data.get("choices", [])
    if not choices:
        err_info = data.get("error", {}).get("message", "无 choices")
        print(f"[清洗] API 返回异常: {err_info}", flush=True)
        return ""

    content = choices[0].get("message", {}).get("content", "")
    content = content.strip().strip("```").strip()
    # 去掉可能的 markdown 代码块包裹
    if content.startswith("markdown"):
        content = content[8:].strip()
    if content.startswith("json"):
        content = content[4:].strip()
    return content


def clean_single(md_path: Path) -> int:
    if not md_path.exists():
        print(f"[错误] 文件不存在: {md_path}", flush=True)
        return 1
    if "_清洗版" in md_path.stem:
        return 0

    out_path = cleaned_path(md_path)
    if out_path.exists():
        print(f"[跳过] 清洗版已存在: {out_path.name}", flush=True)
        return 0

    text = md_path.read_text("utf-8")
    if len(text.strip()) < 10:
        print(f"[跳过] 内容太少: {md_path.name}", flush=True)
        return 0

    header, body = split_header(text)
    if len(body.strip()) < 10:
        print(f"[跳过] 正文太少: {md_path.name}", flush=True)
        return 0

    print(f"[清洗] {md_path.parent.name}/{md_path.name} (正文 {len(body)} 字)", flush=True)

    # 检查是否配置了 API Key
    if not LLM_API_KEY:
        print(f"[清洗] 未配置 llm_api_key，跳过清洗（仅保留原始逐字稿）", flush=True)
        return 0

    cleaned_body = call_llm(body)
    if not cleaned_body:
        print(f"[清洗] 失败，保留原稿", flush=True)
        return 2

    # 强制拼回头 + 分隔线 + 清洗后正文（元信息永远保留）
    if header.strip():
        final = header.rstrip() + "\n\n---\n\n## 逐字稿（AI 清洗版）\n\n" + cleaned_body.strip() + "\n"
    else:
        final = cleaned_body.strip() + "\n"

    out_path.write_text(final, encoding="utf-8")
    print(f"[清洗] [OK] -> {out_path.name}", flush=True)
    md_path.unlink()
    return 0


def clean_batch():
    if not INPUT_DIR.exists():
        return
    raw = sorted(INPUT_DIR.rglob("*.md"))
    raw = [m for m in raw if "_清洗版" not in m.stem and not cleaned_path(m).exists()]
    if not raw:
        print(f"[提示] 没有需要清洗的原始稿")
        return
    for md in raw:
        clean_single(md)
        time.sleep(2)


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--file":
        sys.exit(clean_single(Path(sys.argv[2])))
    else:
        clean_batch()


if __name__ == "__main__":
    main()
