=== DIAGNOSTIC ===
Time: Wed Sep 23 09:57:13 AM CST 2026
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
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 235, "rules_breakdown": {"static": 208, "generated": 8, "radar": 19, "total": 235}, "uptime": 1790128633.6527812, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "e746884af6fd9d4f02675a147ddc2e750219aeef", "deployed_at": "2026-09-23T01:56:42Z"}OK
=== CLOUDFLARED PROCESS ===
root     1335051  0.1  1.3 1294932 26960 ?       Sl   Sep18  11:07 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1335162  0.1  1.2 1294932 25812 ?       Ssl  Sep18  11:13 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     1898468  1.2  2.0 1294420 40440 ?       Sl   09:57   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-23T01:57:00Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.200.53
2026-09-23T01:57:00Z INF Registered tunnel connection connIndex=1 connection=01bea30b-b554-43ba-948d-da42e7ffa661 event=0 ip=198.41.192.7 location=lax11 protocol=quic
2026-09-23T01:57:00Z INF Registered tunnel connection connIndex=2 connection=8103e736-757e-4c29-b8ca-4f2da05c2fa2 event=0 ip=198.41.200.53 location=lax01 protocol=quic
2026-09-23T01:57:01Z INF Initiating graceful shutdown due to signal terminated ...
2026-09-23T01:57:01Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.192.67
2026-09-23T01:57:01Z ERR failed to run the datagram handler error="context canceled" connIndex=0 event=0 ip=198.41.200.13
2026-09-23T01:57:01Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=0 event=0 ip=198.41.200.13
2026-09-23T01:57:01Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=0 event=0 ip=198.41.200.13
2026-09-23T01:57:01Z INF Retrying connection in up to 1s connIndex=0 event=0 ip=198.41.200.13
2026-09-23T01:57:01Z ERR failed to run the datagram handler error="context canceled" connIndex=2 event=0 ip=198.41.200.53
2026-09-23T01:57:01Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=2 event=0 ip=198.41.200.53
2026-09-23T01:57:01Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=2 event=0 ip=198.41.200.53
2026-09-23T01:57:01Z INF Retrying connection in up to 1s connIndex=2 event=0 ip=198.41.200.53
2026-09-23T01:57:01Z ERR failed to run the datagram handler error="context canceled" connIndex=1 event=0 ip=198.41.192.7
2026-09-23T01:57:01Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=1 event=0 ip=198.41.192.7
2026-09-23T01:57:01Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=1 event=0 ip=198.41.192.7
2026-09-23T01:57:01Z INF Retrying connection in up to 1s connIndex=1 event=0 ip=198.41.192.7
2026-09-23T01:57:01Z INF Registered tunnel connection connIndex=3 connection=20b802d6-cab6-4dff-8c1c-618990a7998f event=0 ip=198.41.192.67 location=lax07 protocol=quic
2026-09-23T01:57:01Z ERR failed to run the datagram handler error="context canceled" connIndex=3 event=0 ip=198.41.192.67
2026-09-23T01:57:01Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=3 event=0 ip=198.41.192.67
2026-09-23T01:57:01Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=3 event=0 ip=198.41.192.67
2026-09-23T01:57:01Z INF Retrying connection in up to 1s connIndex=3 event=0 ip=198.41.192.67
2026-09-23T01:57:02Z ERR Connection terminated connIndex=0
2026-09-23T01:57:02Z ERR Connection terminated connIndex=2
2026-09-23T01:57:02Z ERR Connection terminated connIndex=1
2026-09-23T01:57:02Z ERR Connection terminated connIndex=3
2026-09-23T01:57:02Z ERR no more connections active and exiting
2026-09-23T01:57:02Z INF Tunnel server stopped
2026-09-23T01:57:02Z ERR icmp router terminated error="context canceled"
2026-09-23T01:57:02Z INF Metrics server stopped
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[09:56:42] Time: Wed Sep 23 09:56:42 AM CST 2026
[09:56:42] User: root (UID: 0)
[09:56:42] === STEP 1: 启动 API (端口 8450) ===
[09:56:42] 代码由 runner tarball 投递，权威 sha=e746884a
[09:56:42] commit 对比: 运行进程=b7d9c18b34aa7b46c24e32e3c39aefba12ca5acc / 磁盘=e746884af6fd9d4f02675a147ddc2e750219aeef
[09:56:42] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[09:56:42] 需要重新加载代码 -> 重启 API
[09:56:43] systemd 服务 aishield-api 已安装（Restart=always，WorkingDirectory=/opt/aishield）
[09:56:49] API 状态: OK（第 1 轮验证通过）
[09:56:49] === STEP 2: 安装 cloudflared ===
[09:56:49] cloudflared 安装路径: /usr/local/bin/cloudflared
[09:56:50] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[09:56:50] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[09:56:50] === STEP 3: 检查认证方式 ===
[09:56:50] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[09:56:50] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[09:56:50] 检查现有 tunnel...
[09:56:50] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS                                 
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax05, 1xlax08, 1xlax09, 1xlax10 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                                             
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                                             
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 1xlax09, 1xlax11                   
2026-09-23T01:56:50Z WRN Your version 2026.7.3 is outdated. We recommend upgrading it to 2026.9.1
[09:56:50] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[09:56:50] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[09:56:50] 凭证文件存在
[09:56:50] 创建 config.yml...
[09:56:50] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[09:56:50] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[09:56:53] DNS 路由结果: 2026-09-23T01:56:53Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[09:56:53] === STEP 5: 更新 DNS (API) ===
[09:56:53] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[09:56:54] 创建新 DNS CNAME 记录...
DNS 创建失败: [{"code": 9106, "message": "Missing X-Auth-Key, X-Auth-Email or Authorization headers"}]
[09:56:54] 设置 SSL 模式为 Full...
SSL: 跳过
[09:56:55] === STEP 6: 启动 Tunnel ===
[09:56:55] systemd 托管中 -> systemctl stop cloudflared-tunnel
[09:56:58] 启动 Named Tunnel (cert 模式)...
[09:56:58] 使用 config: /root/.cloudflared/config.yml
[09:56:58] cloudflared PID: 1898295
[09:57:00] Tunnel 连接已建立!
[09:57:00] --- cloudflared 日志 (最后 15 行) ---
2026-09-23T01:56:58Z INF GOOS: linux, GOVersion: go1.26.4, GoArch: amd64
2026-09-23T01:56:58Z INF Settings: map[config:/root/.cloudflared/config.yml cred-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json credentials-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json]
2026-09-23T01:56:58Z INF cloudflared will not automatically update if installed by a package manager.
2026-09-23T01:56:58Z INF Generated Connector ID: cb9b22ee-7b43-4c86-8828-1ad50f7d41ca
2026-09-23T01:56:58Z INF Initial protocol quic
2026-09-23T01:56:58Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-23T01:56:58Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-23T01:56:58Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-23T01:56:58Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-23T01:56:58Z INF Starting metrics server on 127.0.0.1:20242/metrics
2026-09-23T01:56:58Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.200.13
2026-09-23T01:56:59Z INF Registered tunnel connection connIndex=0 connection=3781242c-3211-471e-acb5-6c4721ca4798 event=0 ip=198.41.200.13 location=lax01 protocol=quic
2026-09-23T01:56:59Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.192.7
2026-09-23T01:57:00Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.200.53
2026-09-23T01:57:00Z INF Registered tunnel connection connIndex=1 connection=01bea30b-b554-43ba-948d-da42e7ffa661 event=0 ip=198.41.192.7 location=lax11 protocol=quic
[09:57:00] === STEP 7: 持久化 ===
[09:57:01] 停止 nohup cloudflared (PID 1898295) -> 交由 systemd 单实例托管
[09:57:03] systemd 服务已配置
[09:57:03] Cron 保活已设置（以本项目 API 健康为判据，不被他项目 tunnel 假满足）
[09:57:03] === STEP 8: 验证 ===
[09:57:03] --- API (localhost:8450) ---
 OK
[09:57:03] --- cloudflared 进程 ---
root     1335051  0.1  1.3 1294932 26164 ?       Sl   Sep18  11:07 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1335162  0.1  1.2 1294932 25812 ?       Ssl  Sep18  11:13 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     1898468  0.0  1.3 1292740 27996 ?       Rl   09:57   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[09:57:03] --- aishield.tools ---
 OK
[09:57:06] --- DNS CNAME ---
[09:57:06] --- DNS A ---
104.21.81.46
172.67.188.44
[09:57:06] === 部署汇总 ===
[09:57:06] Tunnel Mode: cert
[09:57:06] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[09:57:06] API: http://localhost:8450
[09:57:06] 域名: https://aishield.tools
[09:57:06] cloudflared: /usr/local/bin/cloudflared
[09:57:06] PID: 1898295
[09:57:06] Config: /root/.cloudflared/config.yml
[09:57:06] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[09:57:06] 状态: Named Tunnel (cert 模式) 已配置
[09:57:06] EXIT 0: API 健康
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Wed 2026-09-23 09:57:03 CST; 10s ago
   Main PID: 1898458 (start-tunnel.sh)
      Tasks: 8 (limit: 2216)
     Memory: 18.1M
        CPU: 141ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─1898458 /bin/bash /opt/start-tunnel.sh
             └─1898468 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
LISTEN 0      5            0.0.0.0:8450       0.0.0.0:*    users:(("python3",pid=1897972,fd=3))                                                    
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
Time: Wed Sep 23 01:57:22 UTC 2026

=== curl test (aishield.tools) ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 235, "rules_breakdown": {"static": 208, "generated": 8, "radar": 19, "total": 235}, "uptime": 1790128642.717977, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "e746884af6fd9d4f02675a147ddc2e750219aeef", "deployed_at": "2026-09-23T01:56:42Z"}
=== DNS lookup ===
172.67.188.44
104.21.81.46

=== DNS CNAME check ===
