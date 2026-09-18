=== DIAGNOSTIC ===
Time: Fri Sep 18 09:32:19 AM CST 2026
=== USER ===
root
=== GIT LOG ===
fatal: detected dubious ownership in repository at '/opt/aishield'
To add an exception for this directory, call:

	git config --global --add safe.directory /opt/aishield
NO GIT REPO
=== SCRIPT CHECK ===
#!/bin/bash
# AIShield Named Tunnel 部署脚本
# 使用 cert.pem (cloudflared tunnel login) 创建持久化 Named Tunnel
# 解决 Quick Tunnel 的 error 1014 (CNAME Cross-User Banned) 问题
#
=== API STATUS ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 238, "rules_breakdown": {"static": 210, "generated": 9, "radar": 19, "total": 238}, "uptime": 1789695139.8046176, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "4d5bbd980b8906a059ddaf8adcf88f71cf13ca5a", "deployed_at": "2026-09-18T01:31:41Z"}OK
=== CLOUDFLARED PROCESS ===
root     1335051  0.1  1.4 1294676 28728 ?       Sl   09:14   0:01 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1335162  0.1  1.4 1294676 28296 ?       Ssl  09:14   0:01 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     1347065  1.1  1.8 1294420 38004 ?       Sl   09:32   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-18T01:32:03Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.192.167
2026-09-18T01:32:03Z INF Registered tunnel connection connIndex=0 connection=327121cb-b64a-439b-a595-0564ffe63452 event=0 ip=198.41.192.167 location=lax09 protocol=quic
2026-09-18T01:32:03Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.73
2026-09-18T01:32:04Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.200.33
2026-09-18T01:32:05Z INF Registered tunnel connection connIndex=2 connection=27929774-7cc8-44d6-ac46-ff833c2fc9bc event=0 ip=198.41.200.33 location=lax01 protocol=quic
2026-09-18T01:32:05Z INF Initiating graceful shutdown due to signal terminated ...
2026-09-18T01:32:05Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.192.57
2026-09-18T01:32:06Z ERR failed to run the datagram handler error="Application error 0x0 (remote)" connIndex=2 event=0 ip=198.41.200.33
2026-09-18T01:32:06Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=2 event=0 ip=198.41.200.33
2026-09-18T01:32:06Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=2 event=0 ip=198.41.200.33
2026-09-18T01:32:06Z INF Retrying connection in up to 1s connIndex=2 event=0 ip=198.41.200.33
2026-09-18T01:32:06Z ERR failed to run the datagram handler error="context canceled" connIndex=0 event=0 ip=198.41.192.167
2026-09-18T01:32:06Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=0 event=0 ip=198.41.192.167
2026-09-18T01:32:06Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=0 event=0 ip=198.41.192.167
2026-09-18T01:32:06Z INF Retrying connection in up to 1s connIndex=0 event=0 ip=198.41.192.167
2026-09-18T01:32:06Z INF Registered tunnel connection connIndex=3 connection=0e1021e5-3154-4022-a300-195a77039ed6 event=0 ip=198.41.192.57 location=lax05 protocol=quic
2026-09-18T01:32:06Z ERR Connection terminated connIndex=2
2026-09-18T01:32:06Z ERR Connection terminated connIndex=0
2026-09-18T01:32:07Z ERR failed to run the datagram handler error="context canceled" connIndex=3 event=0 ip=198.41.192.57
2026-09-18T01:32:07Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=3 event=0 ip=198.41.192.57
2026-09-18T01:32:07Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=3 event=0 ip=198.41.192.57
2026-09-18T01:32:07Z INF Retrying connection in up to 1s connIndex=3 event=0 ip=198.41.192.57
2026-09-18T01:32:07Z ERR Connection terminated connIndex=3
2026-09-18T01:32:08Z ERR Failed to dial a quic connection error="failed to dial to edge with quic: timeout: no recent network activity" connIndex=1 event=0 ip=198.41.200.73
2026-09-18T01:32:08Z INF Retrying connection in up to 2s connIndex=1 event=0 ip=198.41.200.73
2026-09-18T01:32:08Z ERR Connection terminated connIndex=1
2026-09-18T01:32:08Z ERR no more connections active and exiting
2026-09-18T01:32:08Z INF Tunnel server stopped
2026-09-18T01:32:08Z INF Metrics server stopped
2026-09-18T01:32:08Z ERR icmp router terminated error="context canceled"
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[09:31:41] Time: Fri Sep 18 09:31:41 AM CST 2026
[09:31:41] User: root (UID: 0)
[09:31:41] === STEP 1: 启动 API (端口 8450) ===
[09:31:41] 代码由 runner tarball 投递，权威 sha=4d5bbd98
[09:31:41] commit 对比: 运行进程=none / 磁盘=4d5bbd980b8906a059ddaf8adcf88f71cf13ca5a
[09:31:41] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[09:31:41] 需要重新加载代码 -> 重启 API
[09:31:42] systemd 服务 aishield-api 已安装（Restart=always，WorkingDirectory=/opt/aishield）
[09:31:48] API 状态: OK（第 1 轮验证通过）
[09:31:48] === STEP 2: 安装 cloudflared ===
[09:31:48] cloudflared 安装路径: /usr/local/bin/cloudflared
[09:31:48] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[09:31:49] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[09:31:49] === STEP 3: 检查认证方式 ===
[09:31:49] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[09:31:49] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[09:31:49] 检查现有 tunnel...
[09:31:51] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS                                 
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax07, 1xlax08, 1xlax10, 1xlax12 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                                             
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                                             
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 1xlax09, 1xlax11                   
[09:31:51] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[09:31:51] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[09:31:51] 凭证文件存在
[09:31:51] 创建 config.yml...
[09:31:51] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[09:31:51] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[09:31:53] DNS 路由结果: 2026-09-18T01:31:53Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[09:31:53] === STEP 5: 更新 DNS (API) ===
[09:31:53] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[09:31:55] 创建新 DNS CNAME 记录...
DNS 创建失败: [{"code": 9106, "message": "Missing X-Auth-Key, X-Auth-Email or Authorization headers"}]
[09:31:57] 设置 SSL 模式为 Full...
SSL: 跳过
[09:31:59] === STEP 6: 启动 Tunnel ===
[09:31:59] systemd 托管中 -> systemctl stop cloudflared-tunnel
[09:32:03] 启动 Named Tunnel (cert 模式)...
[09:32:03] 使用 config: /root/.cloudflared/config.yml
[09:32:03] cloudflared PID: 1346953
[09:32:05] Tunnel 连接已建立!
[09:32:05] --- cloudflared 日志 (最后 15 行) ---
2026-09-18T01:32:03Z INF Version 2026.7.3 (Checksum 9d71c677db00134c1bd4144b7783486b654ad281b1ea62b4972098d19f770f17)
2026-09-18T01:32:03Z INF GOOS: linux, GOVersion: go1.26.4, GoArch: amd64
2026-09-18T01:32:03Z INF Settings: map[config:/root/.cloudflared/config.yml cred-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json credentials-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json]
2026-09-18T01:32:03Z INF cloudflared will not automatically update if installed by a package manager.
2026-09-18T01:32:03Z INF Generated Connector ID: 22a46a4b-2662-4822-b0da-c749bdc54243
2026-09-18T01:32:03Z INF Initial protocol quic
2026-09-18T01:32:03Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-18T01:32:03Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-18T01:32:03Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-18T01:32:03Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-18T01:32:03Z INF Starting metrics server on 127.0.0.1:20242/metrics
2026-09-18T01:32:03Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.192.167
2026-09-18T01:32:03Z INF Registered tunnel connection connIndex=0 connection=327121cb-b64a-439b-a595-0564ffe63452 event=0 ip=198.41.192.167 location=lax09 protocol=quic
2026-09-18T01:32:03Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.73
2026-09-18T01:32:04Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.200.33
[09:32:05] === STEP 7: 持久化 ===
[09:32:05] 停止 nohup cloudflared (PID 1346953) -> 交由 systemd 单实例托管
[09:32:07] systemd 服务已配置
[09:32:07] Cron 保活已设置（以本项目 API 健康为判据，不被他项目 tunnel 假满足）
[09:32:07] === STEP 8: 验证 ===
[09:32:07] --- API (localhost:8450) ---
 OK
[09:32:07] --- cloudflared 进程 ---
root     1335051  0.1  1.5 1294676 30872 ?       Sl   09:14   0:01 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1335162  0.1  1.5 1294676 30944 ?       Ssl  09:14   0:01 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     1346953 27.2  1.9 1294676 39852 ?       Rl   09:32   0:01 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[09:32:07] --- aishield.tools ---
 OK
[09:32:10] --- DNS CNAME ---
[09:32:10] --- DNS A ---
172.67.188.44
104.21.81.46
[09:32:10] === 部署汇总 ===
[09:32:10] Tunnel Mode: cert
[09:32:10] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[09:32:10] API: http://localhost:8450
[09:32:10] 域名: https://aishield.tools
[09:32:10] cloudflared: /usr/local/bin/cloudflared
[09:32:10] PID: 1346953
[09:32:10] Config: /root/.cloudflared/config.yml
[09:32:10] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[09:32:10] 状态: Named Tunnel (cert 模式) 已配置
[09:32:10] EXIT 0: API 健康
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Fri 2026-09-18 09:32:07 CST; 11s ago
   Main PID: 1347055 (start-tunnel.sh)
      Tasks: 9 (limit: 2216)
     Memory: 20.5M
        CPU: 158ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─1347055 /bin/bash /opt/start-tunnel.sh
             └─1347065 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
LISTEN 0      5            0.0.0.0:8450       0.0.0.0:*    users:(("python3",pid=1346574,fd=3))                                                    
=== CRONTAB ===
*/5 * * * * flock -xn /tmp/stargate.lock -c '/usr/local/qcloud/stargate/admin/start.sh > /dev/null 2>&1 &'
* * * * * curl -sf --max-time 6 http://127.0.0.1:8450/api/v1/health >/dev/null 2>&1 || /opt/start-tunnel.sh >> /tmp/cloudflared.log 2>&1
=== START SCRIPT ===
#!/bin/bash
# AIShield Tunnel 启动脚本
CF_BIN='/usr/local/bin/cloudflared'
CONFIG_FILE='/root/.cloudflared/config.yml'
TOKEN_FILE='/root/.cloudflared/tunnel-token'

cleanup() { kill $CF_PID 2>/dev/null; exit 0; }
trap cleanup SIGTERM SIGINT

# 【2026-09-18】隧道起来不等于 API 在监听。Cloudflare 转发到 localhost:8450，
# 若该端口无进程，域名只会稳定返回 502（09-17~09-18 线上连续失活即此路径：
# cloudflared 存活、API 未监听）。开机/重启后先确保 API 就绪再放行隧道。
if ! curl -sf --max-time 5 http://127.0.0.1:8450/api/v1/health >/dev/null 2>&1; then
    if systemctl is-active aishield-api >/dev/null 2>&1; then
        systemctl restart aishield-api 2>/dev/null || true
    elif systemctl is-enabled aishield-api >/dev/null 2>&1; then
        systemctl start aishield-api 2>/dev/null || true
    elif [ -f /opt/aishield/api/server.py ]; then
        # 【2026-09-18】与 install_api_service / api_start_nohup 一致：
        # systemd 以 root 运行，assert_not_root() 会拒绝启动（线上 502 的根因）。
        (cd /opt/aishield && PORT=8450 AISHIELD_ALLOW_ROOT=1 nohup python3 api/server.py >> /tmp/aishield-api.log 2>&1 &)
    elif [ -f "$HOME/aishield/api/server.py" ]; then
        (cd "$HOME/aishield" && PORT=8450 AISHIELD_ALLOW_ROOT=1 nohup python3 api/server.py >> /tmp/aishield-api.log 2>&1 &)
    fi
    for _i in 1 2 3 4 5 6; do
        curl -sf --max-time 5 http://127.0.0.1:8450/api/v1/health >/dev/null 2>&1 && break
        sleep 3
    done
    if ! curl -sf --max-time 5 http://127.0.0.1:8450/api/v1/health >/dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] WARN: API 未就绪，隧道仍会启动（域名将返回 502）" >> /tmp/aishield-api.log
    fi
fi

if [ -f "$CONFIG_FILE" ]; then
    $CF_BIN tunnel --config "$CONFIG_FILE" run &
    CF_PID=$!
elif [ -f "$TOKEN_FILE" ]; then
    TOKEN=$(cat "$TOKEN_FILE")
    $CF_BIN tunnel run --token "$TOKEN" &
    CF_PID=$!
else
    $CF_BIN tunnel --url http://localhost:8450 &
    CF_PID=$!
fi

wait $CF_PID

=== HTTPS Test from Runner ===
Time: Fri Sep 18 01:32:28 UTC 2026

=== curl test (aishield.tools) ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 238, "rules_breakdown": {"static": 210, "generated": 9, "radar": 19, "total": 238}, "uptime": 1789695149.5421078, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "4d5bbd980b8906a059ddaf8adcf88f71cf13ca5a", "deployed_at": "2026-09-18T01:31:41Z"}
=== DNS lookup ===
104.21.81.46
172.67.188.44

=== DNS CNAME check ===
