=== DIAGNOSTIC ===
Time: Sat Sep 19 10:03:47 PM CST 2026
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
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 235, "rules_breakdown": {"static": 208, "generated": 8, "radar": 19, "total": 235}, "uptime": 1789826627.8994331, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "c133bbedbdfeb51c6325290ab376fe7030997a1f", "deployed_at": "2026-09-19T14:03:08Z"}OK
=== CLOUDFLARED PROCESS ===
root     1335051  0.1  1.0 1294932 21832 ?       Sl   Sep18   3:27 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1335162  0.1  1.0 1294676 20824 ?       Ssl  Sep18   3:27 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     2786405  0.8  1.9 1294420 38804 ?       Sl   22:03   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== CLOUDFLARED LOG (last 30 lines) ===
2026-09-19T14:03:27Z INF Registered tunnel connection connIndex=1 connection=b3f342ed-0667-430d-85f7-d7dce23e7e12 event=0 ip=198.41.200.233 location=lax01 protocol=quic
2026-09-19T14:03:28Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.192.107
2026-09-19T14:03:29Z INF Registered tunnel connection connIndex=2 connection=8d39cff1-41cf-40ba-bfd5-77384469efd2 event=0 ip=198.41.192.107 location=lax07 protocol=quic
2026-09-19T14:03:29Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=3 event=0 ip=198.41.200.33
2026-09-19T14:03:29Z INF Initiating graceful shutdown due to signal terminated ...
2026-09-19T14:03:29Z ERR failed to run the datagram handler error="Application error 0x0 (remote)" connIndex=1 event=0 ip=198.41.200.233
2026-09-19T14:03:29Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=1 event=0 ip=198.41.200.233
2026-09-19T14:03:29Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=1 event=0 ip=198.41.200.233
2026-09-19T14:03:29Z INF Retrying connection in up to 1s connIndex=1 event=0 ip=198.41.200.233
2026-09-19T14:03:29Z ERR failed to run the datagram handler error="context canceled" connIndex=0 event=0 ip=198.41.192.27
2026-09-19T14:03:29Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=0 event=0 ip=198.41.192.27
2026-09-19T14:03:29Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=0 event=0 ip=198.41.192.27
2026-09-19T14:03:29Z INF Retrying connection in up to 1s connIndex=0 event=0 ip=198.41.192.27
2026-09-19T14:03:29Z ERR failed to run the datagram handler error="context canceled" connIndex=2 event=0 ip=198.41.192.107
2026-09-19T14:03:29Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=2 event=0 ip=198.41.192.107
2026-09-19T14:03:29Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=2 event=0 ip=198.41.192.107
2026-09-19T14:03:29Z INF Retrying connection in up to 1s connIndex=2 event=0 ip=198.41.192.107
2026-09-19T14:03:29Z INF Registered tunnel connection connIndex=3 connection=649afc8e-edc8-4372-a1f6-25f4e866c3e6 event=0 ip=198.41.200.33 location=lax01 protocol=quic
2026-09-19T14:03:30Z ERR failed to run the datagram handler error="context canceled" connIndex=3 event=0 ip=198.41.200.33
2026-09-19T14:03:30Z ERR failed to serve tunnel connection error="accept stream listener encountered a failure while serving" connIndex=3 event=0 ip=198.41.200.33
2026-09-19T14:03:30Z ERR Serve tunnel error error="accept stream listener encountered a failure while serving" connIndex=3 event=0 ip=198.41.200.33
2026-09-19T14:03:30Z INF Retrying connection in up to 1s connIndex=3 event=0 ip=198.41.200.33
2026-09-19T14:03:30Z ERR Connection terminated connIndex=1
2026-09-19T14:03:30Z ERR Connection terminated connIndex=0
2026-09-19T14:03:30Z ERR Connection terminated connIndex=2
2026-09-19T14:03:30Z ERR Connection terminated connIndex=3
2026-09-19T14:03:30Z ERR no more connections active and exiting
2026-09-19T14:03:30Z INF Tunnel server stopped
2026-09-19T14:03:30Z INF Metrics server stopped
2026-09-19T14:03:30Z ERR icmp router terminated error="context canceled"
=== DEPLOY LOG ===
=== AIShield Named Tunnel Deployment ===
[22:03:08] Time: Sat Sep 19 10:03:08 PM CST 2026
[22:03:08] User: root (UID: 0)
[22:03:08] === STEP 1: 启动 API (端口 8450) ===
[22:03:08] 代码由 runner tarball 投递，权威 sha=c133bbed
[22:03:09] commit 对比: 运行进程=03db3ccb2046dcab94e53e30a8f6084f2fa698e6 / 磁盘=c133bbedbdfeb51c6325290ab376fe7030997a1f
[22:03:09] 运行进程落后于磁盘代码（commit 不一致）-> 标记重启
[22:03:09] 需要重新加载代码 -> 重启 API
[22:03:10] systemd 服务 aishield-api 已安装（Restart=always，WorkingDirectory=/opt/aishield）
[22:03:16] API 状态: OK（第 1 轮验证通过）
[22:03:16] === STEP 2: 安装 cloudflared ===
[22:03:16] cloudflared 安装路径: /usr/local/bin/cloudflared
[22:03:16] cloudflared 已安装: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[22:03:16] cloudflared 版本: cloudflared version 2026.7.3 (built 2026-07-23-09:58 UTC)
[22:03:16] === STEP 3: 检查认证方式 ===
[22:03:16] cert.pem 存在: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
[22:03:16] === STEP 4: 使用 cert.pem 创建 Named Tunnel ===
[22:03:16] 检查现有 tunnel...
[22:03:17] 现有 tunnel 列表:
You can obtain more detailed information for each tunnel with `cloudflared tunnel info <name/uuid>`
ID                                   NAME              CREATED              CONNECTIONS                                 
0c39bcfb-0c96-4858-9025-d54131e062ec aishield-tunnel   2026-07-30T23:21:20Z 4xlax01, 1xlax05, 1xlax07, 1xlax08, 1xlax10 
a956a3fe-ad15-4f1e-8499-8dad27859d3d aishield.tools    2026-06-27T14:20:27Z                                             
aa3f86b8-01f4-4ce0-83a8-5512219f9003 healthlens        2026-07-28T03:03:32Z                                             
772e48b6-fec9-4295-9816-92f6479e823d healthlens-tunnel 2026-09-02T00:32:00Z 2xlax01, 1xlax09, 1xlax11                   
2026-09-19T14:03:17Z WRN Your version 2026.7.3 is outdated. We recommend upgrading it to 2026.9.1
[22:03:17] Tunnel 已存在: 0c39bcfb-0c96-4858-9025-d54131e062ec
[22:03:17] 凭证文件: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json
[22:03:17] 凭证文件存在
[22:03:17] 创建 config.yml...
[22:03:17] config.yml 已创建:
tunnel: 0c39bcfb-0c96-4858-9025-d54131e062ec
credentials-file: /root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json

ingress:
  - hostname: aishield.tools
    service: http://localhost:8450
  - service: http_status:404
[22:03:17] 路由 DNS: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[22:03:20] DNS 路由结果: 2026-09-19T14:03:20Z INF aishield.tools.healthlens.cc is already configured to route to your tunnel tunnelID=0c39bcfb-0c96-4858-9025-d54131e062ec
[22:03:20] === STEP 5: 更新 DNS (API) ===
[22:03:20] CNAME: aishield.tools -> 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[22:03:21] 创建新 DNS CNAME 记录...
DNS 创建失败: [{"code": 9106, "message": "Missing X-Auth-Key, X-Auth-Email or Authorization headers"}]
[22:03:22] 设置 SSL 模式为 Full...
SSL: 跳过
[22:03:23] === STEP 6: 启动 Tunnel ===
[22:03:23] systemd 托管中 -> systemctl stop cloudflared-tunnel
[22:03:27] 启动 Named Tunnel (cert 模式)...
[22:03:27] 使用 config: /root/.cloudflared/config.yml
[22:03:27] cloudflared PID: 2786265
[22:03:29] Tunnel 连接已建立!
[22:03:29] --- cloudflared 日志 (最后 15 行) ---
2026-09-19T14:03:27Z INF GOOS: linux, GOVersion: go1.26.4, GoArch: amd64
2026-09-19T14:03:27Z INF Settings: map[config:/root/.cloudflared/config.yml cred-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json credentials-file:/root/.cloudflared/0c39bcfb-0c96-4858-9025-d54131e062ec.json]
2026-09-19T14:03:27Z INF cloudflared will not automatically update if installed by a package manager.
2026-09-19T14:03:27Z INF Generated Connector ID: f89c5d17-82a9-4b2b-af28-0798841f478f
2026-09-19T14:03:27Z INF Initial protocol quic
2026-09-19T14:03:27Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-19T14:03:27Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-19T14:03:27Z INF ICMP proxy will use 10.0.0.11 as source for IPv4
2026-09-19T14:03:27Z INF ICMP proxy will use fe80::5054:ff:fe13:e120 in zone eth0 as source for IPv6
2026-09-19T14:03:27Z INF Starting metrics server on 127.0.0.1:20242/metrics
2026-09-19T14:03:27Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=0 event=0 ip=198.41.192.27
2026-09-19T14:03:27Z INF Registered tunnel connection connIndex=0 connection=de6d680c-1f41-441d-b93b-d630c42f0f6f event=0 ip=198.41.192.27 location=lax08 protocol=quic
2026-09-19T14:03:27Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=1 event=0 ip=198.41.200.233
2026-09-19T14:03:27Z INF Registered tunnel connection connIndex=1 connection=b3f342ed-0667-430d-85f7-d7dce23e7e12 event=0 ip=198.41.200.233 location=lax01 protocol=quic
2026-09-19T14:03:28Z INF Tunnel connection curve preferences: [X25519MLKEM768 CurveID(65074) CurveP256] connIndex=2 event=0 ip=198.41.192.107
[22:03:29] === STEP 7: 持久化 ===
[22:03:29] 停止 nohup cloudflared (PID 2786265) -> 交由 systemd 单实例托管
[22:03:31] systemd 服务已配置
[22:03:31] Cron 保活已设置（以本项目 API 健康为判据，不被他项目 tunnel 假满足）
[22:03:31] === STEP 8: 验证 ===
[22:03:31] --- API (localhost:8450) ---
 OK
[22:03:31] --- cloudflared 进程 ---
root     1335051  0.1  1.0 1294932 22044 ?       Sl   Sep18   3:27 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
root     1335162  0.1  1.0 1294676 20976 ?       Ssl  Sep18   3:27 /usr/local/bin/cloudflared --config /etc/cloudflared-healthlens/config.yml tunnel --metrics 127.0.0.1:8099 run
root     2786405  0.0  1.3 1292484 27428 ?       Sl   22:03   0:00 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
[22:03:31] --- aishield.tools ---
 OK
[22:03:34] --- DNS CNAME ---
[22:03:34] --- DNS A ---
104.21.81.46
172.67.188.44
[22:03:34] === 部署汇总 ===
[22:03:34] Tunnel Mode: cert
[22:03:34] Tunnel ID: 0c39bcfb-0c96-4858-9025-d54131e062ec
[22:03:34] API: http://localhost:8450
[22:03:34] 域名: https://aishield.tools
[22:03:34] cloudflared: /usr/local/bin/cloudflared
[22:03:34] PID: 2786265
[22:03:34] Config: /root/.cloudflared/config.yml
[22:03:34] CNAME: 0c39bcfb-0c96-4858-9025-d54131e062ec.cfargotunnel.com
[22:03:34] 状态: Named Tunnel (cert 模式) 已配置
[22:03:34] EXIT 0: API 健康
=== TUNNEL INFO ===
Tunnel ID: NOT SET
Token File: NOT SET
cert.pem: -rw------- 1 root root 282 Jul 28 11:02 /root/.cloudflared/cert.pem
=== SYSTEMD STATUS ===
● cloudflared-tunnel.service - Cloudflare Named Tunnel for AIShield
     Loaded: loaded (/etc/systemd/system/cloudflared-tunnel.service; enabled; vendor preset: enabled)
     Active: active (running) since Sat 2026-09-19 22:03:31 CST; 16s ago
   Main PID: 2786385 (start-tunnel.sh)
      Tasks: 9 (limit: 2216)
     Memory: 18.0M
        CPU: 154ms
     CGroup: /system.slice/cloudflared-tunnel.service
             ├─2786385 /bin/bash /opt/start-tunnel.sh
             └─2786405 /usr/local/bin/cloudflared tunnel --config /root/.cloudflared/config.yml run
=== PORTS ===
LISTEN 0      5            0.0.0.0:8450       0.0.0.0:*    users:(("python3",pid=2785951,fd=3))                                                    
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
Time: Sat Sep 19 14:04:10 UTC 2026

=== curl test (aishield.tools) ===
{"status": "ok", "version": "4.3.0", "owasp_standard": "OWASP MCP Top 10 (2025 v0.1)", "rules_count": 235, "rules_breakdown": {"static": 208, "generated": 8, "radar": 19, "total": 235}, "uptime": 1789826651.0818362, "agent_first": true, "openapi": "/openapi.json", "agent_setup": "/api/v1/agent/setup", "commit": "c133bbedbdfeb51c6325290ab376fe7030997a1f", "deployed_at": "2026-09-19T14:03:08Z"}
=== DNS lookup ===
172.67.188.44
104.21.81.46

=== DNS CNAME check ===
