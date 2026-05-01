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
        s = parse_skill(f)
        if s: skills.append(s)
    return skills


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
    from llm_runner import call, ANTHROPIC_MODEL

    model = model or ANTHROPIC_MODEL
    log = _setup_logger(birth, gender, model)

    skills = load_all_skills()
    if not skills:
        log.error("workflow.no_skills")
        print("错误：未加载到任何 skill 文件")
        return {}

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
        f.write(f"```\n{chart_text}\n```\n")
    if verbose:
        print(f"实时输出: {out_file}\n")

    outputs = {}

    for i, skill in enumerate(skills):
        step_num = i + 1
        t0 = _time.time()
        if verbose:
            print(f"[{step_num}/{len(skills)}] {skill.id} — {skill.name} ... ", end="", flush=True)

        # 构建上下文：排盘 + 全部前序步骤输出
        user_parts = [f"## 排盘数据\n{chart_text}"]
        prior_ids = []
        for sid, text in outputs.items():
            prior_ids.append(sid)
            if len(text) > 3000 and step_num <= 5:
                text = text[:3000] + "\n...(截断)"
            user_parts.append(f"## {sid} 输出\n{text}")
        user_prompt = "\n\n".join(user_parts)

        # 记录本步输入
        log.info("step.start", step=step_num, skill_id=skill.id, skill_name=skill.name,
                 system_prompt_len=len(skill.content), system_prompt_preview=skill.content[:300],
                 user_prompt_len=len(user_prompt), prior_steps=prior_ids,
                 declared_deps=skill.required_inputs)

        # 调用 LLM
        result = call(skill.content, user_prompt, model=model)
        elapsed = round(_time.time() - t0, 2)

        if result.startswith("ERROR"):
            if verbose:
                print(f"失败: {result[:100]}")
            result = f"执行失败: {result}"
            outputs[skill.id] = result
            log.error("step.failed", step=step_num, skill_id=skill.id,
                      error=result[:300], elapsed_s=elapsed)
        else:
            outputs[skill.id] = result
            log.info("step.done", step=step_num, skill_id=skill.id,
                     output_len=len(result), output_preview=result[:300],
                     elapsed_s=elapsed)
            if verbose:
                preview = result[:80].replace('\n', ' ')
                print(f"OK ({len(result)}字/{elapsed}s) — {preview}...")

        # 实时写入
        _write_step(out_file, skill.id, skill.name, outputs[skill.id])

    log.info("workflow.done", total_steps=len(skills), output_file=str(out_file))
    if verbose:
        print(f"\n全部 {len(skills)} 步执行完毕 → {out_file}")

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
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: summary, prompt, run")
