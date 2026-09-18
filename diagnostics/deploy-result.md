=== DIAGNOSTIC ===
Time: Fri Sep 18 09:14:12 AM CST 2026
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
root     1333232  0.8  1.2 1360284 24204 ?       Sl   09:13   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1333338  1.1  1.3 1360284 26860 ?       Ssl  09:13   0:00 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-18T01:13:57Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.192.47
2026-09-18T01:13:58Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.192.57
2026-09-18T01:13:58Z INF Registered tunnel connection connIndex=1 connection=cb87f508-b23c-4933-bcaa-f8d399d8b5e9 event=0 ip=198.41.192.47 location=lax05 protocol=quic
2026-09-18T01:13:59Z INF Registered tunnel connection connIndex=2 connection=df0d84bc-adc6-4056-b0e7-dadf87a09471 event=0 ip=198.41.192.57 location=lax08 protocol=quic
2026-09-18T01:13:59Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.200.63
2026-09-18T01:14:00Z INF Registered tunnel connection connIndex=3 connection=e99e5069-31fb-4824-89f6-dbf5ab1ad7eb event=0 ip=198.41.200.63 location=lax01 protocol=quic
2026-09-18T01:14:01Z ERR  error="Unable to reach the origin service. The service may be down or it may not be responding to traffic from cloudflared: dial tcp 127.0.0.1:8450: connect: connection refused" connIndex=1 event=1 ingressRule=0 originService=http://localhost:8450
2026-09-18T01:14:01Z ERR Request failed error="Unable to reach the origin service. The service may be down or it may not be responding to traffic from cloudflared: dial tcp 127.0.0.1:8450: connect: connection refused" connIndex=1 dest=https://aishield.tools/api/v1/health event=0 ip=198.41.192.47 type=http
2026-09-18T01:14:03Z INF +-------------------------------------------------------------------------------------+
2026-09-18T01:14:03Z INF |                               CONNECTIVITY PRE-CHECKS                               |
2026-09-18T01:14:03Z INF +-------------------------------------------------------------------------------------+
2026-09-18T01:14:03Z INF |  COMPONENT         TARGET                     STATUS  DETAILS                       |
2026-09-18T01:14:03Z INF |  DNS Resolution    region1.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-18T01:14:03Z INF |  DNS Resolution    region2.v2.argotunnel.com  PASS    DNS Resolved successfully     |
2026-09-18T01:14:03Z INF |  UDP Connectivity  region1.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-18T01:14:03Z INF |  UDP Connectivity  region2.v2.argotunnel.com  PASS    QUIC connection successful    |
2026-09-18T01:14:03Z INF |  TCP Connectivity  region1.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-18T01:14:03Z INF |  TCP Connectivity  region2.v2.argotunnel.com  PASS    HTTP/2 connection successful  |
2026-09-18T01:14:03Z INF |  Cloudflare API    api.cloudflare.com:443     PASS    API is reachable              |
2026-09-18T01:14:03Z INF |                                                                                     |
2026-09-18T01:14:03Z INF |  SUMMARY: Environment is healthy. cloudflared will use 'quic' as primary protocol.  |
2026-09-18T01:14:03Z INF +-------------------------------------------------------------------------------------+
2026-09-18T01:14:03Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=a286ba1f-98ff-41f0-8352-45253c66827f status=pass target=region1.v2.argotunnel.com
2026-09-18T01:14:03Z INF precheck component="DNS Resolution" details="DNS Resolved successfully" run_id=a286ba1f-98ff-41f0-8352-45253c66827f status=pass target=region2.v2.argotunnel.com
2026-09-18T01:14:03Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=a286ba1f-98ff-41f0-8352-45253c66827f status=pass target=region1.v2.argotunnel.com
2026-09-18T01:14:03Z INF precheck component="UDP Connectivity" details="QUIC connection successful" run_id=a286ba1f-98ff-41f0-8352-45253c66827f status=pass target=region2.v2.argotunnel.com
2026-09-18T01:14:03Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=a286ba1f-98ff-41f0-8352-45253c66827f status=pass target=region1.v2.argotunnel.com
2026-09-18T01:14:03Z INF precheck component="TCP Connectivity" details="HTTP/2 connection successful" run_id=a286ba1f-98ff-41f0-8352-45253c66827f status=pass target=region2.v2.argotunnel.com
2026-09-18T01:14:03Z INF precheck component="Cloudflare API" details="API is reachable" run_id=a286ba1f-98ff-41f0-8352-45253c66827f status=pass target=api.cloudflare.com:443
2026-09-18T01:14:03Z INF precheck complete hard_fail=false run_id=a286ba1f-98ff-41f0-8352-45253c66827f suggested_protocol=quic
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[09:14:07] Time: Fri Sep 18 09:14:07 AM CST 2026
[09:14:07] User: root (UID: 0)
[09:14:07] === STEP 1: 启动 API (端口 8450) ===
[09:14:07] 代码由 runner tarball 投递，权威 sha=bdd01c19
[09:14:07] commit 对比: 运行进程=none / 磁盘=bdd01c19c86f207485eb5b834157d9cc5ff3ae72
[09:14:07] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[09:14:07] 需要重新加载代码 -> 重启 API
[09:14:09] systemd 服务 aishield-api 已安装（Restart=always，WorkingDirectory=/opt/aishield）
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Fri 2026-09-18 09:13:59 CST; 13s ago
   Main PID: 1333365 (start-tunnel.sh)
      Tasks: 2 (limit: 2216)
     Memory: 3.3M
        CPU: 45ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─1333365 /bin/bash /opt/start-tunnel.sh
             └─1334228 sleep 3
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

# 【2026-09-18】隧道起来不等于 API 在监听。Cloudflare 转发到 localhost:8450，
# 若该端口无进程，域名只会稳定返回 502（09-17~09-18 线上连续失活即此路径：
# cloudflared 存活、API 未监听）。开机/重启后先确保 API 就绪再放行隧道。
if ! curl -sf --max-time 5 http://127.0.0.1:8450/api/v1/health >/dev/null 2>&1; then
    if systemctl is-active aishield-api >/dev/null 2>&1; then
        systemctl restart aishield-api 2>/dev/null || true
    elif systemctl is-enabled aishield-api >/dev/null 2>&1; then
        systemctl start aishield-api 2>/dev/null || true
    elif [ -f /opt/aishield/api/server.py ]; then
        (cd /opt/aishield && PORT=8450 nohup python3 api/server.py >> /tmp/aishield-api.log 2>&1 &)
    elif [ -f "$HOME/aishield/api/server.py" ]; then
        (cd "$HOME/aishield" && PORT=8450 nohup python3 api/server.py >> /tmp/aishield-api.log 2>&1 &)
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
Time: Fri Sep 18 01:14:25 UTC 2026

=== curl test (aishield.tools) ===
error code: 502

=== DNS lookup ===
172.67.188.44
104.21.81.46

=== DNS CNAME check ===
