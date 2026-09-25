"""connectors — 平台接入层。

平台优先路径：
  - Meta Muse       (海外，muse.ai)
  - xAI Grok Bot    (海外，api.x.ai)
  - OpenAI Assistants / Anthropic / ChatGPT-Agent 等（后续）

大陆访问：muse.ai / api.x.ai 均不通（curl 2026-09-24 实测），
需要用户设置 HTTPS_PROXY / HTTP_PROXY 环境变量，或者在境外服务器运行。
"""
