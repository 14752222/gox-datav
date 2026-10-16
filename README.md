# gx-datav

[![npm](https://img.shields.io/npm/v/gx-datav)](https://www.npmjs.com/package/gx-datav)
[![license](https://img.shields.io/npm/l/gx-datav)](./LICENSE)

Gox 数据大屏（DataV）组件库 —— **29 个 canvas 自绘组件**，零第三方依赖。
深空底、高饱和强调色、信号驱动的响应式数据流，全部由 `gx/gfx` 的 canvas
原语与 `gx/solid` 的信号拼出来。

> ⚠️ **这不是 Node / 浏览器包。**
> 组件依赖 Gox 内置的 `gx/gfx`（自带软件光栅化 GUI）与 JSX 语法，在 Node 或
> 浏览器里 `import` 会直接失败（找不到 `gx/gfx` 模块）。**必须先装 Gox 运行时**：
> `npm i -g @goxjs/goxjs`（详见 [Gox 项目](https://github.com/14752222/Gox)）。
> 网页上看不到实时渲染 —— `gfx` 没有浏览器后端，[WASM 图形版已实测不可行]
> (https://github.com/14752222/Gox/blob/main/docs/wasm-playground-feasibility.md)，
> 想交互只能本地 `./gox` 跑，[展示站](https://14752222.github.io/gox-datav/)
> 上是截图与代码。

## 安装与文档

```bash
gox install gx-datav     # 推荐：Gox 自带的纯 JS 包安装器，装进工程 node_modules/
# 或
npm i gx-datav           # 等价，落到同一个 node_modules/
```

```js
import { BorderBox, TitleBar, LineChart, palette } from "gx-datav";
```

📖 **[组件展示站](https://14752222.github.io/gox-datav/)** —— 29 个组件逐个带截图 +
完整 props 表（文档与源码注释同源，由脚本生成）。

## 与 `@goxjs/goxjs` 的分工

两者都走 npm registry，但角色完全不同，**互不替代**：

| 包 | 作用 | 内容 |
|---|---|---|
| `@goxjs/goxjs` | 给你**运行 Gox 的能力** | 平台二进制分发器（`bin/gox.js` 探测平台后 spawn） |
| `gx-datav`（本包） | 给你的脚本**提供库** | 纯 JS ESM 源码，供 VM 的 `import` 解析 |

`gox/npm install` 之后是 Gox 的 ESM 解析器读包入口，优先级与 Node 一致：
`exports > module > main > browser > index.*`。本包的 `exports` 只声明
`import` / `default` 两个条件 —— Gox 的条件裁剪只认这两个（`require` /
`browser` / `node` / `types` 一概不认）。

## 包内目录

```
gx-datav/
├── src/          组件与工具（随包发布）
│   ├── theme.js     色板 / 数学 / 格式化 / 文本度量 / 模拟数据流
│   ├── draw.js      绘制工具层（平滑曲线 / 渐变面积 / 光晕 / 圆角柱）
│   ├── index.js     统一导出 + components 清单
│   ├── border.js … wordcloud.js   28 个组件源文件
│   └── motion.js    值缓动公共逻辑
├── examples/     三张完整大屏（1920×1080，确定性种子，截图可复现）
│   ├── dashboard.js      全部组件齐上场
│   ├── more-charts.js    第二批图表组件
│   └── more-widgets.js   第二批信息组件
├── docs/         展示站（GitHub Pages 直接托管，**不进 npm 包**）
│   ├── index.html / assets/     零构建静态站
│   ├── components.json          站点数据，从源码注释生成
│   └── shots/                   组件截图（资产，非运行时生成）
├── scripts/      校验闸门（同步 / 站点 / 冒烟），见 scripts/README.md
└── tools/        截图脚本生成器（给 Gox 主仓的截图流水线用）
```

## 源码真源与同步

组件源码有**两份**，这是刻意的妥协，不是疏忽：

| 位置 | 角色 | 为什么 |
|---|---|---|
| 本仓 `src/` | **发布真源**（npm 包内容） | 独立发版，不依赖 Gox 主仓 |
| Gox 主仓 `testdata/datav/` | 画廊截图的**运行时依赖** | `go test ./gfx/ -run TestGalleryShotScripts` 要真读这些文件跑渲染；改成 CI checkout 会让本地测试直接跑不起来 |

防漂移靠闸门，不靠自觉：

```bash
python3 scripts/check-sync.py   # 逐字节比对两份 src，不一致即非零退出
```

组件库的**设计讨论与高难度功能清单**在另一个仓：
[Gox-hard-features](https://github.com/14752222/Gox-hard-features)。

## 许可证

[MIT](./LICENSE)

## 快速开始

```js
import { h, render, createSignal } from "gox";
import {
  BorderBox, TitleBar, RingProgress, LineChart,
  palette, seriesRandomWalk,
} from "./datav/index.js";

const [vals, setVals] = createSignal([78, 92, 64]);
const [trend, setTrend] = createSignal([
  { name: "订单量", data: seriesRandomWalk(24, 120, 18, 7) },
]);

render(
  <window title="大屏" width={1280} height={720}>
    <column width="100%" height="100%" background={palette.bg} padding={12} gap={10}>
      <BorderBox type={1} width="100%" flexGrow={1}>
        <TitleBar title="核心指标" align="left" fontSize={14}/>
        <row flexGrow={1} justifyContent="space-around" alignItems="center">
          <RingProgress value={() => vals()[0]} size={110} label="订单" sub="完成率"/>
          <RingProgress value={() => vals()[1]} size={110} color={palette.ok} label="履约" sub="及时率"/>
        </row>
      </BorderBox>
      <BorderBox type={2} width="100%" height={280}>
        <TitleBar title="24 小时订单趋势" align="left" fontSize={14}/>
        <LineChart width="100%" height={220} series={() => trend()} yMax={220}/>
      </BorderBox>
    </column>
  </window>
);

// 数据变化即重绘: 所有数据 prop 都接受 signal getter
setInterval(() => {
  setVals([rnd(60, 99), rnd(70, 99), rnd(40, 95)]);
  setTrend([{ name: "订单量", data: seriesRandomWalk(24, 120, 18, Math.floor(Math.random() * 1e6)) }]);
}, 2000);
```

跑完整示例（1920×1080，数据每 2s 模拟刷新）：

```
./gox examples/dashboard.js
```

离屏渲染截图（CI 画廊流水线，无需显示服务器）：

```
GOX_SHOTS_OUT=/tmp/shots go test ./gfx/ -run 'TestGalleryShotScripts/datav-dashboard' -v
# → /tmp/shots/linux/datav-dashboard.png
```

## 数据 prop 的两种写法

所有组件的数据类 prop 同时接受**静态值**与 **signal getter**：

```js
<LineChart series={[{ name: "A", data: [1, 2, 3] }]} />        {/* 静态 */}
<LineChart series={() => trend()} />                            {/* 响应式 */}
```

getter 在每次 `onDraw` 时求值，读取的 signal 自动成为绘制依赖 —— 数据一变，
内核标脏重绘，不需要手动调重画。**约定：组件只在首帧读一次静态配置**
（如 RankingList 的 `max`、FlipBoard 的 `digits`）；换列表请换整个 props 值。

## 主题约定

`theme.js` 导出的是**主题契约** —— demo 与自定义组件都应从这里取色，换肤只改
一个文件：

| 名称 | 值 | 用途 |
|---|---|---|
| `palette.bg` | `#070d1f` | 大屏最底层底色 |
| `palette.panel` | `rgba(13,32,74,.55)` | 面板填充（半透明，叠出层次） |
| `palette.line` | `rgba(90,130,200,.18)` | 网格 / 轴线 |
| `palette.text` / `sub` | `#dbe8ff` / `#7e93bd` | 主 / 次文本 |
| `palette.accent` | `#22e6ff` | 主强调色（青）：进度、当前值、高亮 |
| `palette.ok` / `warn` / `bad` | 绿 / 黄 / 红 | 三档状态色 |
| `seriesColors` | 8 色数组 | 图表分类色板，按索引循环取 |

公共工具随包导出：`clamp` / `lerp` / `easeOutCubic` / `polar` / `fmtInt` /
`fmtCompact` / `trimFloat` / `textWidth` / `makeRng` / `seriesRandomWalk` 等。
`textWidth` 是**估算**（CJK ≈ 1.0×字号、ASCII ≈ 0.58×），用于居中 / 避让 /
截断，不用于像素级对齐。

## 组件

### BorderBox 科技风面板边框

大屏的"大屏感"一半来自边框。6 型预置，结构是绝对定位三件套（面板底 rect +
装饰 canvas + 内容流），内容走普通 flex。

```jsx
<BorderBox type={1} width="100%" height={252} color="#22e6ff">
  <TitleBar title="核心指标" align="left" fontSize={14}/>
  {/* …任意子节点… */}
</BorderBox>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `type` | `1` | 1 经典角标 · 2 双层边框 · 3 斜切角 · 4 左光条 · 5 外框光晕 · 6 科技角 |
| `width` / `height` | — | 支持 `"100%"` 与数字 |
| `color` | `palette.accent` | 主强调色（角标 / 描边） |
| `background` | `palette.panel` | 面板底 |
| `title` | — | 顶部标题槽（画在装饰层上，type 6 的搭档） |
| `scan` | `false` | 扫描线动画（type 6 氛围件） |
| `padding` | 按 type | 内容内边距（type 3 斜角要留 24） |
| `border` / `radius` | `true` / `0` | 面板描边 / 圆角 |

> **children 是变参**：JSX 把 `<BorderBox>…</BorderBox>` 降级成
> `BorderBox(props, ...children)`（parser 层直接调用组件函数），**不是**
> `props.children`。库内嵌套组件同理：`RingProgress({...})` 直接调，
> `h(RingProgress, {...}) 会报 "tag must be a string"`（`h()` 只收字符串标签）。

### TitleBar 装饰标题

```jsx
<TitleBar title="运营数据中心" subtitle="REAL-TIME OPERATIONS" align="left" fontSize={22}/>
<TitleBar title="Gox 数据可视化大屏" align="center" fontSize={26}/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `title` / `subtitle` | `""` | 主 / 副标题 |
| `align` | `"left"` | `left` 竖条 + 翼线；`center` 菱形 + 双翼线 |
| `fontSize` / `subFontSize` | `16` / `11` | 字号 |
| `color` / `textColor` / `subColor` | 主题三色 | 装饰 / 主文本 / 副文本色 |
| `deco` | `true` | 装饰件开关 |

### FlipBoard 数字翻牌器

每位数字是一列 0-9 竖直带，值变化时该位滚过去（至少 1.5 圈，像真翻牌）。
KPI 大数字的标配。

```jsx
<FlipBoard value={() => kpi()[2].value} digits={8} size={26} accent={palette.warn}/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `value` | — | 数字或 signal getter |
| `digits` | 按 value 位数 | 固定位数（不足补零前导） |
| `size` | `34` | 单字宽，牌高 = size × 1.4 |
| `gap` | `6` | 位间距 |
| `accent` | `palette.accent` | 翻定落位色 |
| `color` / `bg` | 主题色 | 数字色 / 牌底 |

### CountUp 数字缓动

值变化时 easeOutCubic 追平，中途每帧格式化显示。适合总量 / 汇总类指标。

```jsx
<CountUp value={() => kpi()[0].value} fontSize={20} color={palette.accent}/>
<CountUp value={() => kpi()[3].value} fontSize={18} decimals={1} suffix="%" color={palette.ok}/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `value` | — | 数字或 signal getter |
| `decimals` | `0` | 小数位 |
| `prefix` / `suffix` | `""` | 前后缀（`"¥"` / `"%"`） |
| `comma` | `true` | 千分位 |
| `fontSize` / `color` | `26` / 主题色 | — |
| `duration` | `800` | 缓动 ms |

### RingProgress 环形进度

轨道 + 从 12 点顺时针的进度弧 + 端点光晕 + 中心三层文本（上标签 / 大数值 /
副标签）。数值恒显示，不被 label 替换。

```jsx
<RingProgress value={() => vals()[0]} size={110} label="订单" sub="完成率"/>
<RingProgress value={72} size={120} width={12} color={palette.ok} ticks={36} unit="%"/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `value` | — | 0~100（越界钳制），数字或 getter |
| `size` | `120` | 直径 |
| `width` | `10` | 环厚 |
| `color` / `track` | 强调色 / 暗蓝 | 进度色 / 轨道色 |
| `label` / `sub` | — / `""` | 顶部小标签 / 底部副标签 |
| `unit` | `"%"` | 数值后缀 |
| `ticks` | `0` | 外圈刻度数（0 = 不画） |
| `glow` | `true` | 端点光晕 |
| `duration` | `900` | 缓动 ms |

### Gauge 仪表盘

135° 起、225° 扫过的速度表，24 段绿→黄→红刻度带（越过警戒区变红），
指针 + 中心大数值一起缓动。

```jsx
<Gauge value={() => gaugeVal()} min={0} max={100} unit="%" label="综合负载" size={300}/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `value` | — | 当前值，数字或 getter |
| `min` / `max` | `0` / `100` | 量程 |
| `unit` / `label` | `""` | 单位串 / 底部表名 |
| `size` | `260` | 画布宽，高 = size × 0.62 |
| `color` | 强调色 | 指针色 |
| `decimals` | `0` | 数值小数位 |
| `duration` | `900` | 缓动 ms |

### LineChart 多序列折线

Catmull-Rom 平滑曲线 + 渐变面积（仅首序列）+ 数据点 + 末值标签 + 图例 +
niceCeil Y 轴。

```jsx
<LineChart
  width="100%" height={330}
  series={() => lineData()}     // [{name, color?, data: [number]}]
  labels={HOURS}                // X 轴刻度 (与 data 等长)
  yMax={220}
/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `series` | `[]` | 多序列，按索引取色板 |
| `labels` | `[]` | X 轴刻度，过密自动抽稀到 8 个 |
| `height` | `200` | 画布高（宽由容器给 `"100%"`） |
| `smooth` | `true` | Catmull-Rom 平滑；`false` 原折线 |
| `area` | `true` | 渐变面积（仅第一条线） |
| `yMax` / `yMin` | 自动 / `0` | Y 范围；自动 = 峰值 1.15 倍向上取整 |
| `yGrid` | `4` | Y 网格线数 |
| `legend` | `true` | 图例 |
| `valueFmt` | `trimFloat` 1 位 | 末值标签格式化 |

### BarChart 柱状图

顶端圆角柱 + 柱顶数值 + X 标签。单序列可用 `data` 简写（自动逐柱取色板，
大屏常见的"彩虹柱"）；多序列并列。

```jsx
<BarChart width="100%" height={190} data={() => barData()} labels={REGIONS}/>
<BarChart series={[{ name: "订单量", data: [...] }, { name: "退单量", data: [...] }]} labels={HOURS}/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `data` | — | 简写：数字数组 → 一条彩虹柱序列 |
| `series` | `[]` | 完整写法：`[{name, color?, data}]` 多序列并列 |
| `labels` | `[]` | X 轴标签 |
| `height` | `200` | 画布高 |
| `barRatio` | `0.55` | 柱宽占槽宽比 |
| `showValue` | `true` | 柱顶数值（柱宽 ≥ 18px 才放得下） |
| `yMax` / `yGrid` | 自动 / `4` | 同折线图 |
| `legend` | 多序列时开 | 图例 |

### PieChart 饼图 / 环图

实心饼与环图同一套数据，1.5° 扇区间隙，环图中心放总计。悬停命中自己算
（内核 hit-test 对 canvas 是整块矩形），悬停扇区外扩 3px、中心切换显示该项。

```jsx
<PieChart donut={true} size={190} data={() => pieData()} center="8,080" unit=" 单"
          onHover={(d) => console.log(d)}/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `data` | `[]` | `[{name, value, color?}]`，color 缺省取色板 |
| `donut` | `false` | 环图模式 |
| `inner` | `0.62` | 环图内径比（0~1） |
| `size` | `200` | 画布边长 |
| `center` | 总计 | 环图中心文案（覆盖默认） |
| `centerSub` | `"总计"` | 中心副文案 |
| `unit` | `""` | 默认中心文案单位 |
| `onHover` | — | 悬停扇区回调 `({name, value, index} \| null)` |
| `startAngle` | `-90°` | 起始角（12 点起） |

### RadarChart 雷达图

levels 层同心多边形网格 + 轴线 + 多序列半透明数据多边形。轴标签按象限
自动对齐（右半区左对齐、左半区右对齐），不压图。

```jsx
<RadarChart size={230}
  axes={["订单", "履约", "库存", "售后", "营销", "风控"]}
  series={() => radarData()}    // [{name, color?, values: [0~max]}]
/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `axes` | `[]` | 轴名称数组（3~8 条） |
| `series` | `[]` | 各轴取值 0~max |
| `size` | `220` | 画布边长 |
| `max` | `100` | 轴最大值 |
| `levels` | `4` | 网格层数 |
| `legend` | `true` | 图例 |

### RankingList 排行榜

前三名金银铜徽章 + 名称截断 + 数值条（每行独立缓动）+ 右对齐数值。
全 canvas 自画 —— 条宽连续插值 + 避让文本，flex 做不到这么轻。

```jsx
<RankingList width="100%" rows={() => rankRows()} rowHeight={38}/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `rows` | `[]` | `[{name, value}]`（`{label}` 兼容） |
| `width` | `320` | 画布宽，**传 `"100%"` 时内部按 `ctx.width` 布局** |
| `rowHeight` | `30` | 行高 |
| `max` | rows 最大值 | 条满格值 |
| `showBar` | `true` | 数值条 |
| `nameWidth` | `110` | 名称列宽（超出截断） |
| `color` | 强调色 | 条色（前三名用奖牌色） |
| `valueFmt` | `fmtInt` | 数值格式化 |

### ScrollTable 轮播表格

大屏的表格不是给人翻页的，是"自己动"的：行带从下往上连续滚，到底循环。
canvas 连续位移，没有 flex + scrollTop 回顶时的硬跳。

```jsx
<ScrollTable
  width="100%" height={104} rowHeight={26}
  columns={[
    { key: "id", label: "订单号", width: 1.2 },
    { key: "amt", label: "金额 (元)", width: 1, align: "right" },
  ]}
  rows={() => tableRows()}
/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `columns` | `[]` | `[{key, label, width?, align?}]`，width 是权重 |
| `rows` | `[]` | 数据行 |
| `height` | `200` | 可视高 |
| `rowHeight` | `30` | 行高 |
| `header` | `true` | 表头 |
| `speed` | `30` | 滚动速度 px/s |
| `zebra` | `true` | 斑马纹 |
| `interval` | `0` | 每行停顿 ms（0 = 连续滚） |

### ClockPanel 时钟面板

HH:MM:SS（冒号每秒半亮心跳）+ 日期 + 星期。运行时没有 `Date`，时间全部走
`Temporal.Now.zonedDateTimeISO()` —— 本项目时钟类组件的唯一正解。
setTimeout 对齐整秒后再进 setInterval，避免随启动相位漂移。

```jsx
<ClockPanel size={26}/>
```

| prop | 缺省 | 说明 |
|---|---|---|
| `size` | `30` | 主字号 |
| `color` / `accent` | 主题色 | 主色 / 冒号装饰色 |
| `showDate` / `showWeek` | `true` | 日期行 / 星期 |
| `width` | `190` | 画布宽 |

## 多屏适配

全部尺寸按**设计稿**（如 1920×1080）声明；上真屏（LED / 投影 / 不同分辨率）
时按目标分辨率开窗即可，组件内部坐标随画布走，不需要改代码：

```jsx
<window title="大屏" width={1920} height={1080}>…</window>
```

三条适配纪律：

1. **容器用百分比 + flexGrow，图表用固定高**：`width="100%"` 让宽度跟随
   面板，`height` 给死保证绘图区比例不变。面板与面板之间用 `gap` 呼吸。
2. **不要按屏幕尺寸写死坐标**：canvas 的 `width/height` 接受 `"100%"`，
   组件内部一律以 `ctx.width` / `ctx.height` 为布局基准（内核解析后的像素值）。
   在 JS 侧对可能是 `"100%"` 的 prop 做算术会得 NaN —— 数值画在 NaN 坐标
   静默消失，这是本库踩过的坑（RankingList 的数值条曾经这么丢的）。
3. **字号按观看距离定**：大屏正文不小于 12，主数字 28 起（见
   `theme.fontSizes` 阶梯）。

## 运行时坑位记录（实测）

这套库是拿 Gox 运行时"当船划"划出来的，以下坑全部实测复现过，写组件前先读：

| # | 坑 | 绕法 |
|---|---|---|
| 1 | **组件 children 是变参**：`<Comp>kids</Comp>` 降级成 `Comp(props, ...kids)`，不是 `props.children` | 组件签名写 `(props, ...children)`；库内嵌套直接调组件函数，`h()` 只收字符串标签 |
| 2 | **`for...of` 按 UTF-8 字节迭代字符串**（每项 `length` 恒 1） | 逐字符一律走索引 + `charAt` / `charCodeAt`（theme.js 的 textWidth 就是这么写的） |
| 3 | **`s[i]` 是字节语义**，而 `charAt` / `slice` / `length` 是码元语义 | 字符串索引统一用 `charAt(i)` |
| 4 | **TDZ 误判**：定时器 / rAF 回调闭包在**内层块**里引用**外层函数体变量**，报 `Cannot access lexical declaration before initialization` | loop 与它引用的变量都放在函数体同一层，块里只留注册调用（见 table.js / border.js） |
| 5 | **没有 `Date` / `Intl`** | 时间走 `Temporal.Now.zonedDateTimeISO()`；千分位自己拼（theme.js `fmtInt`） |
| 6 | **canvas 的 `width/height` 可以是 `"100%"` 字符串** | 布局计算用 `ctx.width` / `ctx.height`，别对 prop 做算术 |
| 7 | **`padding` 不支持数组** | 单一基准值 + `paddingTop/Right/Bottom/Left` 覆盖 |
| 8 | **canvas hit-test 是整块矩形** | 扇区级 / 图元级命中自己在 `onMouseMove` 里算（见 pie.js 的极坐标判定） |
| 9 | **`createSignal` 返回 `[getter, setter]` 二元组**，二元组本身不是函数 | 拆开存：`const [get, set] = createSignal(0)` |
| 10 | **effect 里读动画信号自己 = 死循环** | 副作用 effect 只依赖目标表达式，当前值走闭包变量镜像（motion.js） |

## 本地验证

组件库的回归跑在 Gox 主仓里（本仓只放可发布的源码）：

```bash
# 纯逻辑测试（主题 / 绘制工具 / 格式化，无 GUI）
./gox testdata/datav_logic_test.js

# 离屏渲染全家桶（19 个画廊脚本，含本大屏；无头 Linux 可跑）
GOX_SHOTS_OUT=/tmp/shots go test ./gfx/ -run TestGalleryShotScripts
```

发布前在本仓跑一遍同步闸门：

```bash
python3 scripts/check-sync.py
```
