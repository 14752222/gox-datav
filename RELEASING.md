# 上线清单

本仓（`gx-datav`）已经建好、提交在本地 `main`，但**还没推到 GitHub** ——
当前沙箱里的 GitHub 凭据已失效（HTTPS 要用户名、SSH 无 key），我代推不了。
所有权相关的动作也需要你来做。

下面是从零到线上的完整步骤，按顺序做一遍即可。

## 1. 建仓并推送

```bash
cd /path/to/gox-datav
git remote add origin git@github.com:14752222/gox-datav.git   # 或 https://...
git push -u origin main
```

## 2. 打开 Pages

仓库 → **Settings → Pages → Build and deployment → Source** 选
**GitHub Actions**（不选这个，`pages.yml` 会一直失败）。

推完 `main` 后 `pages.yml` 会自动跑，站点上线在
**https://14752222.github.io/gox-datav/**

> 顺手确认一下 README 顶部与 `package.json` 里写的 `homepage` 是这个地址，
> 对不上就改掉 —— 文档里的链接是给用户点的，错了就是死链。

## 3. 发布到 npm

**第一次必须手动发**：npm 的 Trusted Publishing 配置项要挂在**已存在的包**
上，包还不存在时没法配。

```bash
cd /path/to/gox-datav
npm login                # 用 14752222 这个账号
npm publish --access public
```

发完去 npmjs.com 上该包的 **Settings → Trusted Publisher** 填四个字段，
必须逐字符相等（失配的症状是**误导性的 404**，不是 403）：

| 字段 | 值 |
|---|---|
| Organization or user | `14752222` |
| Repository | `gox-datav` |
| Workflow filename | `release.yml` |
| Environment name | （留空） |

配好之后，后续发版全自动：改 `package.json` 的 `version` → 推 `main` →
打标签 `v0.1.1` 推上去（或建 Release），`release.yml` 会判重后发布，
并附 npm provenance 证明。

> ⚠️ 别在 workflow 里加 `NODE_AUTH_TOKEN` / `registry-url` ——
> `.npmrc` 里的 token 会压过 OIDC 自动检测，最后仍然是那个 404。

## 4. 发布前的本地检查（建议每次都跑）

```bash
python3 scripts/check-sync.py      # 与主仓 testdata/datav/ 一致
python3 scripts/gen-site-data.py   # 重新生成站点数据
python3 scripts/check-site.py      # 站点完整性
xvfb-run -a ./scripts/smoke.sh     # 装进临时工程真跑一遍（有显示服务器可去掉 xvfb-run）
```

## 5. 还差一件事：纯 JS 包在 Gox 里的 import 验证

`smoke.sh` 用的是本地 `gox` 二进制 + 本地 `node_modules` 布局，证明了包的
**结构**没问题。但还有一条真实的用户路径没走通：**从 registry 真的
`gox install gx-datav` 装下来能不能 import**。

这条我没法在沙箱里验证（要发到 registry 之后才能测，而发布需要你的凭据）。
发布第一版后，请在本地验一下：

```bash
mkdir /tmp/t && cd /tmp/t
npm init -y
npm i -g @goxjs/goxjs         # 若尚未安装 Gox 运行时
gox install gx-datav
cat > app.js <<'EOF'
import { BorderBox, TitleBar, RingProgress, palette } from "gx-datav";
console.log("组件库已加载，palette.bg =", palette.bg);
EOF
gox app.js
```

预期输出 `组件库已加载，palette.bg = #070d1f`。

如果这里报"找不到模块 `gx-datav`"，多半是 `exports` 条件与 Gox 解析器
不匹配（Gox 只认 `import` / `default` 两个条件，不认 `require` /
`browser` / `node` / `types`），回来核对 `package.json` 的 `exports`。
