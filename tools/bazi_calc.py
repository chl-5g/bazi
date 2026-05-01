"""
八字排盘底座模块。封装 lunar_python，供 workflow 调用。

用法：
    python bazi_calc.py "1984-05-18 14:00" 乾造 北京
"""

import sys, json
from lunar_python import Solar


def get_chart(birth: str, gender: str = "乾造", birthplace: str = "") -> dict:
    """输入公历时间，返回完整八字排盘 JSON。"""
    dt = birth.strip()
    date_part, time_part = (dt.split(" ", 1) + ["00:00"])[:2]
    h, m, s = (time_part.replace(":", " ").split() + ["0", "0"])[:3]

    y, mo, d = [int(x) for x in date_part.split("-")]
    solar = Solar.fromYmdHms(y, mo, d, int(h), int(m), int(s))
    lunar = solar.getLunar()
    ec = lunar.getEightChar()

    g = 1 if gender in ("乾造", "男", "male") else 0
    yun = ec.getYun(g)

    day_gan = ec.getDayGan()

    def pillar(label):
        return {
            "gan": getattr(ec, f"get{label}Gan")(),
            "zhi": getattr(ec, f"get{label}Zhi")(),
            "cang_gan": getattr(ec, f"get{label}HideGan")() or [],
            "shi_shen_gan": getattr(ec, f"get{label}ShiShenGan")(),
            "shi_shen_zhi": getattr(ec, f"get{label}ShiShenZhi")(),
            "na_yin": getattr(ec, f"get{label}NaYin")(),
            "xun_kong": getattr(ec, f"get{label}XunKong")(),
            "di_shi": getattr(ec, f"get{label}DiShi")(),
        }

    da_yun = []
    for dy in yun.getDaYun()[:10]:
        gz = dy.getGanZhi()
        gz_str = gz.toString() if hasattr(gz, 'toString') else str(gz)
        if not gz_str or gz_str.strip() == '': continue
        da_yun.append({
            "index": dy.getIndex(),
            "gan_zhi": gz_str,
            "start_age": dy.getStartAge(),
            "end_age": dy.getEndAge(),
            "start_year": dy.getStartYear(),
            "end_year": dy.getEndYear(),
        })

    return {
        "birth": birth, "gender": gender, "birthplace": birthplace,
        "year": pillar("Year"), "month": pillar("Month"),
        "day": pillar("Day"), "hour": pillar("Time"),
        "day_master": day_gan,
        "qi_yun": {
            "age": yun.getStartYear(),
            "year": solar.getYear() + yun.getStartYear(),
            "month": yun.getStartMonth(),
            "day": yun.getStartDay(),
        },
        "da_yun": da_yun,
    }


def chart_to_text(chart: dict) -> str:
    """排盘转可读文本，喂给 LLM。"""
    c = chart
    lines = [
        f"四柱：{c['year']['gan']}{c['year']['zhi']} {c['month']['gan']}{c['month']['zhi']} {c['day']['gan']}{c['day']['zhi']} {c['hour']['gan']}{c['hour']['zhi']}",
        f"性别：{c['gender']}  日主：{c['day_master']}",
        "",
        "藏干：",
        f"  年{c['year']['zhi']}：{', '.join(c['year']['cang_gan'])}",
        f"  月{c['month']['zhi']}：{', '.join(c['month']['cang_gan'])}",
        f"  日{c['day']['zhi']}：{', '.join(c['day']['cang_gan'])}",
        f"  时{c['hour']['zhi']}：{', '.join(c['hour']['cang_gan'])}",
        "",
        "十神（天干/地支）：",
        f"  年：{c['year']['shi_shen_gan']}/{c['year']['shi_shen_zhi']}",
        f"  月：{c['month']['shi_shen_gan']}/{c['month']['shi_shen_zhi']}",
        f"  日：{c['day']['shi_shen_gan']}/{c['day']['shi_shen_zhi']}",
        f"  时：{c['hour']['shi_shen_gan']}/{c['hour']['shi_shen_zhi']}",
        "",
        "纳音：",
        f"  {c['year']['na_yin']} / {c['month']['na_yin']} / {c['day']['na_yin']} / {c['hour']['na_yin']}",
        "",
        f"起运：{c['qi_yun']['age']}岁（{c['qi_yun']['year']}年{c['qi_yun']['month']}月）",
        "",
        "大运：",
    ]
    for dy in c["da_yun"]:
        lines.append(f"  {dy['gan_zhi']}  {dy['start_age']}-{dy['end_age']}岁 ({dy['start_year']}-{dy['end_year']})")
    return '\n'.join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python bazi_calc.py 'YYYY-MM-DD HH:MM' 乾造 [北京]")
        sys.exit(1)
    c = get_chart(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
    print(chart_to_text(c))
