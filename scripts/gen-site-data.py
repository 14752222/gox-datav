#!/usr/bin/env python3
"""从组件源码生成展示站的数据文件（docs/components.json）。

为什么不手抄：29 个组件、每个一份 props 说明，手抄必然与源码脱节 ——
源码改了注释、站点还印着旧参数，用户照着写就报错。这里直接解析组件
源码里的注释块，站点数据与源码注释同源。

解析口径（踩过的坑都写在这，改的时候别再踩）：
  1. props 段**不一定在文件头部** —— BorderBox 的 props 在文件中部的
     注释块里（头部先讲结构设计与六种边框）。所以扫全文件的 `//` 行，
     取最后一次出现的 `props:` 段落。
  2. props 条目的说明**可能折行** —— bar.js 的 series 说明占三行，
     第三行缩进对齐。续行没有 `名字` 开头，要拼到上一条的 desc 里，
     不能当成段落结束（v1 就是这么把 8 项截成 1 项的）。
  3. 段落结束的判据是**出现第一行非注释代码**（import/function/export），
     不是"下一行没有名字开头"。
  4. FlipBoard 与 CountUp 同在 flip.js，各自有独立注释块 —— 按组件名
     找它自己那段，别拿文件头那段当两个组件的说明。
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
SRC = os.path.join(PKG, "src")


def head_block(text):
    """文件头部注释块（第 1 行开始的第一段连续 // 行）。

    简介一律取这里 —— props 所在的块可能在文件中段（BorderBox），
    那段是给读实现的人看的，第一行常是"用法同文件头"，当简介用会文不对题。
    """
    block = []
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith("//"):
            block.append(s[2:].strip())
        elif block:
            break
        elif s:
            break
    return block


def props_block(text, comp):
    """找出 comp 对应的含 props 段的注释块（可能不在文件头部）。"""
    lines = text.split("\n")
    blocks, cur = [], []
    for ln in lines:
        s = ln.strip()
        if s.startswith("//"):
            cur.append(s[2:].strip())
        else:
            if cur:
                blocks.append(cur)
                cur = []
    if cur:
        blocks.append(cur)

    # 优先：块里既有 props: 又提到组件名（flip.js 里 FlipBoard/CountUp 各一块）
    named = [b for b in blocks if any(x.startswith("props") for x in b)
             and any(comp in x for x in b)]
    if named:
        return named[-1]
    withprops = [b for b in blocks if any(x.startswith("props") for x in b)]
    if withprops:
        return withprops[-1]
    return []


def clean(s):
    """去掉 markdown 记号（注释里混 ** 粗体、` 反引号）。"""
    s = s.replace("**", "").replace("`", "")
    return re.sub(r"\s+", " ", s).strip()


def parse_desc(text, comp):
    """简介取组件自己那段注释块 —— 不一定是文件头。

    flip.js 里有三个注释块（文件头讲用途、FlipBoard 段、CountUp 段），
    取文件头的话 CountUp 会印上 FlipBoard 的说明。这里先在"含组件名的
    注释块"里找，找不到再退回文件头。
    """
    lines = text.split("\n")
    blocks, cur = [], []
    for ln in lines:
        s = ln.strip()
        if s.startswith("//"):
            cur.append(s[2:].strip())
        else:
            if cur:
                blocks.append(cur)
                cur = []
    if cur:
        blocks.append(cur)

    title = [b for b in blocks
             if b and b[0].startswith("=====") and comp in b[0]]
    block = title[-1] if title else head_block(text)

    out = []
    for s in block:
        if s.startswith("====="):
            # 标题行有几种写法：
            #   "===== gx-datav BorderBox 科技风边框 ====="   → 取后半
            #   "===== FlipBoard 翻牌器 ====="               → 取后半
            #   "===== gx-datav 数字组件: 翻牌器 + 数字动效 =====" → 泛化标题，丢弃
            m = re.match(r"^=+\s*(.*?)\s*=+$", s)
            if m:
                t = m.group(1)
                if "——" in t:
                    out.append(t.split("——", 1)[1])
                elif not t.startswith("gx-datav ") and ":" not in t:
                    parts = t.split(" ", 1)
                    if len(parts) == 2 and parts[1] != "组件":
                        out.append(parts[1])
                elif t.startswith("gx-datav "):
                    # "gx-datav BorderBox 科技风边框" → 去掉前缀
                    rest = t[len("gx-datav "):]
                    parts = rest.split(" ")
                    if len(parts) >= 2:
                        out.append(" ".join(parts[1:]))
            continue
        if s.startswith("props"):
            break
        out.append(s)
    desc = clean(" ".join(x for x in out if x))
    desc = re.sub(r"^\S+\s+——\s*", "", desc)
    return desc


def parse_props(text, comp):
    block = props_block(text, comp)
    props, in_props = [], False
    for s in block:
        if s.startswith("props"):
            in_props = True
            continue
        if not in_props:
            continue
        m = re.match(r"^([a-zA-Z][\w]*)\s+(.*)$", s)
        if m and _looks_like_prop(m.group(1)):
            props.append({"name": m.group(1), "desc": clean(m.group(2))})
        elif props:
            props[-1]["desc"] = clean(props[-1]["desc"] + " " + s)
    return props


def _looks_like_prop(name):
    """排掉说明性文字被误当成 prop 名字的情况。

    props 名一律小写驼峰/单词（width、showValue、rowHeight…）；
    说明续行常以中文或大写开头，会被正则挡掉。这里再放宽兜一层：
    名字长度 <= 12 且不含中文。
    """
    return len(name) <= 12 and not re.search(r"[\u4e00-\u9fff]", name)


FILE_OF = {
    "BorderBox": "border", "TitleBar": "title", "FlipBoard": "flip",
    "CountUp": "flip", "RingProgress": "ring", "Gauge": "gauge",
    "LineChart": "line", "BarChart": "bar", "ComboChart": "combo",
    "PieChart": "pie", "RoseChart": "rose", "RadarChart": "radar",
    "ScatterChart": "scatter", "HeatMap": "heatmap", "FunnelChart": "funnel",
    "RankingList": "ranking", "ProgressList": "progress", "BulletChart": "bullet",
    "ScrollTable": "table", "ClockPanel": "clock", "Countdown": "countdown",
    "LiquidFill": "liquid", "StatusLight": "status", "Sparkline": "sparkline",
    "KpiCard": "kpicard", "MarqueeText": "marquee", "Timeline": "timeline",
    "FlightLines": "flight", "WordCloud": "wordcloud",
}

SHOT_SLUG = {
    "BorderBox": "border", "TitleBar": "title", "FlipBoard": "flip",
    "CountUp": "countup", "RingProgress": "ring", "Gauge": "gauge",
    "LineChart": "line", "BarChart": "bar", "ComboChart": "combo",
    "PieChart": "pie", "RoseChart": "rose", "RadarChart": "radar",
    "ScatterChart": "scatter", "HeatMap": "heatmap", "FunnelChart": "funnel",
    "RankingList": "ranking", "ProgressList": "progress", "BulletChart": "bullet",
    "ScrollTable": "table", "ClockPanel": "clock", "Countdown": "countdown",
    "LiquidFill": "liquid", "StatusLight": "status", "Sparkline": "sparkline",
    "KpiCard": "kpicard", "MarqueeText": "marquee", "Timeline": "timeline",
    "FlightLines": "flight", "WordCloud": "wordcloud",
}

GROUP = {
    "BorderBox": "布局与容器", "TitleBar": "布局与容器",
    "FlipBoard": "数字与指标", "CountUp": "数字与指标", "KpiCard": "数字与指标",
    "Sparkline": "数字与指标", "ProgressList": "数字与指标",
    "RankingList": "数字与指标", "BulletChart": "数字与指标",
    "RingProgress": "仪表与进度", "Gauge": "仪表与进度", "LiquidFill": "仪表与进度",
    "LineChart": "图表", "BarChart": "图表", "ComboChart": "图表",
    "PieChart": "图表", "RoseChart": "图表", "RadarChart": "图表",
    "ScatterChart": "图表", "HeatMap": "图表", "FunnelChart": "图表",
    "WordCloud": "图表",
    "ScrollTable": "信息组件", "StatusLight": "信息组件", "Timeline": "信息组件",
    "MarqueeText": "信息组件", "FlightLines": "信息组件",
    "ClockPanel": "信息组件", "Countdown": "信息组件",
}
GROUP_ORDER = ["布局与容器", "数字与指标", "仪表与进度", "图表", "信息组件"]

# ─────────────────────────────────────────────────────────────────────────────
# 手工补充：源码注释里**没有** `props:` 段的组件。
#
# BorderBox / TitleBar 的注释在讲"结构为什么这么设"（绝对定位三件套、
# 变参 children、布局 prop 透传），props 表只写在 README 里。与其去改源码
# 注释（那是给读实现的人看的，塞个 props 表反而冲淡重点），不如在这里
# 补一份，并注明"来源 README"。**改这两个组件的 prop 时，README、
# 源码、这里三处都要动** —— 这个脚本存在的前提就是"别让站点与真源脱节"，
# 手工表是唯一的例外，所以单独框出来提醒。
MANUAL = {
    "BorderBox": [
        ("type", "1（经典角标）· 2 双层边框 · 3 斜切角 · 4 左光条 · 5 外框光晕 · 6 科技角"),
        ("width / height", "支持 \"100%\" 与数字"),
        ("color", "主强调色（角标 / 描边），缺省 palette.accent"),
        ("background", "面板底，缺省 palette.panel"),
        ("title", "顶部标题槽（画在装饰层上，type 6 的搭档）"),
        ("scan", "扫描线动画（type 6 氛围件），缺省 false"),
        ("padding", "内容内边距，缺省按 type（type 3 斜角要留 24）"),
        ("border / radius", "面板描边 / 圆角，缺省 true / 0"),
    ],
    "TitleBar": [
        ("title / subtitle", "主 / 副标题，缺省 \"\""),
        ("align", "\"left\" 竖条 + 翼线；\"center\" 菱形 + 双翼线，缺省 left"),
        ("fontSize / subFontSize", "字号，缺省 16 / 11"),
        ("color / textColor / subColor", "装饰 / 主文本 / 副文本色，缺省主题三色"),
        ("deco", "装饰件开关，缺省 true"),
    ],
}
MANUAL_SOURCE = {"BorderBox", "TitleBar"}


def main():
    index = open(os.path.join(SRC, "index.js"), encoding="utf-8").read()
    m = re.search(r"export const components = \{(.*?)\n\};", index, re.S)
    listed = re.findall(r'(\w+): "([^"]+)"', m.group(1))

    out = []
    for comp, short in listed:
        f = FILE_OF[comp]
        path = os.path.join(SRC, f + ".js")
        text = open(path, encoding="utf-8").read()
        desc = parse_desc(text, comp)
        props = parse_props(text, comp)
        source = "src"
        if not props and comp in MANUAL:
            props = [{"name": n, "desc": clean(d)} for n, d in MANUAL[comp]]
            source = "readme"
        out.append({
            "name": comp,
            "short": short,
            "group": GROUP[comp],
            "desc": desc,
            "props": props,
            "propsSource": source,
            # ⚠️ 路径相对**页面**（docs/index.html），不是仓库根 —— 站点根就是
            # docs/，写成 "docs/shots/..." 会被浏览器拼成 docs/docs/shots/...
            # 直接 404，29 张图全挂。2026-10-16 实测踩过：控制台 29 条 404，
            # 页面上每张卡片都是空的。别再改成仓库相对路径。
            "shot": "shots/datav-c-%s.png" % SHOT_SLUG[comp],
        })

    data = {"groups": GROUP_ORDER, "components": out}
    path = os.path.join(PKG, "docs", "components.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print("写出", path)
    warn = []
    for c in out:
        tag = ""
        if len(c["props"]) == 0:
            tag = "  ← 无 props（解析失败？）"
            warn.append(c["name"])
        print("  %-14s %-12s props %2d 项%s" % (c["name"], c["group"], len(c["props"]), tag))
    if warn:
        print("\n需人工确认:", warn)
    else:
        print("\n全部组件都解析到 props ✓")


if __name__ == "__main__":
    main()
