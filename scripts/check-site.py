#!/usr/bin/env python3
"""站点与数据的完整性自检（CI 与本地都用这一份）。

为什么单独成脚本而不写在 workflow 的 run: 里 —— YAML 里嵌 Python heredoc
可读性差、缩进敏感，改错了只有 CI 跑起来才知道。这里能本地直接跑。

检查项：
  1. components.json 存在且能解析
  2. 组件数是 29（改了组件数量要同步改这里，是刻意的"绊一跤"）
  3. 每个组件都有 props（解析失败会退化成空，站点上就是一张没有字段说明的卡片）
  4. 每个组件引用的截图文件真实存在（**这条最容易漏**：2026-10-16 站点
     上线时 29 张图的路径写成了仓库相对路径，浏览器全 404，而打包全程绿灯）
  5. 站点三个核心文件在位

用法:
    python3 scripts/check-site.py
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
DOCS = os.path.join(PKG, "docs")
EXPECTED = 29


def main():
    data_path = os.path.join(DOCS, "components.json")
    if not os.path.isfile(data_path):
        print("缺 docs/components.json —— 先跑 python3 scripts/gen-site-data.py", file=sys.stderr)
        return 1

    data = json.load(open(data_path, encoding="utf-8"))
    comps = data["components"]
    errs = []

    if len(comps) != EXPECTED:
        errs.append("组件数 %d != %d" % (len(comps), EXPECTED))

    for c in comps:
        if not c.get("props"):
            errs.append("%s: 没解析到 props" % c["name"])
        shot = os.path.join(DOCS, c["shot"])
        if not os.path.isfile(shot):
            errs.append("%s: 截图不存在 %s" % (c["name"], c["shot"]))
        # 路径必须以 "shots/" 开头（相对页面），不是 "docs/shots/"（相对仓库根）
        if c["shot"].startswith("docs/"):
            errs.append("%s: 截图路径是仓库相对（%s），浏览器会 404" % (c["name"], c["shot"]))

    for f in ("index.html", "assets/style.css", "assets/app.js"):
        if not os.path.isfile(os.path.join(DOCS, f)):
            errs.append("缺站点文件 docs/%s" % f)

    if errs:
        print("站点自检失败：", file=sys.stderr)
        for e in errs:
            print("  ✗ " + e, file=sys.stderr)
        return 1

    print("站点自检 OK：%d 个组件，props 与截图齐全，站点文件在位" % len(comps))
    return 0


if __name__ == "__main__":
    sys.exit(main())
