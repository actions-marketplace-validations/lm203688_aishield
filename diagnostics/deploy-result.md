=== DIAGNOSTIC ===
Time: Tue Sep 15 04:47:34 PM CST 2026
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
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 238, "rules_breakdown": {"static": 210, "generated": 9, "radar": 19, "total": 238}, "uptime": 1789462054.2280664, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "ff457dfc505c4db3a5a6c2a66e89b3f0c6ef513b", "deployed_at": "2026-09-15T08:46:52Z"}OK
=== CLOUDFLARED PROCESS ===
root     2997694  0.5  1.9 1360284 38852 ?       Sl   16:47   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     2997750  0.7  1.8 1294420 37720 ?       Ssl  16:47   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     2997955  1.0  1.9 1294676 38736 ?       Sl   16:47   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-15T08:47:20Z INF +-------------------------------------------------------------------------------------+
2026-09-15T08:47:20Z INF |                               CONNECTIVITY PRE-CHECKS                               |
2026-09-15T08:47:20Z INF +-------------------------------------------------------------------------------------+
2026-09-15T08:47:20Z INF |  COMPONENT         TARGET                     STATUS  DETAILS                       |
2026-09-15T08:47:20Z INF |  DNS Resolution    region1.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-15T08:47:20Z INF |  DNS Resolution    region2.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-15T08:47:20Z INF |  UDP Connectivity  region1.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-15T08:47:20Z INF |  UDP Connectivity  region2.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-15T08:47:20Z INF |  TCP Connectivity  region1.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-15T08:47:20Z INF |  TCP Connectivity  region2.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-15T08:47:20Z INF |  Cloudflare API    api.cloudflare.com:443     PASS    API is reachable              |
2026-09-15T08:47:20Z INF |                                                                                     |
2026-09-15T08:47:20Z INF |  SUMMARY: Environment is healthy. cloudflared will use 'quic' as primary protocol.  |
2026-09-15T08:47:20Z INF +-------------------------------------------------------------------------------------+
2026-09-15T08:47:20Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region1.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region2.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region1.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region2.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region1.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region2.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="Cloudflare API" details="API is reachable" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=api.cloudflare.com:443
2026-09-15T08:47:20Z INF precheck complete hard_fail=false run_id=0c01cb99-753f-40cc-ae84-57878a840e8c suggested_protocol=quic
2026-09-15T08:47:20Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.200.53
2026-09-15T08:47:20Z INF Registered tunnel connection connIndex=3 connection=51802939-37d9-4275-bb56-96f66f3514aa event=0 ip=198.41.200.53 location=lax01 protocol=quic
2026-09-15T08:47:23Z WRN Failed to dial a quic connection error="failed to dial to edge with quic: timeout: no recent network activity" connIndex=1 event=0 ip=198.41.200.193
2026-09-15T08:47:23Z INF Retrying connection in up to 2s connIndex=1 event=0 ip=198.41.200.193
2026-09-15T08:47:23Z WRN Connection terminated error="failed to dial to edge with quic: timeout: no recent network activity" connIndex=1
2026-09-15T08:47:28Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.73
2026-09-15T08:47:33Z WRN Failed to dial a quic connection error="failed to dial to edge with quic: timeout: no recent network activity" connIndex=1 event=0 ip=198.41.200.73
2026-09-15T08:47:33Z INF Retrying connection in up to 4s connIndex=1 event=0 ip=198.41.200.73
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[16:46:52] Time: Tue Sep 15 04:46:52 PM CST 2026
[16:46:52] User: root (UID: 0)
[16:46:52] === STEP 1: 启动 API (端口 8450) ===
[16:46:52] 代码由 runner tarball 投递，权威 sha=ff457dfc
[16:46:52] commit 对比: 运行进程=73c672660e8e1d4c5e75d6ebd30148fb120b5dc9 / 磁盘=ff457dfc505c4db3a5a6c2a66e89b3f0c6ef513b
[16:46:52] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[16:46:52] 需要重新加载代码 -> 重启 API
[16:46:53] 强制重启 Python API 进程（当前commit=73c672660e8e1d4c5e75d6ebd30148fb120b5dc9 目标=ff457dfc505c4db3a5a6c2a66e89b3f0c6ef513b）
[16:47:03] API 状态: OK
[16:47:03] === STEP 2: 安装 cloudflared ===
[16:47:03] cloudflared 安装路径: /usr/local/bin/cloudflared
[16:47:03] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:47:03] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:47:03] === STEP 3: 检查认证方式 ===
[16:47:03] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[16:47:03] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[16:47:03] 检查现有 tunnel...
[16:47:04] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS                        
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax07, 1xlax08, 2xlax10 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                                    
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                                    
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 2xlax10                   
2026-09-15T08:47:04Z WRN Your version 2026.7.3 is outdated. We recommend upgrading it to 2026.9.1
[16:47:04] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:47:04] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[16:47:04] 凭证文件存在
[16:47:04] 创建 config.yml...
[16:47:04] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[16:47:04] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:47:06] DNS 路由结果: 2026-09-15T08:47:06Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[16:47:06] === STEP 5: 更新 DNS (API) ===
[16:47:06] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:47:06] 更新现有 DNS 记录 (ID: fdc3eba7fdb90436809fe05358eb0f3a)
DNS 更新: OK
[16:47:07] 设置 SSL 模式为 Full...
SSL: 跳过
[16:47:09] === STEP 6: 启动 Tunnel ===
[16:47:12] 启动 Named Tunnel (cert 模式)...
[16:47:12] 使用 config: /root/.cloudflared/config.yml
[16:47:12] cloudflared PID: 2997694
[16:47:20] Tunnel 连接已建立!
[16:47:20] --- cloudflared 日志 (最后 15 行) ---
2026-09-15T08:47:20Z INF |  UDP Connectivity  region2.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-15T08:47:20Z INF |  TCP Connectivity  region1.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-15T08:47:20Z INF |  TCP Connectivity  region2.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-15T08:47:20Z INF |  Cloudflare API    api.cloudflare.com:443     PASS    API is reachable              |
2026-09-15T08:47:20Z INF |                                                                                     |
2026-09-15T08:47:20Z INF |  SUMMARY: Environment is healthy. cloudflared will use 'quic' as primary protocol.  |
2026-09-15T08:47:20Z INF +-------------------------------------------------------------------------------------+
2026-09-15T08:47:20Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region1.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region2.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region1.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region2.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region1.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=region2.v2.argotunnel.com
2026-09-15T08:47:20Z INF precheck component="Cloudflare API" details="API is reachable" run_id=0c01cb99-753f-40cc-ae84-57878a840e8c status=pass target=api.cloudflare.com:443
2026-09-15T08:47:20Z INF precheck complete hard_fail=false run_id=0c01cb99-753f-40cc-ae84-57878a840e8c suggested_protocol=quic
[16:47:20] === STEP 7: 持久化 ===
[16:47:21] systemd 服务已配置
[16:47:21] Cron 保活已设置
[16:47:21] === STEP 8: 验证 ===
[16:47:21] --- API (localhost:8450) ---
 OK
[16:47:21] --- cloudflared 进程 ---
root     2997694  1.2  1.9 1360284 39720 ?       Sl   16:47   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     2997750  1.5  1.9 1294420 39556 ?       Ssl  16:47   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     2997955  0.0  1.0 1292484 21220 ?       Rl   16:47   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[16:47:21] --- aishield.tools ---
 OK
[16:47:23] --- DNS CNAME ---
[16:47:24] --- DNS A ---
104.21.81.46
172.67.188.44
[16:47:24] === 部署汇总 ===
[16:47:24] Tunnel Mode: cert
[16:47:24] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:47:24] API: http://localhost:8450
[16:47:24] 域名: https://aishield.tools
[16:47:24] cloudflared: /usr/local/bin/cloudflared
[16:47:24] PID: 2997694
[16:47:24] Config: /root/.cloudflared/config.yml
[16:47:24] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:47:24] 状态: Named Tunnel (cert 模式) 已配置
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Tue 2026-09-15 16:47:21 CST; 12s ago
   Main PID: 2997947 (start-tunnel.sh)
      Tasks: 9 (limit: 2216)
     Memory: 19.4M
        CPU: 150ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─2997947 /bin/bash /opt/start-tunnel.sh
             └─2997955 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
LISTEN 0      5            0.0.0.0:8450       0.0.0.0:*    users:(("python3",pid=2997384,fd=3))                                                    
=== CRONTAB ===
*/5 * * * * flock -xn /tmp/stargate.lock -c '/usr/local/qcloud/stargate/admin/start.sh > /dev/null 2>&1 &'
* * * * * pgrep -f 'cloudflared tunnel' > /dev/null 2>&1 || /opt/start-tunnel.sh >> /tmp/cloudflared.log 2>&1
=== START SCRIPT ===
#!/bin/bash
# AIShield Tunnel 启动脚本
CF_BIN='/usr/local/bin/cloudflared'
CONFIG_FILE='/root/.cloudflared/config.yml'
TOKEN_FILE='/root/.cloudflared/tunnel-token'

cleanup() { kill $CF_PID 2>/dev/null; exit 0; }
trap cleanup SIGTERM SIGINT

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
Time: Tue Sep 15 08:47:47 UTC 2026

=== curl test (aishield.tools) ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 238, "rules_breakdown": {"static": 210, "generated": 9, "radar": 19, "total": 238}, "uptime": 1789462067.8496144, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "ff457dfc505c4db3a5a6c2a66e89b3f0c6ef513b", "deployed_at": "2026-09-15T08:46:52Z"}
=== DNS lookup ===
172.67.188.44
104.21.81.46

=== DNS CNAME check ===
