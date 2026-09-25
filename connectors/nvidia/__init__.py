"""NVIDIA 开发者平台接入层（v4.8.2）。

封装 NGC Catalog / NIM 推理微服务 / NeMo 训练编排，所有动作经 AIShield
个人 Agent 治理层做预算/风险 preflight 与 HMAC 行动上链。

鉴权形态：NGC API Key（Bearer），非 OAuth 个人 Agent 形态；
大陆访问需 HTTPS_PROXY 走海外代理，`self_check()` 会报告当前代理状态。
"""

from .nvidia import (
    PLATFORM_ID,
    PROVIDER,
    NGC_BASE,
    NIM_BASE,
    NEMO_BASE,
    DEFAULT_REDIRECT_URI,
    store_api_key,
    get_api_key,
    register_nvidia_agent,
    preflight,
    run_agent_action,
    user_nvidia_state,
    self_check,
)

__all__ = [
    "PLATFORM_ID", "PROVIDER",
    "NGC_BASE", "NIM_BASE", "NEMO_BASE",
    "DEFAULT_REDIRECT_URI",
    "store_api_key", "get_api_key",
    "register_nvidia_agent", "preflight", "run_agent_action",
    "user_nvidia_state", "self_check",
]
