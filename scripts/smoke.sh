#!/usr/bin/env bash
# 本地冒烟：把本包当作**已安装的依赖**装进一个临时工程，用 Gox 真跑一遍。
#
# 为什么不能只靠 `npm pack --dry-run`：那只证明"包能打出来"，不证明
# "打出来的包能用"。exports 写错、相对导入路径错、files 白名单漏文件，
# 打包都照样成功，只有在真正的 import 那一刻才炸。这一步是发布前最后的
# 兜底 —— 2026-10-16 实测：站点里 29 张图的路径就是这么发现的（页面 404
# 而打包全程绿灯）。
#
# 用法:
#     GOX=/path/to/gox ./scripts/smoke.sh
#     GOX 环境变量缺省指向 ../Gox/gox（与主仓平级）
#
# 无头环境需 xvfb（真窗口渲染要显示服务器）:
#     xvfb-run -a ./scripts/smoke.sh

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PKG="$(dirname "$HERE")"
GOX="${GOX:-$(dirname "$PKG")/Gox/gox}"

if [ ! -x "$GOX" ]; then
  echo "找不到 gox 可执行文件: $GOX" >&2
  echo "用 GOX=/path/to/gox 指定，或先在主仓 go build -o gox ." >&2
  exit 2
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "① 同步闸门"
GOX_CORE="${GOX_CORE:-$(dirname "$PKG")/Gox}" python3 "$PKG/scripts/check-sync.py"

echo
echo "② 装进临时工程的 node_modules（不经过 registry，直接拷发布内容）"
mkdir -p "$TMP/node_modules/gx-datav"
# 只拷 package.json 的 files 白名单里的东西 —— 与真实安装收到的内容一致
( cd "$PKG" && cp -r src examples README.md LICENSE package.json "$TMP/node_modules/gx-datav/" )

echo
echo "③ 用 Gox 真跑一遍（import \"gx-datav\" → render）"
cat > "$TMP/app.js" <<'EOF'
import { render, createSignal } from "gox";
import {
  BorderBox, TitleBar, LineChart, RingProgress, KpiCard, ScrollTable,
  palette, seriesRandomWalk, components,
} from "gx-datav";

const n = Object.keys(components).length;
if (n !== 29) throw new Error("期望 29 个组件，实际 " + n);
if (typeof palette.bg !== "string") throw new Error("palette 没导出对");

const [vals] = createSignal([78, 92]);
render(
  <window title="smoke" width={640} height={360} hideFocusRing={true}>
    <column width="100%" height="100%" background={palette.bg} padding={12} gap={10}>
      <BorderBox type={1} width="100%" flexGrow={1}>
        <TitleBar title="包装载冒烟" align="left" fontSize={14}/>
        <row flexGrow={1} justifyContent="space-around" alignItems="center">
          <RingProgress value={() => vals()[0]} size={110} label="A" sub="完成率"/>
          <RingProgress value={() => vals()[1]} size={110} color={palette.ok} label="B" sub="及时率"/>
        </row>
      </BorderBox>
      <LineChart width="100%" height={120} series={[{ name: "T", data: seriesRandomWalk(10, 50, 12, 7) }]} yMax={80}/>
    </column>
  </window>
);
console.log("SMOKE OK —— 29 个组件全部可 import，窗口渲染无异常");
EOF
( cd "$TMP" && "$GOX" app.js )

echo
echo "④ 包内容预览（files 白名单之外的东西不该出现）"
( cd "$PKG" && npm pack --dry-run 2>&1 | sed -n '/Tarball Contents/,/Tarball Details/p' | head -5 )
echo "   …（完整列表见 npm pack --dry-run）"

echo
echo "全部通过 ✓"
