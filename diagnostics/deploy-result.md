=== DIAGNOSTIC ===
Time: Sat Sep 19 01:33:55 PM CST 2026
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
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 235, "rules_breakdown": {"static": 208, "generated": 8, "radar": 19, "total": 235}, "uptime": 1789796035.3074982, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "8103c3845b97756050915074287118eb3db48728", "deployed_at": "2026-09-19T05:33:13Z"}OK
=== CLOUDFLARED PROCESS ===
root     1335051  0.1  1.2 1294932 24596 ?       Sl   Sep18   2:40 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1335162  0.1  1.2 1294676 25480 ?       Ssl  Sep18   2:39 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     2448537  0.9  1.9 1294420 39440 ?       Sl   13:33   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-19T05:33:40Z INF |  UDP Connectivity  region1.v2.argotunnel.com  PASS    QUIC connection successful              |
2026-09-19T05:33:40Z INF |  UDP Connectivity  region2.v2.argotunnel.com  FAIL    QUIC connection failed                  |
2026-09-19T05:33:40Z INF |  TCP Connectivity  region1.v2.argotunnel.com  PASS    HTTP/2 connection successful            |
2026-09-19T05:33:40Z INF |  TCP Connectivity  region2.v2.argotunnel.com  PASS    HTTP/2 connection successful            |
2026-09-19T05:33:40Z INF |  Cloudflare API    api.cloudflare.com:443     PASS    API is reachable                        |
2026-09-19T05:33:40Z INF |  WARNING: Allow outbound QUIC traffic on port 7844 or use HTTP2.                              |
2026-09-19T05:33:40Z INF |                                                                                               |
2026-09-19T05:33:40Z INF |  SUMMARY: Environment ready with degraded transport. cloudflared will proceed using 'http2'.  |
2026-09-19T05:33:40Z INF +-----------------------------------------------------------------------------------------------+
2026-09-19T05:33:40Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=8a61564b-b7b9-4fba-bbf5-dc60467fb685 status=pass target=region1.v2.argotunnel.com
2026-09-19T05:33:40Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=8a61564b-b7b9-4fba-bbf5-dc60467fb685 status=pass target=region2.v2.argotunnel.com
2026-09-19T05:33:40Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=8a61564b-b7b9-4fba-bbf5-dc60467fb685 status=pass target=region1.v2.argotunnel.com
2026-09-19T05:33:40Z INF precheck component="UDP Connectivity" details="QUIC connection failed" run_id=8a61564b-b7b9-4fba-bbf5-dc60467fb685 status=fail target=region2.v2.argotunnel.com
2026-09-19T05:33:40Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=8a61564b-b7b9-4fba-bbf5-dc60467fb685 status=pass target=region1.v2.argotunnel.com
2026-09-19T05:33:40Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=8a61564b-b7b9-4fba-bbf5-dc60467fb685 status=pass target=region2.v2.argotunnel.com
2026-09-19T05:33:40Z INF precheck component="Cloudflare API" details="API is reachable" run_id=8a61564b-b7b9-4fba-bbf5-dc60467fb685 status=pass target=api.cloudflare.com:443
2026-09-19T05:33:40Z INF precheck complete hard_fail=false run_id=8a61564b-b7b9-4fba-bbf5-dc60467fb685 suggested_protocol=http2
2026-09-19T05:33:40Z INF Registered tunnel connection connIndex=3 connection=42dbd833-5a68-4771-a041-2b202ef2646b event=0 ip=198.41.192.7 location=lax07 protocol=quic
2026-09-19T05:33:40Z ERR Connection terminated connIndex=0
2026-09-19T05:33:40Z ERR Connection terminated connIndex=1
2026-09-19T05:33:40Z ERR Connection terminated connIndex=2
2026-09-19T05:33:46Z ERR failed to run the datagram handler error="context canceled" connIndex=3 event=0 ip=198.41.192.7
2026-09-19T05:33:46Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=3 event=0 ip=198.41.192.7
2026-09-19T05:33:46Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=3 event=0 ip=198.41.192.7
2026-09-19T05:33:46Z INF Retrying connection in up to 1s connIndex=3 event=0 ip=198.41.192.7
2026-09-19T05:33:46Z ERR Connection terminated connIndex=3
2026-09-19T05:33:46Z ERR no more connections active and exiting
2026-09-19T05:33:46Z INF Tunnel server stopped
2026-09-19T05:33:46Z ERR icmp router terminated error="context canceled"
2026-09-19T05:33:46Z INF Metrics server stopped
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[13:33:13] Time: Sat Sep 19 01:33:13 PM CST 2026
[13:33:13] User: root (UID: 0)
[13:33:13] === STEP 1: 启动 API (端口 8450) ===
[13:33:13] 代码由 runner tarball 投递，权威 sha=8103c384
[13:33:13] commit 对比: 运行进程=83d6318b8899724fe79829d136717fe92dc77c6a / 磁盘=8103c3845b97756050915074287118eb3db48728
[13:33:13] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[13:33:13] 需要重新加载代码 -> 重启 API
[13:33:15] systemd 服务 aishield-api 已安装（Restart=always，WorkingDirectory=/opt/aishield）
[13:33:21] API 状态: OK（第 1 轮验证通过）
[13:33:21] === STEP 2: 安装 cloudflared ===
[13:33:21] cloudflared 安装路径: /usr/local/bin/cloudflared
[13:33:21] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[13:33:21] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[13:33:21] === STEP 3: 检查认证方式 ===
[13:33:21] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[13:33:21] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[13:33:21] 检查现有 tunnel...
[13:33:23] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS                        
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax07, 1xlax08, 2xlax10 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                                    
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                                    
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 1xlax09, 1xlax11          
2026-09-19T05:33:23Z WRN Your version 2026.7.3 is outdated. We recommend upgrading it to 2026.9.1
[13:33:23] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[13:33:23] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[13:33:23] 凭证文件存在
[13:33:23] 创建 config.yml...
[13:33:23] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[13:33:23] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[13:33:24] DNS 路由结果: 2026-09-19T05:33:24Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[13:33:24] === STEP 5: 更新 DNS (API) ===
[13:33:24] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[13:33:24] 创建新 DNS CNAME 记录...
DNS 创建失败: [{"code": 9106, "message": "Missing X-Auth-Key, X-Auth-Email or Authorization headers"}]
[13:33:25] 设置 SSL 模式为 Full...
SSL: 跳过
[13:33:26] === STEP 6: 启动 Tunnel ===
[13:33:26] systemd 托管中 -> systemctl stop cloudflared-tunnel
[13:33:29] 启动 Named Tunnel (cert 模式)...
[13:33:29] 使用 config: /root/.cloudflared/config.yml
[13:33:29] cloudflared PID: 2448306
[13:33:37] Tunnel 连接已建立!
[13:33:37] --- cloudflared 日志 (最后 15 行) ---
2026-09-19T05:33:30Z INF cloudflared will not automatically update if installed by a package manager.
2026-09-19T05:33:30Z INF Generated Connector ID: f9c0ac9d-5739-4d2e-b79f-ba001e27bd72
2026-09-19T05:33:30Z INF Initial protocol quic
2026-09-19T05:33:30Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-19T05:33:30Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-19T05:33:30Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-19T05:33:30Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-19T05:33:30Z INF Starting metrics server on 127.0.0.1:20242/metrics
2026-09-19T05:33:30Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.200.73
2026-09-19T05:33:35Z ERR Failed to dial a quic connection error="failed to dial to edge with quic: timeout: no recent network activity" connIndex=0 event=0 ip=198.41.200.73
2026-09-19T05:33:35Z INF Retrying connection in up to 2s connIndex=0 event=0 ip=198.41.200.73
2026-09-19T05:33:37Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.192.57
2026-09-19T05:33:37Z INF Registered tunnel connection connIndex=0 connection=cdce4424-88f6-47cc-abd9-4d90de5de0e3 event=0 ip=198.41.192.57 location=lax11 protocol=quic
2026-09-19T05:33:37Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.33
2026-09-19T05:33:37Z INF Registered tunnel connection connIndex=1 connection=d0dcbd61-bf76-450d-8ab9-6324a2ad0c9d event=0 ip=198.41.200.33 location=lax01 protocol=quic
[13:33:37] === STEP 7: 持久化 ===
[13:33:38] 停止 nohup cloudflared (PID 2448306) -> 交由 systemd 单实例托管
[13:33:40] systemd 服务已配置
[13:33:40] Cron 保活已设置（以本项目 API 健康为判据，不被他项目 tunnel 假满足）
[13:33:40] === STEP 8: 验证 ===
[13:33:40] --- API (localhost:8450) ---
 OK
[13:33:40] --- cloudflared 进程 ---
root     1335051  0.1  1.2 1294932 25188 ?       Sl   Sep18   2:40 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1335162  0.1  1.2 1294676 26136 ?       Ssl  Sep18   2:39 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     2448306  3.0  1.9 1294676 39728 ?       Sl   13:33   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[13:33:40] --- aishield.tools ---
 OK
[13:33:42] --- DNS CNAME ---
[13:33:42] --- DNS A ---
104.21.81.46
172.67.188.44
[13:33:42] === 部署汇总 ===
[13:33:42] Tunnel Mode: cert
[13:33:42] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[13:33:42] API: http://localhost:8450
[13:33:42] 域名: https://aishield.tools
[13:33:42] cloudflared: /usr/local/bin/cloudflared
[13:33:42] PID: 2448306
[13:33:42] Config: /root/.cloudflared/config.yml
[13:33:42] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[13:33:42] 状态: Named Tunnel (cert 模式) 已配置
[13:33:42] EXIT 0: API 健康
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Sat 2026-09-19 13:33:40 CST; 14s ago
   Main PID: 2448532 (start-tunnel.sh)
      Tasks: 9 (limit: 2216)
     Memory: 18.3M
        CPU: 159ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─2448532 /bin/bash /opt/start-tunnel.sh
             └─2448537 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
LISTEN 0      5            0.0.0.0:8450       0.0.0.0:*    users:(("python3",pid=2447992,fd=3))                                                    
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
Time: Sat Sep 19 05:34:07 UTC 2026

=== curl test (aishield.tools) ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 235, "rules_breakdown": {"static": 208, "generated": 8, "radar": 19, "total": 235}, "uptime": 1789796048.0132573, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "8103c3845b97756050915074287118eb3db48728", "deployed_at": "2026-09-19T05:33:13Z"}
=== DNS lookup ===
172.67.188.44
104.21.81.46

=== DNS CNAME check ===
