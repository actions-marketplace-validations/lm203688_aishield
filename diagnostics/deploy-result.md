=== DIAGNOSTIC ===
Time: Thu Sep 17 04:43:35 PM CST 2026
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
FAIL
=== CLOUDFLARED PROCESS ===
root      689487  0.8  1.9 1294676 38616 ?       Sl   16:43   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root      689585  1.2  1.9 1294676 39748 ?       Ssl  16:43   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root      689587  1.1  1.9 1294676 39664 ?       Sl   16:43   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-17T08:43:21Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.113
2026-09-17T08:43:22Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.192.7
2026-09-17T08:43:22Z INF Registered tunnel connection connIndex=1 connection=181c03d3-a5a4-4b5d-b4ba-47d062709c5f event=0 ip=198.41.200.113 location=lax01 protocol=quic
2026-09-17T08:43:23Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.200.43
2026-09-17T08:43:23Z INF Registered tunnel connection connIndex=2 connection=f8a183b2-573e-413d-9fc4-8dd3c1f4a793 event=0 ip=198.41.192.7 location=lax10 protocol=quic
2026-09-17T08:43:23Z INF Registered tunnel connection connIndex=3 connection=c39a2520-e5ff-4dd8-b8a3-90c35d3fb066 event=0 ip=198.41.200.43 location=lax01 protocol=quic
2026-09-17T08:43:26Z ERR  error="Unable to reach the origin service. The service may be down or it may not be responding to traffic from cloudflared: dial tcp 127.0.0.1:8450: connect: connection refused" connIndex=3 event=1 ingressRule=0 originService=http://localhost:8450
2026-09-17T08:43:26Z ERR Request failed error="Unable to reach the origin service. The service may be down or it may not be responding to traffic from cloudflared: dial tcp 127.0.0.1:8450: connect: connection refused" connIndex=3 dest=https://aishield.tools/api/v1/health event=0 ip=198.41.200.43 type=http
2026-09-17T08:43:28Z INF +-------------------------------------------------------------------------------------+
2026-09-17T08:43:28Z INF |                               CONNECTIVITY PRE-CHECKS                               |
2026-09-17T08:43:28Z INF +-------------------------------------------------------------------------------------+
2026-09-17T08:43:28Z INF |  COMPONENT         TARGET                     STATUS  DETAILS                       |
2026-09-17T08:43:28Z INF |  DNS Resolution    region1.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-17T08:43:28Z INF |  DNS Resolution    region2.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-17T08:43:28Z INF |  UDP Connectivity  region1.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-17T08:43:28Z INF |  UDP Connectivity  region2.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-17T08:43:28Z INF |  TCP Connectivity  region1.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-17T08:43:28Z INF |  TCP Connectivity  region2.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-17T08:43:28Z INF |  Cloudflare API    api.cloudflare.com:443     PASS    API is reachable              |
2026-09-17T08:43:28Z INF |                                                                                     |
2026-09-17T08:43:28Z INF |  SUMMARY: Environment is healthy. cloudflared will use 'quic' as primary protocol.  |
2026-09-17T08:43:28Z INF +-------------------------------------------------------------------------------------+
2026-09-17T08:43:28Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=742e4388-e53a-4c68-bc89-2c06175d4f24 status=pass target=region1.v2.argotunnel.com
2026-09-17T08:43:28Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=742e4388-e53a-4c68-bc89-2c06175d4f24 status=pass target=region2.v2.argotunnel.com
2026-09-17T08:43:28Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=742e4388-e53a-4c68-bc89-2c06175d4f24 status=pass target=region1.v2.argotunnel.com
2026-09-17T08:43:28Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=742e4388-e53a-4c68-bc89-2c06175d4f24 status=pass target=region2.v2.argotunnel.com
2026-09-17T08:43:28Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=742e4388-e53a-4c68-bc89-2c06175d4f24 status=pass target=region1.v2.argotunnel.com
2026-09-17T08:43:28Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=742e4388-e53a-4c68-bc89-2c06175d4f24 status=pass target=region2.v2.argotunnel.com
2026-09-17T08:43:28Z INF precheck component="Cloudflare API" details="API is reachable" run_id=742e4388-e53a-4c68-bc89-2c06175d4f24 status=pass target=api.cloudflare.com:443
2026-09-17T08:43:28Z INF precheck complete hard_fail=false run_id=742e4388-e53a-4c68-bc89-2c06175d4f24 suggested_protocol=quic
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[16:42:53] Time: Thu Sep 17 04:42:53 PM CST 2026
[16:42:53] User: root (UID: 0)
[16:42:53] === STEP 1: 启动 API (端口 8450) ===
[16:42:53] 代码由 runner tarball 投递，权威 sha=830d3c32
[16:42:53] commit 对比: 运行进程=f65e49865b9548340080319655a8fae50bff5b74 / 磁盘=830d3c3274419132bd96ab70e3557ad27175bdcb
[16:42:53] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[16:42:53] 需要重新加载代码 -> 重启 API
[16:42:53] 强制重启 Python API 进程（当前commit=f65e49865b9548340080319655a8fae50bff5b74 目标=830d3c3274419132bd96ab70e3557ad27175bdcb）
[16:43:03] API 状态: FAIL - 尝试查看日志
[16:43:03] === STEP 2: 安装 cloudflared ===
[16:43:03] cloudflared 安装路径: /usr/local/bin/cloudflared
[16:43:04] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:43:04] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[16:43:04] === STEP 3: 检查认证方式 ===
[16:43:04] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[16:43:04] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[16:43:04] 检查现有 tunnel...
[16:43:05] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS                                 
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax08, 1xlax09, 1xlax10, 1xlax11 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                                             
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                                             
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 1xlax07, 1xlax09                   
[16:43:05] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:43:05] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[16:43:05] 凭证文件存在
[16:43:05] 创建 config.yml...
[16:43:05] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[16:43:05] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:43:14] DNS 路由结果: 2026-09-17T08:43:14Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[16:43:14] === STEP 5: 更新 DNS (API) ===
[16:43:14] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:43:16] 创建新 DNS CNAME 记录...
DNS 创建失败: [{"code": 9106, "message": "Missing X-Auth-Key, X-Auth-Email or Authorization headers"}]
[16:43:17] 设置 SSL 模式为 Full...
SSL: 跳过
[16:43:17] === STEP 6: 启动 Tunnel ===
[16:43:20] 启动 Named Tunnel (cert 模式)...
[16:43:20] 使用 config: /root/.cloudflared/config.yml
[16:43:20] cloudflared PID: 689487
[16:43:22] Tunnel 连接已建立!
[16:43:22] --- cloudflared 日志 (最后 15 行) ---
2026-09-17T08:43:20Z INF GOOS: linux, GOVersion: go1.26.4, GoArch: amd64
2026-09-17T08:43:20Z INF Settings: map[config:/root/.cloudflared/config.yml cred-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json credentials-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json]
2026-09-17T08:43:20Z INF cloudflared will not automatically update if installed by a package manager.
2026-09-17T08:43:20Z INF Generated Connector ID: d9d9be58-bfe7-46a9-b463-23d740e9f3a6
2026-09-17T08:43:20Z INF Initial protocol quic
2026-09-17T08:43:20Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-17T08:43:20Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-17T08:43:20Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-17T08:43:20Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-17T08:43:20Z INF Starting metrics server on 127.0.0.1:20241/metrics
2026-09-17T08:43:20Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.192.107
2026-09-17T08:43:21Z INF Registered tunnel connection connIndex=0 connection=471a59b7-e3b5-45a0-8f17-33c06e9ab419 event=0 ip=198.41.192.107 location=lax09 protocol=quic
2026-09-17T08:43:21Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.113
2026-09-17T08:43:22Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.192.7
2026-09-17T08:43:22Z INF Registered tunnel connection connIndex=1 connection=181c03d3-a5a4-4b5d-b4ba-47d062709c5f event=0 ip=198.41.200.113 location=lax01 protocol=quic
[16:43:22] === STEP 7: 持久化 ===
[16:43:23] systemd 服务已配置
[16:43:23] Cron 保活已设置
[16:43:23] === STEP 8: 验证 ===
[16:43:23] --- API (localhost:8450) ---
 FAIL
[16:43:23] --- cloudflared 进程 ---
root      689487  3.0  1.9 1294676 39664 ?       Sl   16:43   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root      689585  0.0  1.3 1292484 27672 ?       Rsl  16:43   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root      689587  0.0  1.3 1292740 27528 ?       Rl   16:43   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[16:43:23] --- aishield.tools ---
 FAIL (DNS 传播中或配置错误)
[16:43:26] --- DNS CNAME ---
[16:43:27] --- DNS A ---
172.67.188.44
104.21.81.46
[16:43:27] === 部署汇总 ===
[16:43:27] Tunnel Mode: cert
[16:43:27] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[16:43:27] API: http://localhost:8450
[16:43:27] 域名: https://aishield.tools
[16:43:27] cloudflared: /usr/local/bin/cloudflared
[16:43:27] PID: 689487
[16:43:27] Config: /root/.cloudflared/config.yml
[16:43:27] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[16:43:27] 状态: Named Tunnel (cert 模式) 已配置
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Thu 2026-09-17 16:43:23 CST; 11s ago
   Main PID: 689586 (start-tunnel.sh)
      Tasks: 9 (limit: 2216)
     Memory: 18.7M
        CPU: 146ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─689586 /bin/bash /opt/start-tunnel.sh
             └─689587 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
NO PORTS
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
Time: Thu Sep 17 08:43:48 UTC 2026

=== curl test (aishield.tools) ===
error code: 502

=== DNS lookup ===
104.21.81.46
172.67.188.44

=== DNS CNAME check ===
