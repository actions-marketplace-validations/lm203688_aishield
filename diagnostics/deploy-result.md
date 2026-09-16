=== DIAGNOSTIC ===
Time: Wed Sep 16 04:39:49 PM CST 2026
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
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 238, "rules_breakdown": {"static": 210, "generated": 9, "radar": 19, "total": 238}, "uptime": 1789547989.442976, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "f65e49865b9548340080319655a8fae50bff5b74", "deployed_at": "2026-09-16T08:39:15Z"}OK
=== CLOUDFLARED PROCESS ===
root     3940459  1.0  1.9 1294420 39460 ?       Sl   16:39   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     3940602  1.3  1.9 1294676 39584 ?       Ssl  16:39   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     3940607  1.4  1.9 1360284 40124 ?       Sl   16:39   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-16T08:39:36Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.200.63
2026-09-16T08:39:36Z INF Registered tunnel connection connIndex=0 connection=0f6f9743-99dd-4339-ae6e-bf3b539108e1 event=0 ip=198.41.200.63 location=lax01 protocol=quic
2026-09-16T08:39:36Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.192.227
2026-09-16T08:39:37Z INF Registered tunnel connection connIndex=1 connection=90d4f254-73b3-4039-bf7f-021415b40d9e event=0 ip=198.41.192.227 location=lax10 protocol=quic
2026-09-16T08:39:37Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.192.27
2026-09-16T08:39:38Z INF Registered tunnel connection connIndex=2 connection=56b92577-a2fd-4c22-ba91-33b9edb0ec25 event=0 ip=198.41.192.27 location=lax11 protocol=quic
2026-09-16T08:39:38Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.200.53
2026-09-16T08:39:39Z INF Registered tunnel connection connIndex=3 connection=535298f4-9020-4731-94af-04430640b2c9 event=0 ip=198.41.200.53 location=lax01 protocol=quic
2026-09-16T08:39:43Z INF +-------------------------------------------------------------------------------------+
2026-09-16T08:39:43Z INF |                               CONNECTIVITY PRE-CHECKS                               |
2026-09-16T08:39:43Z INF +-------------------------------------------------------------------------------------+
2026-09-16T08:39:43Z INF |  COMPONENT         TARGET                     STATUS  DETAILS                       |
2026-09-16T08:39:43Z INF |  DNS Resolution    region1.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-16T08:39:43Z INF |  DNS Resolution    region2.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-16T08:39:43Z INF |  UDP Connectivity  region1.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-16T08:39:43Z INF |  UDP Connectivity  region2.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-16T08:39:43Z INF |  TCP Connectivity  region1.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-16T08:39:43Z INF |  TCP Connectivity  region2.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-16T08:39:43Z INF |  Cloudflare API    api.cloudflare.com:443     PASS    API is reachable              |
2026-09-16T08:39:43Z INF |                                                                                     |
2026-09-16T08:39:43Z INF |  SUMMARY: Environment is healthy. cloudflared will use 'quic' as primary protocol.  |
2026-09-16T08:39:43Z INF +-------------------------------------------------------------------------------------+
2026-09-16T08:39:43Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=57773346-975a-4ad3-aeba-9cec2274dfeb status=pass target=region1.v2.argotunnel.com
2026-09-16T08:39:43Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=57773346-975a-4ad3-aeba-9cec2274dfeb status=pass target=region2.v2.argotunnel.com
2026-09-16T08:39:43Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=57773346-975a-4ad3-aeba-9cec2274dfeb status=pass target=region1.v2.argotunnel.com
2026-09-16T08:39:43Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=57773346-975a-4ad3-aeba-9cec2274dfeb status=pass target=region2.v2.argotunnel.com
2026-09-16T08:39:43Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=57773346-975a-4ad3-aeba-9cec2274dfeb status=pass target=region1.v2.argotunnel.com
2026-09-16T08:39:43Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=57773346-975a-4ad3-aeba-9cec2274dfeb status=pass target=region2.v2.argotunnel.com
2026-09-16T08:39:43Z INF precheck component="Cloudflare API" details="API is reachable" run_id=57773346-975a-4ad3-aeba-9cec2274dfeb status=pass target=api.cloudflare.com:443
2026-09-16T08:39:43Z INF precheck complete hard_fail=false run_id=57773346-975a-4ad3-aeba-9cec2274dfeb suggested_protocol=quic
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[16:39:15] Time: Wed Sep 16 04:39:15 PM CST 2026
[16:39:15] User: root (UID: 0)
[16:39:15] === STEP 1: 启动 API (端口 8450) ===
[16:39:15] 代码由 runner tarball 投递，权威 sha=f65e4986
[16:39:15] commit 对比: 运行进程=ff457dfc505c4db3a5a6c2a66e89b3f0c6ef513b / 磁盘=f65e49865b9548340080319655a8fae50bff5b74
[16:39:15] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[16:39:15] 需要重新加载代码 -> 重启 API
[16:39:16] 强制重启 Python API 进程（当前commit=ff457dfc505c4db3a5a6c2a66e89b3f0c6ef513b 目标=f65e49865b9548340080319655a8fae50bff5b74）
[16:39:26] API 状态: OK
[16:39:26] === STEP 2: 安装 cloudflared ===
[16:39:26] cloudflared 安装路径: /usr/local/bin/cloudflared
[16:39:26] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:39:26] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:39:26] === STEP 3: 检查认证方式 ===
[16:39:26] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[16:39:26] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[16:39:26] 检查现有 tunnel...
[16:39:27] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS               
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax07, 3xlax10 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                           
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                           
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 1xlax08, 1xlax10 
[16:39:27] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:39:27] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[16:39:27] 凭证文件存在
[16:39:27] 创建 config.yml...
[16:39:27] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[16:39:27] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:39:29] DNS 路由结果: 2026-09-16T08:39:29Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[16:39:29] === STEP 5: 更新 DNS (API) ===
[16:39:29] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:39:30] 创建新 DNS CNAME 记录...
DNS 创建失败: [{"code": 9106, "message": "Missing X-Auth-Key, X-Auth-Email or Authorization headers"}]
[16:39:31] 设置 SSL 模式为 Full...
SSL: 跳过
[16:39:33] === STEP 6: 启动 Tunnel ===
[16:39:36] 启动 Named Tunnel (cert 模式)...
[16:39:36] 使用 config: /root/.cloudflared/config.yml
[16:39:36] cloudflared PID: 3940459
[16:39:38] Tunnel 连接已建立!
[16:39:38] --- cloudflared 日志 (最后 15 行) ---
2026-09-16T08:39:36Z INF Settings: map[config:/root/.cloudflared/config.yml cred-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json credentials-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json]
2026-09-16T08:39:36Z INF cloudflared will not automatically update if installed by a package manager.
2026-09-16T08:39:36Z INF Generated Connector ID: 5bd621da-ffda-4c51-ba62-f0c76de0caaf
2026-09-16T08:39:36Z INF Initial protocol quic
2026-09-16T08:39:36Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-16T08:39:36Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-16T08:39:36Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-16T08:39:36Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-16T08:39:36Z INF Starting metrics server on 127.0.0.1:20241/metrics
2026-09-16T08:39:36Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.200.63
2026-09-16T08:39:36Z INF Registered tunnel connection connIndex=0 connection=0f6f9743-99dd-4339-ae6e-bf3b539108e1 event=0 ip=198.41.200.63 location=lax01 protocol=quic
2026-09-16T08:39:36Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.192.227
2026-09-16T08:39:37Z INF Registered tunnel connection connIndex=1 connection=90d4f254-73b3-4039-bf7f-021415b40d9e event=0 ip=198.41.192.227 location=lax10 protocol=quic
2026-09-16T08:39:37Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.192.27
2026-09-16T08:39:38Z INF Registered tunnel connection connIndex=2 connection=56b92577-a2fd-4c22-ba91-33b9edb0ec25 event=0 ip=198.41.192.27 location=lax11 protocol=quic
[16:39:38] === STEP 7: 持久化 ===
[16:39:39] systemd 服务已配置
[16:39:39] Cron 保活已设置
[16:39:39] === STEP 8: 验证 ===
[16:39:39] --- API (localhost:8450) ---
 OK
[16:39:39] --- cloudflared 进程 ---
root     3940459  3.0  1.9 1294420 39460 ?       Sl   16:39   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     3940602  0.0  1.3 1292484 27296 ?       Rsl  16:39   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     3940607  0.0  1.3 1358348 27428 ?       Rl   16:39   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[16:39:39] --- aishield.tools ---
 OK
[16:39:40] --- DNS CNAME ---
[16:39:41] --- DNS A ---
104.21.81.46
172.67.188.44
[16:39:41] === 部署汇总 ===
[16:39:41] Tunnel Mode: cert
[16:39:41] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:39:41] API: http://localhost:8450
[16:39:41] 域名: https://aishield.tools
[16:39:41] cloudflared: /usr/local/bin/cloudflared
[16:39:41] PID: 3940459
[16:39:41] Config: /root/.cloudflared/config.yml
[16:39:41] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:39:41] 状态: Named Tunnel (cert 模式) 已配置
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Wed 2026-09-16 16:39:39 CST; 10s ago
   Main PID: 3940606 (start-tunnel.sh)
      Tasks: 9 (limit: 2216)
     Memory: 18.2M
        CPU: 152ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─3940606 /bin/bash /opt/start-tunnel.sh
             └─3940607 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
LISTEN 0      5            0.0.0.0:8450       0.0.0.0:*    users:(("python3",pid=3940150,fd=3))                                                    
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
Time: Wed Sep 16 08:39:58 UTC 2026

=== curl test (aishield.tools) ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 238, "rules_breakdown": {"static": 210, "generated": 9, "radar": 19, "total": 238}, "uptime": 1789547999.0320961, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "f65e49865b9548340080319655a8fae50bff5b74", "deployed_at": "2026-09-16T08:39:15Z"}
=== DNS lookup ===
172.67.188.44
104.21.81.46

=== DNS CNAME check ===
