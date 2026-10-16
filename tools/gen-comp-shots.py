#!/usr/bin/env python3
"""生成 gx-datav 单组件画廊截图脚本（给 Gox 主仓的截图流水线当输入）。

每个组件一个脚本，默认落到 `<GOX_CORE>/testdata/shots/datav-c-<name>.js`，
再由主仓的 `go test ./gfx/ -run TestGalleryShotScripts` 离屏渲染成 PNG。

用法:
    GOX_CORE=/path/to/Gox python3 tools/gen-comp-shots.py

设计取舍（踩过的坑都在对应组件下面写着，改的时候别丢）：
- 全部用**静态值**而不是 signal getter：截图要可复现，且首帧即目标值
  （CountUp / FlipBoard 的初值就是 fmt(目标)，静态值不会停在 0）。
- 数据一律走确定性种子（seriesRandomWalk / makeRng 带 seed）。
- 不套 BorderBox：单组件图要让组件本身占满画面，边框会抢戏。
- 画布尺寸按**内容实际尺度**给，不是一律大画布：StatusLight / Timeline /
  WordCloud 是内容自适应宽度的组件，画布开太大只会留一片空白，看着像
  "没铺开"（实测踩过：600 画布配 480 宽度，内容只占 100px）。
"""

import os

# 主仓位置：优先环境变量，缺省与本仓平级
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOX_CORE = os.environ.get("GOX_CORE") or os.path.join(os.path.dirname(PKG), "Gox")
OUT = os.path.join(GOX_CORE, "testdata", "shots")

# 公共数据片段（确定性）
HOURS24 = 'const HOURS = Array.from({ length: 24 }, (_, i) => (i < 10 ? "0" + i : String(i)) + ":00");'
HOURS9 = 'const HOURS = ["00", "03", "06", "09", "12", "15", "18", "21", "24"];'
REGIONS = 'const REGIONS = ["0h", "2h", "4h", "6h", "8h", "10h", "12h", "14h", "16h", "18h", "20h", "22h"];'
DAYS = 'const DAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];'

SCATTER = '''function makeScatter(n, cx, cy, seed) {
  const rng = makeRng(seed);
  const out = [];
  for (let i = 0; i < n; i++) {
    out.push({
      x: Math.round(cx + (rng() - 0.5) * 60),
      y: Math.round(cy + (rng() - 0.5) * 50),
      r: 4 + Math.round(rng() * 20),
    });
  }
  return out;
}'''

HEAT = '''function makeHeat() {
  const rng = makeRng(77);
  const out = [];
  for (let d = 0; d < 7; d++) {
    const row = [];
    for (let h = 0; h < 24; h++) {
      const base = 40 * Math.exp(-Math.pow((h - 11) / 4.5, 2)) + 55 * Math.exp(-Math.pow((h - 20) / 3, 2));
      row.push(Math.round(Math.max(2, base * (0.55 + rng() * 0.7))));
    }
    out.push(row);
  }
  return out;
}'''

WORDS = '''const WORDS = [
  { text: "转化率", weight: 100 }, { text: "留存", weight: 82 },
  { text: "GMV", weight: 76 }, { text: "复购", weight: 64 },
  { text: "拉新", weight: 58 }, { text: "客单价", weight: 52 },
  { text: "ROI", weight: 47 }, { text: "活跃", weight: 41 },
  { text: "漏斗", weight: 36 }, { text: "标签", weight: 31 },
];'''

C = [
    dict(name="border", comp="BorderBox", imports="BorderBox, TitleBar", w=560, h=300,
         desc="科技风面板边框 (6 型)",
         data="",
         body='''<BorderBox type={1} width={460} height={220}>
            <TitleBar title="核心指标" align="left" fontSize={14}/>
            <column flexGrow={1} justifyContent="center" gap={6}>
              <text font={12} color={palette.sub}>面板底 + 装饰 canvas + 内容流</text>
              <text font={12} color={palette.sub}>内容区走普通 flex，随意嵌套</text>
            </column>
          </BorderBox>'''),

    dict(name="title", comp="TitleBar", imports="TitleBar", w=340, h=200,
         desc="装饰标题 (左 / 中两种)",
         data="",
         body='''<column gap={18}>
            <TitleBar title="运营数据中心" subtitle="REAL-TIME OPERATIONS" fontSize={22} align="left"/>
            <TitleBar title="Gox 数据可视化大屏" align="center" fontSize={22}/>
          </column>'''),

    dict(name="flip", comp="FlipBoard", imports="FlipBoard", w=400, h=160,
         desc="数字翻牌器",
         data="",
         body='<FlipBoard value={3842179} digits={8} size={30} accent={palette.warn}/>'),

    dict(name="countup", comp="CountUp", imports="CountUp", w=300, h=190,
         desc="数字缓动",
         data="",
         body='''<column gap={14} alignItems="center">
            <CountUp value={128456} fontSize={30} color={palette.accent}/>
            <CountUp value={68.4} fontSize={22} decimals={1} suffix="%" color={palette.ok}/>
          </column>'''),

    dict(name="ring", comp="RingProgress", imports="RingProgress", w=280, h=280,
         desc="环形进度",
         data="",
         body='<RingProgress value={78} size={180} label="订单" sub="完成率"/>'),

    dict(name="gauge", comp="Gauge", imports="Gauge", w=360, h=340,
         desc="仪表盘 (225° 三段刻度)",
         data="",
         body='<Gauge value={72} min={0} max={100} unit="%" label="综合负载" size={280}/>'),

    dict(name="line", comp="LineChart", imports="LineChart", w=680, h=400,
         desc="多序列折线 (平滑 + 渐变面积)",
         data=HOURS24 + '''
const SERIES = [
  { name: "订单量", data: seriesRandomWalk(24, 120, 18, 7) },
  { name: "退单量", data: seriesRandomWalk(24, 30, 8, 11) },
];''',
         body='<LineChart width={600} height={320} series={SERIES} labels={HOURS} yMax={220}/>'),

    dict(name="bar", comp="BarChart", imports="BarChart", w=680, h=380,
         desc="柱状图 (彩虹柱 / 多序列)",
         data=REGIONS + '''
const BARS = seriesRandomWalk(12, 60, 22, 5, 10, 120);''',
         body='<BarChart width={600} height={280} data={BARS} labels={REGIONS}/>'),

    dict(name="combo", comp="ComboChart", imports="ComboChart", w=680, h=400,
         desc="柱线组合图 (双 Y 轴)",
         data=HOURS9 + '''
const BARS = [{ name: "销量", data: seriesRandomWalk(9, 60, 22, 31) }];
const LINES = [{ name: "转化率", data: seriesRandomWalk(9, 42, 9, 32) }];''',
         body='<ComboChart width={600} height={320} bars={BARS} lines={LINES} labels={HOURS}/>'),

    dict(name="pie", comp="PieChart", imports="PieChart", w=320, h=340,
         desc="饼图 / 环图 (悬停外扩)",
         data='''const PIE = [
  { name: "移动端", value: 4520, color: seriesColors[0] },
  { name: "PC 端", value: 3120, color: seriesColors[1] },
  { name: "小程序", value: 2180, color: seriesColors[2] },
  { name: "第三方", value: 980, color: seriesColors[3] },
];''',
         body='<PieChart donut={true} size={240} data={PIE} center="8,080" unit=" 单"/>'),

    dict(name="rose", comp="RoseChart", imports="RoseChart", w=360, h=360,
         desc="玫瑰图 (南丁格尔)",
         data='''const ROSE = [
  { name: "搜索", value: 4520 }, { name: "直访", value: 3120 },
  { name: "广告", value: 2180 }, { name: "社交", value: 1640 },
  { name: "邮件", value: 890 },
];''',
         body='<RoseChart size={280} data={ROSE}/>'),

    dict(name="radar", comp="RadarChart", imports="RadarChart", w=340, h=340,
         desc="雷达图",
         data='''const RADAR = [
  { name: "本期", values: [82, 90, 68, 76, 88, 72] },
  { name: "上期", values: [64, 72, 80, 58, 66, 82] },
];
const AXES = ["订单", "履约", "库存", "售后", "营销", "风控"];''',
         body='<RadarChart size={280} axes={AXES} series={RADAR}/>'),

    dict(name="scatter", comp="ScatterChart", imports="ScatterChart", w=680, h=400,
         desc="气泡散点图",
         data=SCATTER + '''
const SCATTER = [
  { name: "一线", data: makeScatter(14, 70, 55, 21) },
  { name: "新一线", data: makeScatter(12, 45, 40, 22) },
];''',
         body='<ScatterChart width={600} height={300} series={SCATTER} xLabel="GMV (千万)" yLabel="复购率" sizeRange={[6, 24]}/>'),

    dict(name="heatmap", comp="HeatMap", imports="HeatMap", w=800, h=360,
         desc="热力图 (7 × 24)",
         data=HOURS9 + "\n" + DAYS + "\n" + HEAT + "\nconst HEATDATA = makeHeat();",
         body='<HeatMap width={720} height={240} cellH={26} data={HEATDATA} xLabels={HOURS} yLabels={DAYS}/>'),

    dict(name="funnel", comp="FunnelChart", imports="FunnelChart", w=560, h=360,
         desc="漏斗图",
         data='''const FUNNEL = [
  { name: "曝光", value: 128400 }, { name: "点击", value: 38200 },
  { name: "加购", value: 12400 }, { name: "下单", value: 5180 },
  { name: "支付", value: 2960 },
];''',
         body='<FunnelChart width={440} data={FUNNEL}/>'),

    dict(name="ranking", comp="RankingList", imports="RankingList", w=600, h=380,
         desc="排行榜 (奖牌徽章)",
         data='''const RANKS = [
  { name: "华南大区", value: 9821 }, { name: "华东大区", value: 8764 },
  { name: "华北大区", value: 7932 }, { name: "西南大区", value: 6418 },
  { name: "西北大区", value: 5210 }, { name: "东北大区", value: 4387 },
];''',
         body='<RankingList width={480} rows={RANKS} rowHeight={40}/>'),

    dict(name="progress", comp="ProgressList", imports="ProgressList", w=600, h=360,
         desc="进度条组",
         data='''const PROGRESS = [
  { name: "存储", value: 78, max: 100 }, { name: "计算", value: 46, max: 100 },
  { name: "带宽", value: 91, max: 100 }, { name: "连接数", value: 33, max: 100 },
];''',
         body='<ProgressList width={480} rows={PROGRESS} rowHeight={34}/>'),

    dict(name="bullet", comp="BulletChart", imports="BulletChart", w=600, h=360,
         desc="子弹图 (实际 vs 目标)",
         data='''const BULLET = [
  { name: "订单量", value: 86, target: 75, max: 100 },
  { name: "退单率", value: 12, target: 15, max: 100, unit: "%" },
  { name: "履约时效", value: 94, target: 90, max: 100, unit: "%" },
  { name: "客服满意度", value: 88, target: 92, max: 100, unit: "%" },
];''',
         body='<BulletChart width={480} rows={BULLET}/>'),

    dict(name="table", comp="ScrollTable", imports="ScrollTable", w=760, h=340,
         desc="轮播表格 (无缝循环)",
         data='''const COLUMNS = [
  { key: "id", label: "订单号", width: 1.2 },
  { key: "region", label: "大区", width: 0.8 },
  { key: "ch", label: "渠道", width: 1 },
  { key: "amt", label: "金额 (元)", width: 1, align: "right" },
  { key: "st", label: "状态", width: 0.8, align: "right" },
];
const ROWS = [
  { id: "A-10241", region: "华南", ch: "线上商城", amt: 128900, st: "已完成" },
  { id: "A-10242", region: "华东", ch: "APP 推送", amt: 56200, st: "进行中" },
  { id: "A-10243", region: "华北", ch: "线下门店", amt: 93400, st: "已完成" },
  { id: "A-10244", region: "西南", ch: "第三方", amt: 27800, st: "待付款" },
  { id: "A-10245", region: "西北", ch: "线上商城", amt: 76100, st: "已完成" },
];''',
         body='<ScrollTable width={680} height={220} rowHeight={28} columns={COLUMNS} rows={ROWS}/>'),

    dict(name="clock", comp="ClockPanel", imports="ClockPanel", w=360, h=180,
         desc="时钟面板 (Temporal 驱动)",
         data="// 时间类组件：截图里是渲染那一刻的时钟，不可复现（见 README）。",
         body='<ClockPanel size={38}/>'),

    dict(name="countdown", comp="Countdown", imports="Countdown", w=380, h=200,
         desc="倒计时",
         data='const TARGET = Number(Temporal.Now.instant().epochMilliseconds) + 8 * 3600 * 1000 + 42 * 60 * 1000;',
         body='<Countdown target={TARGET} size={44}/>'),

    dict(name="liquid", comp="LiquidFill", imports="LiquidFill", w=280, h=320,
         desc="水球图",
         data="",
         body='<LiquidFill value={86} size={200} label="存储"/>'),

    dict(name="status", comp="StatusLight", imports="StatusLight", w=190, h=300,
         desc="状态指示灯组",
         # 实测口径：StatusLight 是**内容自适应宽度**的组件（灯 + 名称 + 文案
         # 从左往右排，宽度由文字撑），width prop 只决定画布多宽、不参与布局。
         # 曾经给 600 画布配 480 宽度，结果内容只占 100px，右边一大片空 ——
         # 看着像组件没铺开，实际是把画布开太大了。画布收到内容尺度即可。
         # rowHeight prop 组件不认（内部按 showDetail 定 30/20），已去掉。
         data='''const SERVICES = [
  { name: "API 网关", status: "ok", detail: "p99 38ms" },
  { name: "支付核心", status: "ok", detail: "p99 62ms" },
  { name: "搜索服务", status: "warn", detail: "延迟升高" },
  { name: "消息队列", status: "ok", detail: "堆积 0" },
  { name: "推荐引擎", status: "bad", detail: "实例 2/5 失联" },
  { name: "数据同步", status: "ok", detail: "滞后 1.2s" },
];''',
         body='<StatusLight width={168} items={SERVICES}/>'),

    dict(name="sparkline", comp="Sparkline", imports="Sparkline", w=560, h=240,
         desc="迷你趋势线 (无轴无刻度)",
         data='const TREND = seriesRandomWalk(32, 100, 22, 9);',
         body='''<column gap={16} alignItems="center">
            <Sparkline data={TREND} width={360} height={70}/>
            <Sparkline data={TREND} width={360} height={54} color={palette.ok} smooth={false}/>
          </column>'''),

    dict(name="kpicard", comp="KpiCard", imports="KpiCard", w=600, h=240,
         desc="KPI 指标卡 (含迷你趋势线)",
         data='const TREND = seriesRandomWalk(20, 100, 18, 3);',
         body='<KpiCard label="今日 GMV" value={1284560} delta={12.4} trend={TREND} width={440}/>'),

    dict(name="marquee", comp="MarqueeText", imports="MarqueeText", w=760, h=180,
         desc="滚动消息栏",
         # 画廊截图取的是**首帧**，而 MarqueeText 的 phase 从 0 起步 ——
         # off=0 时文本正好压在视口右边界外，画面上只剩左边那枚菱形标记
         # （实测非底色像素 201，判为近乎空白）。真跑起来一秒后文字就滑进来了，
         # 但截图永远停在那一刻。这里改用**短消息**走组件的静态分支
         # （cycleW <= inner 时不滚，直接画在 x0）—— 顺带让截图能看清全文，
         # 比一条滑了一半的跑马灯有信息量。
         data="// 短消息 → 组件走静态分支（不滚），否则首帧文本在视口外，截图一片空。",
         body='<MarqueeText text="● 双十一预热进行中 · 库存同步任务 12/12 完成 · 支付通道延迟恢复正常" speed={70} fontSize={15} accent={palette.warn}/>'),

    dict(name="timeline", comp="Timeline", imports="Timeline", w=300, h=440,
         desc="时间轴",
         # Timeline 同样内容自适应：右边界是文字截断宽度（ctx.width - tx）。
         # 画布给 680 时事件文案短，只画到 183px，右边空一半。收到 460 后
         # 截断宽度与最长文案相称，画面才平衡。
         data='''const EVENTS = [
  { time: "16:58", title: "支付通道延迟恢复", detail: "延迟从 210ms 回落至 38ms", status: "ok" },
  { time: "16:41", title: "推荐引擎实例失联", detail: "node-07 / node-09 心跳超时", status: "bad" },
  { time: "16:20", title: "搜索服务延迟升高", detail: "p99 超过 500ms 阈值", status: "warn" },
  { time: "15:55", title: "大促预热活动上线", detail: "双十一主会场 · 全量发布", status: "info" },
  { time: "15:30", title: "库存同步任务完成", detail: "12/12 分片 · 零差异", status: "ok" },
];''',
         body='<Timeline width={268} events={EVENTS}/>'),

    dict(name="flight", comp="FlightLines", imports="FlightLines", w=760, h=500,
         desc="飞线图",
         data='''const LINES = [
  { from: [80, 300], to: [300, 90], value: 128 },
  { from: [120, 330], to: [430, 150], value: 96 },
  { from: [300, 90], to: [490, 280], value: 64 },
  { from: [430, 150], to: [180, 180], value: 42 },
  { from: [80, 300], to: [490, 280], value: 31 },
];
const LABELS = [
  { x: 66, y: 318, text: "华南仓" }, { x: 276, y: 66, text: "华东枢纽" },
  { x: 404, y: 168, text: "华北仓" }, { x: 462, y: 300, text: "西北仓" },
  { x: 156, y: 196, text: "西南仓" },
];''',
         body='<FlightLines width={560} height={380} lines={LINES} labels={LABELS}/>'),

    dict(name="wordcloud", comp="WordCloud", imports="WordCloud", w=340, h=420,
         desc="词云 (螺旋布局)",
         # 词云的字号由 weight 归一化到 [minSize, maxSize]，螺线从中心外扩，
         # 占多大是数据说了算。画布 680 时只聚在中间 221px。收到 480 后
         # 密集度上来了；词少的话再多给词，别指望它自己铺满。
         data=WORDS,
         body='<WordCloud width={300} height={320} words={WORDS}/>'),
]

# 数据段里用到的工具函数，必须一并 import。
#
# 血泪教训：Gox 的缺名导入**不报错**（缺的那个名字静默变 undefined），
# 于是 data 段第一次调用时才炸，或者直接算出 NaN 画不出东西。2026-10-15
# heatmap.js 就是从 theme.js 导入 draw.js 才有的 mix，整块热力图只剩一行
# 行标签。这里按脚本显式列出，别指望"反正不报错"。
TOOLS = {
    "line": "seriesRandomWalk",
    "bar": "seriesRandomWalk",
    "combo": "seriesRandomWalk",
    "pie": "seriesColors",
    "scatter": "makeRng",
    "heatmap": "makeRng",
    "sparkline": "seriesRandomWalk",
    "kpicard": "seriesRandomWalk",
}

TPL = '''// 画廊截图: gx-datav 单组件 —— {comp}（{desc}）
//
// 单组件图: 不套 BorderBox（边框会抢戏），组件直接居中在深空底上。
// 一律静态值 + 确定性种子 —— 截图要能复现。
import {{ render }} from "gox";
import {{ {allimports} }} from "../datav/index.js";

{data}

render(
  <window title="gx-datav · {comp}" width={{{w}}} height={{{h}}} hideFocusRing={{true}}>
    <column width="100%" height="100%" background={{palette.bg}} padding={{16}}>
      <row flexGrow={{1}} alignItems="center" justifyContent="center">
        {body}
      </row>
    </column>
  </window>
);
'''

os.makedirs(OUT, exist_ok=True)
for c in C:
    names = [c["imports"], "palette"]
    if c["name"] in TOOLS:
        names.append(TOOLS[c["name"]])
    src = TPL.format(
        comp=c["comp"], desc=c["desc"], allimports=", ".join(names),
        w=c["w"], h=c["h"], data=c["data"], body=c["body"],
    )
    # 数据段为空时不要留空行
    src = src.replace("\n\n\nrender(", "\n\nrender(")
    path = os.path.join(OUT, "datav-c-%s.js" % c["name"])
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("写", path)
print("\n共", len(C), "个脚本")
