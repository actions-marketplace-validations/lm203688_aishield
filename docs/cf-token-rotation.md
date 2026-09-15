# CF API Token 轮换（一次性操作）

> 目标：把过去硬编码在 `scripts/deploy-named-tunnel.sh:20` 和
> `scripts/deploy-quick-tunnel.sh:156` 里的 Cloudflare token 换成从 VPS 文件
> 读取，并吊销旧 token。
>
> 预计耗时 5 分钟，需要点开 3 个网页。之后无需再维护。

---

## 为什么这是 P0

该 token 以 base64 形式写在**公开仓库**里。base64 不是加密，任何人 clone 仓库后
一行命令就能拿到。它拥有 `aishield.tools` 的：

| 权限 | 攻击者能做什么 |
|---|---|
| Zone Read | 读取域名与账户拓扑 |
| DNS Records Edit | **把 `aishield.tools` 的 CNAME 改指向攻击者服务器**（域名劫持，用户会访问伪造站点） |
| Zone Settings Edit | 改 SSL 模式等安全设置 |

因此这不是"最佳实践"问题，是**现在就可以被利用**的问题。

---

## 实测到的现状（2026-09-15 17:20）

| 探测项 | 结果 |
|---|---|
| token 有效性 | ✅ 有效（`/user/tokens/verify` 200） |
| 能读 zone / DNS 记录 | ✅ 可以 |
| 拥有 zone：`aishield.tools` | account `8162aa3b2241c132e43a81f526d7f758`（61960005@qq.com） |
| 该账户下的 Named Tunnel 数 | **0** |
| 但 `aishield.tools` 的 CNAME 是 | `0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com`（在线服务正常） |
| CF Pages 权限 | ❌ 403 |

**结论**：真正的 tunnel 不在 `aishield.tools` 所属的那个账户里（可能在
463102527@qq.com 账户下）。这不影响本次轮换 —— deploy 脚本的 API 分支只在
`cert.pem` 缺失时才用到 CF token 去建 tunnel；正常路径走 VPS 上已有的
`/root/.cloudflared/cert.pem` + cloudflared CLI，完全不碰 CF token。
**日常部署只需要 DNS 写权限**，所以下面的最小权限集就够了。

---

## 步骤 1 — 创建新 token（约 2 分钟）

打开 👉 **https://dash.cloudflare.com/profile/api-tokens**

> 确认左上角当前登录的是 **61960005@qq.com** 账户（`aishield.tools` 所属账户）。
> 如果页面顶部显示的是别的账户，点账户名切换。

1. 点右上角 **Create Token**
2. 选 **Create custom token**（不要用 Quick Start 的 Zone. DNS Zone 模板，
   它会多给权限）
3. **Token name**：`aishield-deploy`
4. **Permissions** —— 添加下面 4 条，每条都把右侧下拉设为 **Only aishield.tools**
   （只有第 4 条是 Account 级，不用选 zone）：

   | # | Edit permissions | Resource |
   |---|---|---|
   | 1 | Zone — Zone Read | Only aishield.tools |
   | 2 | Zone — DNS Records | Only aishield.tools |
   | 3 | Zone — Zone Settings | Only aishield.tools |
   | 4 | Account — Cloudflare Tunnel | Edit |

   > 第 4 条是给 deploy 脚本的 API 兜底分支用的（`cert.pem` 丢失时的重建路径）。
   > 不想要隧道权限的话可以省掉，日常部署不会用到。

5. **TTL**：选 **No expiration**（或者你觉得能接受每年再轮换一次也行）
6. 最下面 **Continue to summary** → **Create Token**
7. **复制 token 值** —— 页面关闭后就看不到了，只能重建

---

## 步骤 2 — 存成 GitHub Secret（约 1 分钟）

打开 👉 **https://github.com/lm203688/aishield/settings/secrets/actions**

1. 点 **New repository secret**
2. **Secret** 名称：`CF_TUNNEL_TOKEN`
3. **Secret** 值：粘贴步骤 1 复制的 token
4. **Add secret**

> ⚠️ 名称必须精确是 `CF_TUNNEL_TOKEN`（大写、下划线）。脚本和 workflow 都按这个名字找。

---

## 步骤 3 — 运行安装 workflow（约 1 分钟）

打开 👉 **https://github.com/lm203688/aishield/actions/workflows/install-cf-token.yml**

1. 左侧 **Run workflow** 下拉 → 选 `main`
2. 点绿色 **Run workflow**
3. 刷新页面，展开 job 的 **Write token to VPS (over ssh/scp)** 和
   **Verify token from the VPS itself** 两步

看到这段输出即成功：

```
=== 1. token 自身有效 ===
  success: True  token_id: <前 12 位>
=== 2. 能读目标 zone（deploy 必需）===
  zone: aishield.tools  account: 8162aa3b...  err:
=== 3. 能读 DNS 记录（deploy 必需）===
  success: True  records: 1
```

> 失败排查：
> - 第 1 步报 `success: False` → token 复制不完整（常见：末尾少一段或多了空格），
>   回步骤 1 重建
> - 第 2 步报 `err: Unauthorized to access requested resource` → token 没选对
>   zone，回步骤 1 检查第 1–3 条权限的 Resource 是否都选了 aishield.tools
> - `ssh` 相关报错 → 说明部署通道本身有问题，不是 token 的事

---

## 步骤 4 — 吊销旧 token（约 30 秒，**必须做**）

回到 👉 **https://dash.cloudflare.com/profile/api-tokens**

在 token 列表里找到那个旧的 token（名字可能是 `Zone - DNS Zone` 或你当初起的名字），
点它右边的 **Delete token**。

> 这一步**不会**中断在线服务：`aishield.tools` 的 DNS 记录不会变，
> VPS 上的 cloudflared 进程用的是自己的 tunnel token，跟这个 API token 无关。
> 只是从此刻起，任何还握着旧 token 的人（包括所有 clone 过仓库的人）
> 都无法再改动你的域名。

---

## 完成后的状态

| 项 | 值 |
|---|---|
| 脚本读 token 的方式 | `env $CF_TUNNEL_TOKEN` → `/root/.aishield/cf-token` |
| token 存放位置 | VPS `/root/.aishield/cf-token`（目录 700 / 文件 600） |
| 仓库里的密钥 | **无**（`grep -r` 已确认 0 处） |
| 旧 token | 已吊销 |

---

## 以后如何再换 token

只需重做步骤 1 → 2 → 3，然后步骤 4 删旧的。**不需要改任何代码**。
