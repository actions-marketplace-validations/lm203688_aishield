=== DIAGNOSTIC ===
Time: Mon Sep 14 04:57:58 PM CST 2026
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
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 236, "rules_breakdown": {"static": 210, "generated": 9, "radar": 17, "total": 236}, "uptime": 1789376278.5245898, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "73c672660e8e1d4c5e75d6ebd30148fb120b5dc9", "deployed_at": "2026-09-14T08:57:26Z"}OK
=== CLOUDFLARED PROCESS ===
root     2073940  1.0  1.7 1360028 35260 ?       Sl   16:57   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     2074084  1.6  1.7 1294676 35068 ?       Ssl  16:57   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     2074099  1.5  1.8 1294676 37120 ?       Sl   16:57   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-14T08:57:45Z INF Registered tunnel connection connIndex=0 connection=558edc05-9dda-4888-825e-b80b4668f81d event=0 ip=198.41.200.113 location=lax01 protocol=quic
2026-09-14T08:57:45Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.192.227
2026-09-14T08:57:46Z INF Registered tunnel connection connIndex=1 connection=4328dfb4-fb6e-4b46-a988-fdf58700dfff event=0 ip=198.41.192.227 location=lax07 protocol=quic
2026-09-14T08:57:46Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.200.13
2026-09-14T08:57:47Z INF Registered tunnel connection connIndex=2 connection=33a8d445-f4f4-49a1-8cdd-f214ddfb445f event=0 ip=198.41.200.13 location=lax01 protocol=quic
2026-09-14T08:57:47Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.192.57
2026-09-14T08:57:48Z INF Registered tunnel connection connIndex=3 connection=74c3b3b0-0e75-457f-9596-7b4062951ace event=0 ip=198.41.192.57 location=lax11 protocol=quic
2026-09-14T08:57:55Z INF +-----------------------------------------------------------------------------------------------+
2026-09-14T08:57:55Z INF |                                    CONNECTIVITY PRE-CHECKS                                    |
2026-09-14T08:57:55Z INF +-----------------------------------------------------------------------------------------------+
2026-09-14T08:57:55Z INF |  COMPONENT         TARGET                     STATUS  DETAILS                                 |
2026-09-14T08:57:55Z INF |  DNS Resolution    region1.v2.argotunnel.com  PASS    DNS Resolved successfully               |
2026-09-14T08:57:55Z INF |  DNS Resolution    region2.v2.argotunnel.com  PASS    DNS Resolved successfully               |
2026-09-14T08:57:55Z INF |  UDP Connectivity  region1.v2.argotunnel.com  PASS    QUIC connection successful              |
2026-09-14T08:57:55Z INF |  UDP Connectivity  region2.v2.argotunnel.com  FAIL    QUIC connection failed                  |
2026-09-14T08:57:55Z INF |  TCP Connectivity  region1.v2.argotunnel.com  PASS    HTTP/2 connection successful            |
2026-09-14T08:57:55Z INF |  TCP Connectivity  region2.v2.argotunnel.com  PASS    HTTP/2 connection successful            |
2026-09-14T08:57:55Z INF |  Cloudflare API    api.cloudflare.com:443     PASS    API is reachable                        |
2026-09-14T08:57:55Z INF |  WARNING: Allow outbound QUIC traffic on port 7844 or use HTTP2.                              |
2026-09-14T08:57:55Z INF |                                                                                               |
2026-09-14T08:57:55Z INF |  SUMMARY: Environment ready with degraded transport. cloudflared will proceed using 'http2'.  |
2026-09-14T08:57:55Z INF +-----------------------------------------------------------------------------------------------+
2026-09-14T08:57:55Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=0f7de753-3bd6-4456-9321-2add34c16d74 status=pass target=region1.v2.argotunnel.com
2026-09-14T08:57:55Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=0f7de753-3bd6-4456-9321-2add34c16d74 status=pass target=region2.v2.argotunnel.com
2026-09-14T08:57:55Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=0f7de753-3bd6-4456-9321-2add34c16d74 status=pass target=region1.v2.argotunnel.com
2026-09-14T08:57:55Z INF precheck component="UDP Connectivity" details="QUIC connection failed" run_id=0f7de753-3bd6-4456-9321-2add34c16d74 status=fail target=region2.v2.argotunnel.com
2026-09-14T08:57:55Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=0f7de753-3bd6-4456-9321-2add34c16d74 status=pass target=region1.v2.argotunnel.com
2026-09-14T08:57:55Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=0f7de753-3bd6-4456-9321-2add34c16d74 status=pass target=region2.v2.argotunnel.com
2026-09-14T08:57:55Z INF precheck component="Cloudflare API" details="API is reachable" run_id=0f7de753-3bd6-4456-9321-2add34c16d74 status=pass target=api.cloudflare.com:443
2026-09-14T08:57:55Z INF precheck complete hard_fail=false run_id=0f7de753-3bd6-4456-9321-2add34c16d74 suggested_protocol=http2
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[16:57:26] Time: Mon Sep 14 04:57:26 PM CST 2026
[16:57:26] User: root (UID: 0)
[16:57:26] === STEP 1: 启动 API (端口 8450) ===
[16:57:26] 代码由 runner tarball 投递，权威 sha=73c67266
[16:57:26] commit 对比: 运行进程=566d8dc160bee4b9f501f837d21733e2353f1404 / 磁盘=73c672660e8e1d4c5e75d6ebd30148fb120b5dc9
[16:57:26] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[16:57:26] 需要重新加载代码 -> 重启 API
[16:57:27] 强制重启 Python API 进程（当前commit=566d8dc160bee4b9f501f837d21733e2353f1404 目标=73c672660e8e1d4c5e75d6ebd30148fb120b5dc9）
[16:57:37] API 状态: OK
[16:57:37] === STEP 2: 安装 cloudflared ===
[16:57:37] cloudflared 安装路径: /usr/local/bin/cloudflared
[16:57:37] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:57:37] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:57:37] === STEP 3: 检查认证方式 ===
[16:57:37] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[16:57:37] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[16:57:37] 检查现有 tunnel...
[16:57:38] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS                        
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax05, 2xlax07, 1xlax10 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                                    
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                                    
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 1xlax11, 1xlax12          
2026-09-14T08:57:38Z WRN Your version 2026.7.3 is outdated. We recommend upgrading it to 2026.9.1
[16:57:38] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:57:38] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[16:57:38] 凭证文件存在
[16:57:38] 创建 config.yml...
[16:57:38] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[16:57:38] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:57:40] DNS 路由结果: 2026-09-14T08:57:40Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[16:57:40] === STEP 5: 更新 DNS (API) ===
[16:57:40] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:57:40] 更新现有 DNS 记录 (ID: fdc3eba7fdb90436809fe05358eb0f3a)
DNS 更新: OK
[16:57:41] 设置 SSL 模式为 Full...
SSL: 跳过
[16:57:42] === STEP 6: 启动 Tunnel ===
[16:57:45] 启动 Named Tunnel (cert 模式)...
[16:57:45] 使用 config: /root/.cloudflared/config.yml
[16:57:45] cloudflared PID: 2073940
[16:57:47] Tunnel 连接已建立!
[16:57:47] --- cloudflared 日志 (最后 15 行) ---
2026-09-14T08:57:45Z INF GOOS: linux, GOVersion: go1.26.4, GoArch: amd64
2026-09-14T08:57:45Z INF Settings: map[config:/root/.cloudflared/config.yml cred-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json credentials-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json]
2026-09-14T08:57:45Z INF cloudflared will not automatically update if installed by a package manager.
2026-09-14T08:57:45Z INF Generated Connector ID: 05a6aa4c-2a12-4e61-bc75-6639c6edb8f2
2026-09-14T08:57:45Z INF Initial protocol quic
2026-09-14T08:57:45Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-14T08:57:45Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-14T08:57:45Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-14T08:57:45Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-14T08:57:45Z INF Starting metrics server on 127.0.0.1:20241/metrics
2026-09-14T08:57:45Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.200.113
2026-09-14T08:57:45Z INF Registered tunnel connection connIndex=0 connection=558edc05-9dda-4888-825e-b80b4668f81d event=0 ip=198.41.200.113 location=lax01 protocol=quic
2026-09-14T08:57:45Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.192.227
2026-09-14T08:57:46Z INF Registered tunnel connection connIndex=1 connection=4328dfb4-fb6e-4b46-a988-fdf58700dfff event=0 ip=198.41.192.227 location=lax07 protocol=quic
2026-09-14T08:57:46Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.200.13
[16:57:47] === STEP 7: 持久化 ===
[16:57:48] systemd 服务已配置
[16:57:48] Cron 保活已设置
[16:57:48] === STEP 8: 验证 ===
[16:57:48] --- API (localhost:8450) ---
 OK
[16:57:48] --- cloudflared 进程 ---
root     2073940  3.3  1.9 1360028 38988 ?       Sl   16:57   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     2074084  0.0  1.3 1292740 26900 ?       Rsl  16:57   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     2074099  0.0  1.3 1292740 27220 ?       Rl   16:57   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[16:57:48] --- aishield.tools ---
 OK
[16:57:50] --- DNS CNAME ---
[16:57:50] --- DNS A ---
104.21.81.46
172.67.188.44
[16:57:50] === 部署汇总 ===
[16:57:50] Tunnel Mode: cert
[16:57:50] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:57:50] API: http://localhost:8450
[16:57:50] 域名: https://aishield.tools
[16:57:50] cloudflared: /usr/local/bin/cloudflared
[16:57:50] PID: 2073940
[16:57:50] Config: /root/.cloudflared/config.yml
[16:57:50] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:57:50] 状态: Named Tunnel (cert 模式) 已配置
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2026-09-14 16:57:48 CST; 10s ago
   Main PID: 2074088 (start-tunnel.sh)
      Tasks: 8 (limit: 2216)
     Memory: 20.3M
        CPU: 158ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─2074088 /bin/bash /opt/start-tunnel.sh
             └─2074099 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
LISTEN 0      5            0.0.0.0:8450       0.0.0.0:*    users:(("python3",pid=2073599,fd=3))                                                    
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
Time: Mon Sep 14 08:58:09 UTC 2026

=== curl test (aishield.tools) ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 236, "rules_breakdown": {"static": 210, "generated": 9, "radar": 17, "total": 236}, "uptime": 1789376290.231228, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "73c672660e8e1d4c5e75d6ebd30148fb120b5dc9", "deployed_at": "2026-09-14T08:57:26Z"}
=== DNS lookup ===
172.67.188.44
104.21.81.46

=== DNS CNAME check ===
