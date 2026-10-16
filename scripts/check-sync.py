#!/usr/bin/env python3
"""源码双份同步闸门。

gx-datav 的组件源码刻意存在两份（理由见 README「源码真源与同步」）：
本仓 src/ 是 npm 包的发布真源，Gox 主仓 testdata/datav/ 是画廊截图测试
的运行时依赖。两份靠自觉必然漂移 —— 这个脚本就是那个不靠自觉的闸门：
逐字节比对，不一致即非零退出。

用法:
    python3 scripts/check-sync.py
    GOX_CORE=/path/to/Gox python3 scripts/check-sync.py

退出码:
    0  两份一致
    1  发现不一致（已列出文件）
    2  找不到 Gox 主仓（CI 里需要先 checkout）
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)

# 主仓位置：优先环境变量，其次与本仓平级的 ../Gox
CORE = os.environ.get("GOX_CORE") or os.path.join(os.path.dirname(PKG), "Gox")
CORE_DATAV = os.path.join(CORE, "testdata", "datav")

# 主仓里的完整大屏 demo：在本仓落到 examples/，且相对导入要改写成 ../src/。
# 其余 .js 一律与本仓 src/ 同名对应。
EXAMPLES = ("dashboard.js", "more-charts.js", "more-widgets.js")

# examples/ 从 src/ 平级挪走后，入口的相对路径必然不同 —— 比对前归一化，
# 否则这三行差异会永久报警、把真正的漂移淹没在噪音里。
EXAMPLES_REWRITE = [('../src/index.js', './index.js')]


def norm(text):
    for a, b in EXAMPLES_REWRITE:
        text = text.replace(a, b)
    return text


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def main():
    if not os.path.isdir(CORE_DATAV):
        print(f"找不到 Gox 主仓的 {CORE_DATAV}", file=sys.stderr)
        print("CI 里请先 checkout 主仓，或用 GOX_CORE= 指定路径。", file=sys.stderr)
        return 2

    drift = []
    checked = 0

    core_files = sorted(f for f in os.listdir(CORE_DATAV) if f.endswith(".js"))
    for name in core_files:
        core_path = os.path.join(CORE_DATAV, name)
        if name in EXAMPLES:
            mine = os.path.join(PKG, "examples", name)
            label = f"examples/{name}"
            want = norm(read(core_path))
            got = norm(read(mine)) if os.path.isfile(mine) else None
        else:
            mine = os.path.join(PKG, "src", name)
            label = f"src/{name}"
            want = read(core_path)
            got = read(mine) if os.path.isfile(mine) else None

        if got is None:
            drift.append(f"{label}: 本仓缺失（主仓有）")
            continue
        checked += 1
        if got != want:
            drift.append(f"{label}: 内容与主仓不一致")

    # 反向查：本仓有而主仓没有的文件（多半是改名后忘了同步）
    for name in sorted(os.listdir(os.path.join(PKG, "src"))):
        if not name.endswith(".js"):
            continue
        if name not in core_files:
            drift.append(f"src/{name}: 主仓已无此文件（改名还是漏同步？）")

    print(f"比对 {checked} 个文件（主仓 {CORE_DATAV} ↔ 本仓 src/ + examples/）")
    if drift:
        print(f"\n发现 {len(drift)} 处漂移：")
        for d in drift:
            print(f"  ✗ {d}")
        print("\n修法：确认哪边是对的，把对的拷到另一边。主仓那边改完记得跑")
        print("  go test ./gfx/ -run TestGalleryShotScripts")
        return 1

    print("一致 ✓")
    return 0


if __name__ == "__main__":
    sys.exit(main())
