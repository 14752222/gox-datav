# 上线清单

`gx-datav` 已上线。本文记录**现状**、**还差你做的事**，以及首轮上线时
实测踩到的坑（都是文档里查不到、撞上才知道的）。

## 现状

| 环节 | 状态 | 备注 |
|---|---|---|
| GitHub 仓库 | ✅ 已建 | https://github.com/14752222/gox-datav（默认分支 `master`） |
| 代码推送 | ✅ 已推 | 3 个提交，96 个文件 |
| 展示站 | ✅ 已部署 | https://14752222.github.io/gox-datav/ |
| npm 包 | ✅ 0.1.0 已发布 | https://www.npmjs.com/package/gx-datav（发布者 `goxjs`） |
| registry 真装验证 | ✅ 已过 | `gox install gx-datav` → 29 组件全部可 import，渲染无异常 |
| CI | ✅ 绿 | 站点自检 + 同步闸门（35 文件一致）+ 真渲染冒烟 |
| Trusted Publisher | ⬜ 待配 | 见下，配好之后发版全自动 |

## 还差你做的两件事

### 1. 配 npm Trusted Publisher（一次性的）

npmjs.com → 包 **Settings → Publishing access → Add trusted publisher**，
四个字段必须**逐字符相等**（失配的症状是**误导性的 404**，不是 403）：

| 字段 | 值 |
|---|---|
| Organization or user | `14752222` |
| Repository | `gox-datav` |
| Workflow filename | `release.yml` |
| Environment name | （留空） |

配好之后发版流程：改 `package.json` 的 `version` → 推 `master` → 打标签
`v0.1.1` 推上去（或建 Release），`release.yml` 走 OIDC 自动发布并附
provenance，**不需要任何 token**。

> ⚠️ 别在 workflow 里加 `NODE_AUTH_TOKEN` / `registry-url` ——
> `.npmrc` 里的 token 会压过 OIDC 自动检测，最后仍然是那个 404。

建议配完打一个 `v0.1.1` 试一次，确认 OIDC 链路通了再正式用。

### 2. revoke 所有临时 token

- npm：`gox-all`（bypass_2fa=false，已无用）、`ai1`（只用于首次发布）
  → https://www.npmjs.com/settings/goxjs/tokens
- GitHub：两个 fine-grained PAT → https://github.com/settings/personal-access-tokens

OIDC 生效后这两边的 token 都不再需要。

## 首轮实测踩到的坑

都撞过一遍，记下来免得下次重新踩。

### npm：token 必须是 Automation 类型

不是权限问题，是 token 类型。第一个 token 权限是 `package:write`，
照样被 2FA 拦下：

```
npm error code EOTP
npm error This operation requires a one-time password.
```

查 token 元数据才看出区别（`bypass_2fa`）：

```bash
curl -sH "Authorization: Bearer $TOKEN" https://registry.npmjs.org/-/npm/v1/tokens
# { "name": "gox-all", "permissions": [...], "bypass_2fa": false }   ← 被拦
# { "name": "ai1",     "permissions": [...], "bypass_2fa": true  }   ← 通过
```

**Automation 类型 = `bypass_2fa: true`**，这是它存在的唯一理由。
账号开了 2FA 时，Publish 类型的 token 会在发布那一步要 OTP，无人值守环境填不了。

### npm：新包有 staged publishing

首次发布完 `npm publish` 回显 `+ gx-datav@0.1.0` 看着成功了，但 registry
上立刻查是个占位版本：

```json
{ "dist-tags": { "latest": "0.0.0-stage" },
  "description": "Temporary package placeholder for staged publishing" }
```

**约 2 分钟后**审核通过，`0.1.0` 才成为 `latest`。这期间装包会拿到空壳。
判断依据：轮询 `dist-tags.latest` 是否变成真版本号，别只看 publish 的回显。

### npm：发布要显式指定官方源

沙箱默认 `registry=https://mirrors.tencent.com/npm/`（只读镜像），直接
`npm publish` 发不出去。发布时加 `--registry=https://registry.npmjs.org`。

### GitHub：fine-grained token 要勾两项

`Contents: Read and write` + `Workflows: Read and write`。只有建仓权限的话，
症状是认证通过但推送 403：

```
remote: Permission to 14752222/Gox.git denied to 14752222.   ← 认证过了，权限不够
```

缺 Workflows 权限时，推 `.github/workflows/*.yml` 会被单独拒绝。

### GitHub：git 协议可能超时，退路是 Git Data API

沙箱到 `github.com:443` 会间歇性超时，但 `api.github.com` 通常可达。
单文件改动可以走 blob → tree → commit → PATCH ref 四步；元数据（作者、
邮箱、时间）照抄的话，重建出的 commit sha 与本地**完全一致**。

### CI：`go build` 路径写错 = 冒烟静默跳过

```yaml
( cd .gox-build && go build -o gox . )        # 错：根目录没有 .go 文件
( cd .gox-build && go build -o gox ./cmd/gox ) # 对
```

写错的后果比报错严重：构建步骤挂了 `continue-on-error` 不红 → 冒烟被
`if: steps.gox.outputs.ok == '1'` 门控于是不跑 → **CI 全绿但从没真跑过**。
现在两种失败都打 `::error::`，在 Actions 界面能看见红标。

## 发布前的本地检查（每次都跑）

```bash
python3 scripts/check-sync.py      # 与主仓 testdata/datav/ 一致（35 文件）
python3 scripts/gen-site-data.py   # 重新生成站点数据
python3 scripts/check-site.py      # 站点完整性
xvfb-run -a ./scripts/smoke.sh     # 装进临时工程真跑一遍
```

## registry 真装验证（已过，留档）

```bash
mkdir /tmp/t && cd /tmp/t
gox install gx-datav          # 装到 0.1.0，38 个文件
```

`app.js` 里 `import { components } from "gx-datav"` 后渲染，实测输出：

```
REGISTRY SMOKE OK —— 29 个组件从 npm 装下来后全部可 import，窗口渲染无异常
```

这条路径和 `smoke.sh` 不重复：后者是拷贝发布内容进 `node_modules`（绕过
registry），前者走真实下载。包结构对不对靠前者，registry 元数据对不对
靠后者 —— 两个都过才算完。
