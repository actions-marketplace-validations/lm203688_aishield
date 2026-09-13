=== DIAGNOSTIC ===
Time: Sun Sep 13 04:24:15 PM CST 2026
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
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 236, "rules_breakdown": {"static": 210, "generated": 9, "radar": 17, "total": 236}, "uptime": 1789287855.9371982, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "566d8dc160bee4b9f501f837d21733e2353f1404", "deployed_at": "2026-09-13T08:23:42Z"}OK
=== CLOUDFLARED PROCESS ===
root     1110458  1.0  1.9 1294676 39856 ?       Sl   16:24   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1110568  1.5  2.0 1294676 40440 ?       Ssl  16:24   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     1110570  1.5  2.0 1294420 40504 ?       Sl   16:24   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-13T08:24:02Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.192.107
2026-09-13T08:24:03Z INF Registered tunnel connection connIndex=0 connection=82a9177b-8f9d-4175-afe5-3f1ff2568e0c event=0 ip=198.41.192.107 location=lax07 protocol=quic
2026-09-13T08:24:03Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.233
2026-09-13T08:24:03Z INF Registered tunnel connection connIndex=1 connection=fbfb4054-4737-461b-aa49-65c2539b0534 event=0 ip=198.41.200.233 location=lax01 protocol=quic
2026-09-13T08:24:04Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.200.113
2026-09-13T08:24:04Z INF Registered tunnel connection connIndex=2 connection=8101c1a4-7a9b-4fc6-be6d-e21efb777ce9 event=0 ip=198.41.200.113 location=lax01 protocol=quic
2026-09-13T08:24:05Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.192.27
2026-09-13T08:24:05Z INF Registered tunnel connection connIndex=3 connection=687f515e-aaf0-4a3f-a876-c661e5597a18 event=0 ip=198.41.192.27 location=lax10 protocol=quic
2026-09-13T08:24:09Z INF +-------------------------------------------------------------------------------------+
2026-09-13T08:24:09Z INF |                               CONNECTIVITY PRE-CHECKS                               |
2026-09-13T08:24:09Z INF +-------------------------------------------------------------------------------------+
2026-09-13T08:24:09Z INF |  COMPONENT         TARGET                     STATUS  DETAILS                       |
2026-09-13T08:24:09Z INF |  DNS Resolution    region1.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-13T08:24:09Z INF |  DNS Resolution    region2.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-13T08:24:09Z INF |  UDP Connectivity  region1.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-13T08:24:09Z INF |  UDP Connectivity  region2.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-13T08:24:09Z INF |  TCP Connectivity  region1.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-13T08:24:09Z INF |  TCP Connectivity  region2.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-13T08:24:09Z INF |  Cloudflare API    api.cloudflare.com:443     PASS    API is reachable              |
2026-09-13T08:24:09Z INF |                                                                                     |
2026-09-13T08:24:09Z INF |  SUMMARY: Environment is healthy. cloudflared will use 'quic' as primary protocol.  |
2026-09-13T08:24:09Z INF +-------------------------------------------------------------------------------------+
2026-09-13T08:24:09Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=d7ebc664-9c44-4c25-bb6f-73ce8a8b6280 status=pass target=region1.v2.argotunnel.com
2026-09-13T08:24:09Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=d7ebc664-9c44-4c25-bb6f-73ce8a8b6280 status=pass target=region2.v2.argotunnel.com
2026-09-13T08:24:09Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=d7ebc664-9c44-4c25-bb6f-73ce8a8b6280 status=pass target=region1.v2.argotunnel.com
2026-09-13T08:24:09Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=d7ebc664-9c44-4c25-bb6f-73ce8a8b6280 status=pass target=region2.v2.argotunnel.com
2026-09-13T08:24:09Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=d7ebc664-9c44-4c25-bb6f-73ce8a8b6280 status=pass target=region1.v2.argotunnel.com
2026-09-13T08:24:09Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=d7ebc664-9c44-4c25-bb6f-73ce8a8b6280 status=pass target=region2.v2.argotunnel.com
2026-09-13T08:24:09Z INF precheck component="Cloudflare API" details="API is reachable" run_id=d7ebc664-9c44-4c25-bb6f-73ce8a8b6280 status=pass target=api.cloudflare.com:443
2026-09-13T08:24:09Z INF precheck complete hard_fail=false run_id=d7ebc664-9c44-4c25-bb6f-73ce8a8b6280 suggested_protocol=quic
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[16:23:42] Time: Sun Sep 13 04:23:42 PM CST 2026
[16:23:42] User: root (UID: 0)
[16:23:42] === STEP 1: 启动 API (端口 8450) ===
[16:23:42] 代码由 runner tarball 投递，权威 sha=566d8dc1
[16:23:42] commit 对比: 运行进程=81eb016a5fd4f1da0f898b66a6f811e6e41e8cd7 / 磁盘=566d8dc160bee4b9f501f837d21733e2353f1404
[16:23:42] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[16:23:42] 需要重新加载代码 -> 重启 API
[16:23:42] 强制重启 Python API 进程（当前commit=81eb016a5fd4f1da0f898b66a6f811e6e41e8cd7 目标=566d8dc160bee4b9f501f837d21733e2353f1404）
[16:23:52] API 状态: OK
[16:23:52] === STEP 2: 安装 cloudflared ===
[16:23:52] cloudflared 安装路径: /usr/local/bin/cloudflared
[16:23:53] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:23:53] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:23:53] === STEP 3: 检查认证方式 ===
[16:23:53] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[16:23:53] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[16:23:53] 检查现有 tunnel...
[16:23:54] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS                                 
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax05, 1xlax08, 1xlax09, 1xlax10 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                                             
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                                             
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 1xlax08, 1xlax09                   
2026-09-13T08:23:54Z WRN Your version 2026.7.3 is outdated. We recommend upgrading it to 2026.9.1
[16:23:54] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:23:54] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[16:23:54] 凭证文件存在
[16:23:54] 创建 config.yml...
[16:23:54] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[16:23:54] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:23:57] DNS 路由结果: 2026-09-13T08:23:57Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[16:23:57] === STEP 5: 更新 DNS (API) ===
[16:23:57] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:23:58] 更新现有 DNS 记录 (ID: fdc3eba7fdb90436809fe05358eb0f3a)
DNS 更新: OK
[16:23:58] 设置 SSL 模式为 Full...
SSL: 跳过
[16:23:59] === STEP 6: 启动 Tunnel ===
[16:24:02] 启动 Named Tunnel (cert 模式)...
[16:24:02] 使用 config: /root/.cloudflared/config.yml
[16:24:02] cloudflared PID: 1110458
[16:24:04] Tunnel 连接已建立!
[16:24:04] --- cloudflared 日志 (最后 15 行) ---
2026-09-13T08:24:02Z INF Settings: map[config:/root/.cloudflared/config.yml cred-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json credentials-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json]
2026-09-13T08:24:02Z INF cloudflared will not automatically update if installed by a package manager.
2026-09-13T08:24:02Z INF Generated Connector ID: 4a1c862a-4d60-47e6-a6ae-b7ca740f1ec3
2026-09-13T08:24:02Z INF Initial protocol quic
2026-09-13T08:24:02Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-13T08:24:02Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-13T08:24:02Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-13T08:24:02Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-13T08:24:02Z INF Starting metrics server on 127.0.0.1:20241/metrics
2026-09-13T08:24:02Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.192.107
2026-09-13T08:24:03Z INF Registered tunnel connection connIndex=0 connection=82a9177b-8f9d-4175-afe5-3f1ff2568e0c event=0 ip=198.41.192.107 location=lax07 protocol=quic
2026-09-13T08:24:03Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.233
2026-09-13T08:24:03Z INF Registered tunnel connection connIndex=1 connection=fbfb4054-4737-461b-aa49-65c2539b0534 event=0 ip=198.41.200.233 location=lax01 protocol=quic
2026-09-13T08:24:04Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.200.113
2026-09-13T08:24:04Z INF Registered tunnel connection connIndex=2 connection=8101c1a4-7a9b-4fc6-be6d-e21efb777ce9 event=0 ip=198.41.200.113 location=lax01 protocol=quic
[16:24:04] === STEP 7: 持久化 ===
[16:24:06] systemd 服务已配置
[16:24:06] Cron 保活已设置
[16:24:06] === STEP 8: 验证 ===
[16:24:06] --- API (localhost:8450) ---
 OK
[16:24:06] --- cloudflared 进程 ---
root     1110458  3.0  1.9 1294676 39656 ?       Sl   16:24   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1110568  0.0  1.3 1292484 27416 ?       Rsl  16:24   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     1110570  0.0  1.3 1292484 27312 ?       Rl   16:24   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[16:24:06] --- aishield.tools ---
 OK
[16:24:07] --- DNS CNAME ---
[16:24:08] --- DNS A ---
172.67.188.44
104.21.81.46
[16:24:08] === 部署汇总 ===
[16:24:08] Tunnel Mode: cert
[16:24:08] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:24:08] API: http://localhost:8450
[16:24:08] 域名: https://aishield.tools
[16:24:08] cloudflared: /usr/local/bin/cloudflared
[16:24:08] PID: 1110458
[16:24:08] Config: /root/.cloudflared/config.yml
[16:24:08] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:24:08] 状态: Named Tunnel (cert 模式) 已配置
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Sun 2026-09-13 16:24:06 CST; 9s ago
   Main PID: 1110569 (start-tunnel.sh)
      Tasks: 9 (limit: 2216)
     Memory: 18.2M
        CPU: 149ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─1110569 /bin/bash /opt/start-tunnel.sh
             └─1110570 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
LISTEN 0      5            0.0.0.0:8450       0.0.0.0:*    users:(("python3",pid=1110067,fd=3))                                                    
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
Time: Sun Sep 13 08:24:25 UTC 2026

=== curl test (aishield.tools) ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 236, "rules_breakdown": {"static": 210, "generated": 9, "radar": 17, "total": 236}, "uptime": 1789287866.2896464, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "566d8dc160bee4b9f501f837d21733e2353f1404", "deployed_at": "2026-09-13T08:23:42Z"}
=== DNS lookup ===
104.21.81.46
172.67.188.44

=== DNS CNAME check ===
