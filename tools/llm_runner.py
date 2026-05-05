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
    """调用 Anthropic API，返回模型输出文本。兼容旧接口。"""
    result = call_full(system_prompt, user_prompt, model)
    return result["text"]


def call_full(system_prompt: str, user_prompt: str, model: str = None) -> dict:
    """调用 Anthropic API，返回完整结果字典。

    返回: {
        "text": str,         # 模型输出文本
        "input_tokens": int,  # 输入 token 数
        "output_tokens": int, # 输出 token 数
        "model": str,         # 实际使用的模型
        "stop_reason": str,   # 停止原因
    }
    出错时返回: {"text": "ERROR: ...", "error": True}
    """
    import urllib.request, urllib.error

    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "your-api-key-here":
        return {"text": "ERROR: ANTHROPIC_API_KEY 未配置，请在 ~/bazi/.env 中设置", "error": True}

    actual_model = model or ANTHROPIC_MODEL
    body = json.dumps({
        "model": actual_model,
        "max_tokens": 2048,
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

        # 提取文本
        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text = block["text"]
                break
        if not text:
            text = data["content"][0].get("text", data["content"][0].get("thinking", str(data["content"])))

        # 提取 token 用量
        usage = data.get("usage", {})
        return {
            "text": text,
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "model": data.get("model", actual_model),
            "stop_reason": data.get("stop_reason", ""),
        }

    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8") if e.fp else ""
        return {"text": f"ERROR: HTTP {e.code} - {err_body[:500]}", "error": True}
    except Exception as e:
        return {"text": f"ERROR: {e}", "error": True}


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
