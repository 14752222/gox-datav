# scripts/

本仓的校验与生成脚本。没有构建步骤（站点是零构建静态站），但有几条**必须
能重复执行**的流程，脚本化是为了让它们不靠记忆。

## 闸门（改动后跑，CI 也跑同一批）

| 脚本 | 管什么 | 什么时候必须跑 |
|---|---|---|
| `check-sync.py` | 本仓 `src/` 与 Gox 主仓 `testdata/datav/` 逐字节一致 | 改了任何组件源码 —— 两份源码漂移是本仓最大的结构性风险（理由见 README「源码真源与同步」） |
| `check-site.py` | 站点数据的完整性：29 个组件、props 非空、**截图文件真实存在且路径可被浏览器解析** | 改了 `docs/components.json` 或挪动截图 |
| `gen-site-data.py` | 从组件源码注释生成 `docs/components.json` | 组件源码的注释改了（props 表变了） |
| `smoke.sh` | 把包当已安装依赖装进临时工程，用 Gox 真 `import` 并渲染 | 发布前必跑；改过 `package.json` / `exports` / 目录结构后必跑 |

```bash
python3 scripts/check-sync.py
python3 scripts/check-site.py
python3 scripts/gen-site-data.py
xvfb-run -a ./scripts/smoke.sh        # 无头环境；有显示服务器直接 ./scripts/smoke.sh
```

`check-sync.py` 与 `smoke.sh` 需要能找到 Gox 主仓：默认取与本仓平级的
`../Gox`，或用 `GOX_CORE=` / `GOX=` 指定。

## 组件截图怎么来的（重新生成）

`docs/shots/` 下的 29 张单组件图 + 3 张大屏总览图**不在本仓生成** ——
截图要真跑 Gox 的软件光栅化渲染，而本仓没有 Gox 运行时，部署机也没有
（`gfx` 依赖系统字体与 GUI 栈）。所以它们是**资产**：在 Gox 主仓那边离线
生成后提交进来。

重新生成（在主仓 `Gox/` 下执行）：

```bash
# 1) 单组件图：29 个脚本在 testdata/shots/datav-c-*.js
GOX_SHOTS_OUT=/tmp/shots-comp go test ./gfx/ -run 'TestGalleryShotScripts/datav-c-.*'

# 2) 大屏总览图
GOX_SHOTS_OUT=/tmp/shots go test ./gfx/ -run 'TestGalleryShotScripts/datav-(dashboard|more|widgets)'

# 3) 拷进本仓
cp /tmp/shots-comp/linux/datav-c-*.png  <本仓>/docs/shots/
cp /tmp/shots/linux/datav-dashboard.png <本仓>/docs/shots/full/dashboard.png
cp /tmp/shots/linux/datav-more.png      <本仓>/docs/shots/full/more-charts.png
cp /tmp/shots/linux/datav-widgets.png   <本仓>/docs/shots/full/more-widgets.png
```

单组件脚本由 `gen_comp_shots.py` 批量生成（在主仓的 WorkBuddy 工作目录里，
不在两个仓库内）—— 它的设计取舍写在脚本头部：**一律静态值 + 确定性种子**，
因为截图要对动画组件取首帧，而滚动类组件首帧可能是空白的（MarqueeText 就
踩过：`phase` 从 0 起，文本正好在视口外，画面上只剩左边那枚菱形标记）。
新加组件时照那个模式补一个脚本，别手写。

> 重新生成后**务必目检**。画廊测试的判据是"整帧不空白"，
> 单块面板画成空盒子它抓不到 —— 2026-10-15 就是这么漏掉 5 处静默失效的
> （详见主仓 `gfx/gallery_shot_test.go` 里 `galleryAssertCanvasesLaidOut` 的注释）。
> 本仓的 `check-site.py` 只能证明"文件在"，证明不了"图里有东西"。
