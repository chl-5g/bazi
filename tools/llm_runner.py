"""
LLM Runner - 调用 Anthropic API 执行单步推理。
从 .env 读取 API 配置。

用法：
    python llm_runner.py "system prompt text" "user prompt text"
    python llm_runner.py --file skills/s01_chart.md --context '{"chart_data": "..."}'
"""

import os, sys, json
from pathlib import Path

# 加载 .env
def _load_dotenv():
    env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key, val = key.strip(), val.strip()
            if key not in os.environ:
                os.environ[key] = val

_load_dotenv()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
_BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1")
# 确保 URL 以 /messages 结尾
ANTHROPIC_BASE_URL = _BASE_URL if _BASE_URL.endswith("/messages") else _BASE_URL.rstrip("/") + "/messages"


def call(system_prompt: str, user_prompt: str, model: str = None) -> str:
    """调用 Anthropic API，返回模型输出文本。"""
    import urllib.request, urllib.error

    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your-api-key-here":
        return "ERROR: ANTHROPIC_API_KEY 未配置，请在 ~/bazi/.env 中设置"

    body = json.dumps({
        "model": model or ANTHROPIC_MODEL,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
        "thinking": {"type": "disabled"},
    }).encode("utf-8")

    req = urllib.request.Request(
        ANTHROPIC_BASE_URL,
        data=body,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
    )

    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read().decode("utf-8"))
        # 从 content 数组中提取 text 类型的内容（跳过 thinking 等）
        for block in data.get("content", []):
            if block.get("type") == "text":
                return block["text"]
        # fallback: 返回第一个 content 的 text 字段
        return data["content"][0].get("text", data["content"][0].get("thinking", str(data["content"])))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        return f"ERROR: HTTP {e.code} - {err_body[:500]}"
    except Exception as e:
        return f"ERROR: {e}"


def call_with_skill(skill_file: str, context: dict, model: str = None) -> str:
    """加载 skill 文件，填充模板，调用 API。"""
    from bazi_workflow import parse_skill

    skill = parse_skill(Path(skill_file))
    if not skill:
        return f"ERROR: 无法加载 {skill_file}"

    # 填充上下文模板
    user_prompt = skill.content
    for key, val in context.items():
        user_prompt = user_prompt.replace("{{" + key + "}}", str(val))
    user_prompt = user_prompt.replace("{{chart_data}}", str(context.get("chart_data", "")))

    return call(skill.content.split("\n")[0].replace("# ", "") + " 请按输出格式输出。",
                user_prompt, model)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python llm_runner.py 'system' 'user_prompt'")
        print("      python llm_runner.py --skill skills/s17_career.md '{\"chart_data\":\"...\"}'")
        sys.exit(1)

    if sys.argv[1] == "--skill":
        ctx = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        print(call_with_skill(sys.argv[2], ctx))
    else:
        print(call(sys.argv[1], sys.argv[2]))
