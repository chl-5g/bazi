"""
八字推命 Workflow 引擎。

只做三件事：加载 skills、按顺序执行、传递上下文。
每个步骤的 prompt 在 ~/bazi/skills/*.md 中独立维护，可单独迭代。

用法：
    python bazi_workflow.py summary              # 列出所有步骤
    python bazi_workflow.py prompt               # 输出完整 prompt（供人工审阅）
    python bazi_workflow.py run "1984-05-18 14:00" 乾造 黑龙江  # 自动执行全流程
"""

import os, sys, re
from dataclasses import dataclass, field
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"

@dataclass
class ClassicalRef:
    quote: str; source: str; question: str

@dataclass
class Skill:
    id: str; name: str; content: str
    required_inputs: list = field(default_factory=list)
    checks: list = field(default_factory=list)


def parse_skill(filepath: Path) -> Skill | None:
    """解析 skill 文件。格式：
    # 步骤名
    (id: sXX_xxx)
    前置: s01_xxx, s02_xxx
    校验: [来源]「原文」→ 问题

    ## System Prompt
    ...
    """
    text = filepath.read_text(encoding='utf-8')
    lines = text.split('\n')

    name = ""; sid = ""; required = []; checks = []; prompt_start = 0

    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('# ') and not name:
            name = s[2:].strip()
        elif s.startswith('(id: ') and not sid:
            sid = s[5:].split(')')[0].strip()
        elif s.startswith('前置:') and not required:
            reqs = s[3:].strip()
            if reqs: required = [r.strip() for r in reqs.split(',')]
        elif s.startswith('校验:'):
            check = s[3:].strip()
            parts = check.split('→', 1)
            q = parts[1].strip() if len(parts) > 1 else ""
            m = re.match(r'\[(.+?)\]\s*「(.+?)」', parts[0].strip())
            if m: checks.append(ClassicalRef(m.group(2), m.group(1), q))
        elif s.startswith('## System Prompt'):
            prompt_start = i + 1
            break

    if not sid or prompt_start == 0:
        return None

    content = '\n'.join(lines[prompt_start:]).strip()
    for r in required:
        content = content.replace('{' + r + '}', '{{' + r + '}}')

    return Skill(id=sid, name=name, content=content,
                 required_inputs=required, checks=checks)


def load_all_skills() -> list[Skill]:
    skills = []
    for f in sorted(SKILLS_DIR.glob('s*.md')):
        if f.name == 's00_mechanism.md':
            continue  # s00 作为静态知识注入，不占独立步骤
        s = parse_skill(f)
        if s: skills.append(s)
    return skills


def load_mechanism() -> str:
    """加载底层机制，注入所有步骤的 system prompt 前缀。"""
    f = SKILLS_DIR / 's00_mechanism.md'
    if f.exists():
        s = parse_skill(f)
        if s:
            return f"【底层机制——必须在分析前内化】\n{s.content}\n---\n"
    return ""


def build_prompt() -> str:
    skills = load_all_skills()
    lines = ["# 八字推命 Workflow ({0}步)".format(len(skills)), "",
             "统一方法论：盲派课程(42节)+六本古籍。",
             "严格顺序，每步校验通过才进下一步。校验不过→回退。", ""]
    for i, s in enumerate(skills):
        lines.append(f"---\n## 步骤{i+1}：{s.name}\n({s.id})")
        if s.required_inputs:
            lines.append(f"前置：{', '.join(s.required_inputs)}")
        if s.checks:
            for c in s.checks:
                lines.append(f"校验：[{c.source}]「{c.quote}」→ {c.question}")
        lines.append("")
        lines.append(s.content)
        lines.append("")
    return '\n'.join(lines)


def print_summary():
    skills = load_all_skills()
    for i, s in enumerate(skills):
        deps = f" ← {', '.join(s.required_inputs)}" if s.required_inputs else ""
        print(f"  {i+1:2d}. {s.id}{deps} [{len(s.checks)}校验]")


# ======================== 自动执行引擎 ========================

import time as _time
import json as _json
import datetime as _dt
import structlog as _structlog

def _slug(birth: str, gender: str) -> str:
    return birth.replace(":", "").replace(" ", "_") + "_" + gender


def _out_dir() -> Path:
    d = Path(__file__).parent.parent / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _logs_dir() -> Path:
    d = Path(__file__).parent.parent / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _write_step(out_file: Path, sid: str, name: str, text: str):
    """实时追加单个步骤结果到文件。"""
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write(f"\n---\n## {sid}: {name}\n\n")
        f.write(text)
        f.write("\n")


def _setup_logger(birth: str, gender: str, model: str) -> _structlog.BoundLogger:
    """为单次 run 创建 structlog logger，输出到 JSONL 文件。"""
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = _logs_dir() / f"{ts}_{_slug(birth, gender)}.jsonl"

    _structlog.configure(
        processors=[
            _structlog.processors.TimeStamper(fmt="iso"),
            _structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=_structlog.PrintLoggerFactory(file=open(log_file, 'w', encoding='utf-8')),
        cache_logger_on_first_use=False,
    )
    log = _structlog.get_logger()
    log.info("workflow.start", birth=birth, gender=gender, model=model)
    return log


def run_workflow(birth: str, gender: str = "乾造", birthplace: str = "",
                 model: str = None, verbose: bool = True) -> dict:
    """执行完整 workflow，每步调用 LLM API。

    - 每步实时写入输出文件 + 结构化分析日志
    - 每步传入 排盘 + 全部前序步骤输出（不只按前置过滤）
    """
    from bazi_calc import get_chart, chart_to_text
    from llm_runner import call_full, ANTHROPIC_MODEL

    model = model or ANTHROPIC_MODEL
    log = _setup_logger(birth, gender, model)

    skills = load_all_skills()
    if not skills:
        log.error("workflow.no_skills")
        print("错误：未加载到任何 skill 文件")
        return {}

    # 加载底层机制，作为每个步骤 system prompt 的前缀
    mechanism = load_mechanism()

    # 排盘
    if verbose:
        print(f"排盘: {birth} {gender} {birthplace}")
    chart = get_chart(birth, gender, birthplace)
    chart_text = chart_to_text(chart)
    log.info("chart.calculated", day_master=chart['day_master'],
             qi_yun_age=chart['qi_yun']['age'])

    if verbose:
        print(f"日主: {chart['day_master']}  起运: {chart['qi_yun']['age']}岁")
        print(f"共 {len(skills)} 个分析步骤\n")

    # 初始化输出文件
    out_file = _out_dir() / f"{_slug(birth, gender)}.md"
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(f"# 八字推命结果\n\n")
        f.write(f"出生: {birth}  性别: {gender}  出生地: {birthplace}\n\n")
        f.write(f"模型: {model}  共{len(skills)}步\n\n")
        f.write(f"```\n{chart_text}\n```\n")
    if verbose:
        print(f"实时输出: {out_file}\n")

    outputs = {}
    total_input_tokens = 0
    total_output_tokens = 0
    step_stats = []

    for i, skill in enumerate(skills):
        step_num = i + 1
        t0 = _time.time()
        if verbose:
            print(f"[{step_num}/{len(skills)}] {skill.id} — {skill.name} ... ", end="", flush=True)

        # 构建上下文：排盘 + 全部前序步骤输出（每步只取结论，截断到500字）
        user_parts = [f"## 排盘数据\n{chart_text}"]
        prior_ids = []
        for sid, text in outputs.items():
            prior_ids.append(sid)
            # 只保留尾部（结论部分），大幅削减上下文
            if len(text) > 500:
                text = text[-500:] + "\n...(前文已截断)"
            user_parts.append(f"## {sid}\n{text}")
        user_prompt = "\n\n".join(user_parts)

        # 注入底层机制作为 system prompt 前缀
        system_prompt = mechanism + skill.content if mechanism else skill.content

        # 调用 LLM（使用 call_full 获取完整返回数据）
        full = call_full(system_prompt, user_prompt, model=model)
        elapsed = round(_time.time() - t0, 2)
        text = full["text"]
        is_error = full.get("error", False)
        in_tok = full.get("input_tokens", 0)
        out_tok = full.get("output_tokens", 0)
        total_input_tokens += in_tok
        total_output_tokens += out_tok

        if is_error or text.startswith("ERROR"):
            if verbose:
                print(f"失败: {text[:100]}")
            text = f"执行失败: {text}"
            outputs[skill.id] = text
            log.error("step.failed", step=step_num, skill_id=skill.id,
                      skill_name=skill.name, error=text[:500], elapsed_s=elapsed,
                      input_tokens=in_tok, output_tokens=out_tok,
                      total_input_tokens=total_input_tokens,
                      total_output_tokens=total_output_tokens)
        else:
            outputs[skill.id] = text
            log.info("step.done", step=step_num, skill_id=skill.id,
                     skill_name=skill.name,
                     output_len=len(text), output_full=text,
                     input_tokens=in_tok, output_tokens=out_tok,
                     total_input_tokens=total_input_tokens,
                     total_output_tokens=total_output_tokens,
                     elapsed_s=elapsed, model=full.get("model", model),
                     stop_reason=full.get("stop_reason", ""))
            if verbose:
                preview = text[:80].replace('\n', ' ')
                print(f"OK ({len(text)}字/{elapsed}s/{in_tok}+{out_tok}tk) — {preview}...")

        step_stats.append({
            "step": step_num, "skill_id": skill.id, "skill_name": skill.name,
            "output_len": len(text), "input_tokens": in_tok, "output_tokens": out_tok,
            "elapsed_s": elapsed, "error": is_error,
        })

        # 实时写入
        _write_step(out_file, skill.id, skill.name, outputs[skill.id])

    # 写入汇总统计
    with open(out_file, 'a', encoding='utf-8') as f:
        f.write(f"\n---\n## 执行统计\n\n")
        f.write(f"| 步骤 | Skill | 输出字数 | 输入tk | 输出tk | 耗时 |\n")
        f.write(f"|------|-------|---------|--------|--------|------|\n")
        for s in step_stats:
            status = "ERR" if s["error"] else "OK"
            f.write(f"| {s['step']} | {s['skill_id']} | {s['output_len']} | {s['input_tokens']} | {s['output_tokens']} | {s['elapsed_s']}s |\n")
        f.write(f"\n**总计**: {total_input_tokens} input + {total_output_tokens} output = {total_input_tokens + total_output_tokens} tokens\n")

    log.info("workflow.done", total_steps=len(skills),
             total_input_tokens=total_input_tokens,
             total_output_tokens=total_output_tokens,
             total_tokens=total_input_tokens + total_output_tokens,
             output_file=str(out_file))

    if verbose:
        print(f"\n全部 {len(skills)} 步执行完毕 → {out_file}")
        print(f"Token: {total_input_tokens} in + {total_output_tokens} out = {total_input_tokens + total_output_tokens}")

    return outputs


def save_results(birth: str, gender: str, outputs: dict, out_dir: Path = None):
    """（兼容旧接口）批量保存。新代码推荐用 run_workflow 自带实时写入。"""
    if out_dir is None:
        out_dir = _out_dir()
    out_file = out_dir / f"{_slug(birth, gender)}.md"

    skills = {s.id: s for s in load_all_skills()}
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(f"# 八字推命结果\n\n")
        f.write(f"出生: {birth}  性别: {gender}\n\n")
        for sid, text in outputs.items():
            skill = skills.get(sid)
            name = skill.name if skill else sid
            f.write(f"\n---\n## {sid}: {name}\n\n")
            f.write(text)
            f.write("\n")
    return out_file


# ======================== CLI ========================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：")
        print("  python bazi_workflow.py summary")
        print("  python bazi_workflow.py prompt")
        print("  python bazi_workflow.py run 'YYYY-MM-DD HH:MM' 乾造 [出生地]")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "summary":
        print_summary()
    elif cmd == "prompt":
        print(build_prompt())
    elif cmd == "run":
        if len(sys.argv) < 3:
            print("请提供出生时间: python bazi_workflow.py run 'YYYY-MM-DD HH:MM' 乾造 [出生地]")
            sys.exit(1)
        birth = sys.argv[2]
        gender = sys.argv[3] if len(sys.argv) > 3 else "乾造"
        birthplace = sys.argv[4] if len(sys.argv) > 4 else ""

        outputs = run_workflow(birth, gender, birthplace)
        print(f"\n完整结果: {_out_dir() / _slug(birth, gender)}.md")

    elif cmd == "test":
        # 单步测试：只跑一个 skill，秒级验证
        # python bazi_workflow.py test s03 "1961-09-27 06:00" 乾造 [出生地] [--std STANDARD.md]
        if len(sys.argv) < 4:
            print("用法: python bazi_workflow.py test <skill_id> 'YYYY-MM-DD HH:MM' 乾造 [出生地] [--std STANDARD.md]")
            sys.exit(1)

        sid = sys.argv[2]
        birth = sys.argv[3]
        gender = sys.argv[4] if len(sys.argv) > 4 else "乾造"
        birthplace = ""
        std_file = None

        for i, arg in enumerate(sys.argv[5:], start=5):
            if arg == "--std" and i + 1 < len(sys.argv):
                std_file = Path(sys.argv[i + 1])
            elif sys.argv[i-1] != "--std":
                birthplace = arg

        from bazi_calc import get_chart, chart_to_text
        from llm_runner import call_full, ANTHROPIC_MODEL

        all_skills = {s.id: s for s in load_all_skills()}
        skill = all_skills.get(sid)
        if not skill:
            print(f"未知 skill: {sid}")
            print(f"可用: {', '.join(all_skills.keys())}")
            sys.exit(1)

        # 排盘
        chart = get_chart(birth, gender, birthplace)
        chart_text = chart_to_text(chart)
        print(f"排盘: {birth} {gender} {birthplace}")
        print(f"日主: {chart['day_master']}  起运: {chart['qi_yun']['age']}岁")
        print(f"测试: {sid} — {skill.name}\n")

        # 构建上下文
        mechanism = load_mechanism()
        user_parts = [f"## 排盘数据\n{chart_text}"]

        if std_file and std_file.exists():
            # 从标准答案文件读取前序步骤输出
            std_text = std_file.read_text(encoding='utf-8')
            import re
            # 找到目标 skill 之前的步骤
            skill_order = [s.id for s in load_all_skills()]
            target_idx = skill_order.index(sid)
            for prior_sid in skill_order[:target_idx]:
                # 匹配 ## sXX_xxx: ... 到下一个 ## 之间的内容
                pattern = rf'## {prior_sid}:.*?\n(.*?)(?=\n## s|\Z)'
                m = re.search(pattern, std_text, re.DOTALL)
                if m:
                    prior_text = m.group(1).strip()
                    if len(prior_text) > 500:
                        prior_text = prior_text[-500:]
                    user_parts.append(f"## {prior_sid} (标准答案)\n{prior_text}")
                    print(f"  + {prior_sid} 标准答案已注入")
            print()

        user_prompt = "\n\n".join(user_parts)
        system_prompt = mechanism + skill.content if mechanism else skill.content

        print(f"System prompt: {len(system_prompt)} 字")
        print(f"User prompt: {len(user_prompt)} 字")
        print(f"调用 LLM ...\n")

        full = call_full(system_prompt, user_prompt)
        print(full["text"])
        print(f"\n--- Token: {full.get('input_tokens', '?')} in + {full.get('output_tokens', '?')} out ---")
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: summary, prompt, run")
