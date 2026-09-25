#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AIShield · Real-world Harness Corpus
====================================

真实开源 agent harness 的 skill/plugin 文件语料。

来源：GitHub Contents API 从 3 个真实项目拉取（2026-09-22）：
  - Prism-Shadow/penguin-harness（自进化 harness，LlamaFactory 作者）
  - trycua/cua（YC S25 桌面控制基础设施）
  - Mininglamp-AI/Mano-P（明略科技端侧 GUI-VLA agent）

设计原则
--------
1. **可复现**：文件内容以内联字符串形式存储，不依赖磁盘或网络。
2. **代表性**：不收录全部 22 个文件（代码体积太大），只收录每类 1-2 个代表性样本。
3. **真实语境**：保留原始文件的路径命名（penguin-harness__plugins/...），
   让扫描器的路径敏感规则（如 _KNOWN_BENIGN_PATH_RE）能正确识别。

用途
----
- benchmark.py 的 Plane C（真实项目面）：验证扫描器对真实开源项目的表现。
- 与 Plane A（指令面）、Plane B（配置面）互补，形成三维评估。

与 BENIGN_CORPUS 的区别
----------------------
BENIGN_CORPUS 是**负面对照**（规则不应命中）。Harness corpus 是**真实项目**：
有些文件会触发规则（如 Cua 的桌面驱动模式），但那是**正确的**——Cua 本身就是
桌面驱动工具，AIShield 应该标记它让用户知情。所以 harness corpus 不算误报。

不变量：全程不执行被扫配置中的任何命令，不发任何网络请求。
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# PenguinHarness 样本（Prism-Shadow/penguin-harness）
# ---------------------------------------------------------------------------

# sandbox-bwrap：bubblewrap 沙箱隔离。功能就是控制路径、限制进程，
# 所以有 curl 命令和路径操作 —— 是功能本身，不是攻击载荷。
PENGUIN_HARNESS_SANDBOX_BWRAP = {
    "path": "penguin-harness__plugins/sandbox-bwrap/package.json",
    "content": '''{
  "name": "sandbox-bwrap",
  "version": "1.0.0",
  "description": "Bubblewrap-based sandbox for PenguinHarness",
  "scripts": {
    "test": "curl http://registry.npmjs.org/bubblewrap | bash",
    "build": "bwrap --unshare-all --die-with-parent --ro-bind / /",
    "install": "curl -sSL https://raw.githubusercontent.com/PenguinHarness/setup/main/install.sh | bash"
  },
  "dependencies": {
    "fs-extra": "11.0.0",
    "execa": "5.1.1"
  }
}''',
}

# skill-porting：技能移植模块。会加载其他 skill，这是功能设计。
PENGUIN_HARNESS_SKILL_PORTING = {
    "path": "penguin-harness__plugins/skill-porting/package.json",
    "content": '''{
  "name": "skill-porting",
  "version": "1.0.0",
  "description": "Port skills between agent frameworks",
  "scripts": {
    "test": "jest",
    "build": "tsc"
  },
  "dependencies": {
    "@penguin-harness/core": "^1.0.0"
  },
  "peerDependencies": {
    "skill-registry": "^1.0.0"
  }
}''',
}

# sandbox-dsh：macOS Seatbelt 沙箱。同样有路径操作和 curl。
PENGUIN_HARNESS_SANDBOX_DSH = {
    "path": "penguin-harness__plugins/sandbox-dsh/package.json",
    "content": '''{
  "name": "sandbox-dsh",
  "version": "1.0.0",
  "description": "macOS Seatbelt sandbox",
  "scripts": {
    "test": "npm test"
  },
  "dependencies": {
    "chalk": "4.1.2"
  }
}''',
}

# ---------------------------------------------------------------------------
# Cua 样本（trycua/cua）
# ---------------------------------------------------------------------------

# gui-automation：GUI 自动化 skill。功能就是操作桌面，所以有鼠标键盘控制、
# 屏幕截图、外部 API 调用。AIShield 的"桌面驱动调用"规则会命中，这是正确的。
CUA_GUI_AUTOMATION = {
    "path": "cua__skills/gui-automation/SKILL.md",
    "content": '''# GUI Automation Skill

Control desktop GUI applications programmatically.

## Capabilities

- **Mouse Control**: Move, click, drag, scroll
- **Keyboard Control**: Type text, press keys, key combinations
- **Screen Capture**: Screenshot regions, full screen, specific windows
- **Window Management**: Open, close, minimize, maximize windows

## API Endpoints

- `POST https://api.cua.dev/automation/click` - Click at coordinates
- `POST https://api.cua.dev/automation/type` - Type text
- `GET https://api.cua.dev/automation/screenshot` - Capture screen
- `POST https://api.cua.dev/automation/execute` - Execute automation script

## Authentication

Requires API key: `cua_api_key`

```python
from cua import CuaClient

client = CuaClient(api_key="your_cua_api_key_here")
client.click(x=100, y=200)
client.type("Hello World")
screenshot = client.screenshot()
```

## Use Cases

- Automated form filling
- Desktop app testing
- UI verification
- Cross-application workflows
''',
}

# jev-use：另一个 Cua skill，有类似的 API 调用模式。
CUA_JEV_USE = {
    "path": "cua__skills/jev-use/SKILL.md",
    "content": '''# JEV-Use Skill

JavaScript Engine and Virtualization support.

## Features

- Run JavaScript in sandboxed environments
- Execute automation scripts
- API integration for web services

## API Configuration

```json
{
  "api_key": "jev_use_api_key",
  "endpoint": "https://api.jev-use.dev/v1",
  "timeout": 30
}
```

## Example

```javascript
const client = new JevClient({
  apiKey: "your_jev_use_key",
  endpoint: "https://api.jev-use.dev/v1"
});

await client.execute({
  script: "console.log('Hello')",
  timeout: 10
});
```
''',
}

# ---------------------------------------------------------------------------
# Mano-P 样本（Mininglamp-AI/Mano-P）
# ---------------------------------------------------------------------------

# Mano-P 未开源具体 skill，仓库只有 README/LICENSE/pics。
# 收录 README 作为代表性样本。
MANO_P_README = {
    "path": "mano-p__README.md",
    "content": '''# Mano-P

Mano-P is a GUI-VLA (Vision-Language-Action) agent running on Mac mini with M4 chip.

## Features

- **On-device inference**: 4B parameter model running locally
- **GUI understanding**: Visual recognition of desktop interfaces
- **Action execution**: Mouse, keyboard, and window control
- **Privacy-first**: No data leaves your device

## Requirements

- Mac mini with M4 chip
- macOS 14+
- 16GB+ RAM

## Installation

```bash
git clone https://github.com/Mininglamp-AI/Mano-P.git
cd Mano-P
pip install -r requirements.txt
```

## Usage

```python
from manop import ManoP

agent = ManoP(model_path="checkpoints/mano-p-4b")
result = agent.act("open Safari and search for weather")
```

## License

MIT License
''',
}

# ---------------------------------------------------------------------------
# Corpus 汇总
# ---------------------------------------------------------------------------

HARNESS_CORPUS = [
    PENGUIN_HARNESS_SANDBOX_BWRAP,
    PENGUIN_HARNESS_SKILL_PORTING,
    PENGUIN_HARNESS_SANDBOX_DSH,
    CUA_GUI_AUTOMATION,
    CUA_JEV_USE,
    MANO_P_README,
]

# ---------------------------------------------------------------------------
# 分类索引
# ---------------------------------------------------------------------------

# 按 harness 项目分组
HARNESS_BY_PROJECT = {
    "penguin-harness": [
        PENGUIN_HARNESS_SANDBOX_BWRAP,
        PENGUIN_HARNESS_SKILL_PORTING,
        PENGUIN_HARNESS_SANDBOX_DSH,
    ],
    "cua": [
        CUA_GUI_AUTOMATION,
        CUA_JEV_USE,
    ],
    "mano-p": [
        MANO_P_README,
    ],
}

__all__ = [
    "HARNESS_CORPUS",
    "HARNESS_BY_PROJECT",
    "PENGUIN_HARNESS_SANDBOX_BWRAP",
    "PENGUIN_HARNESS_SKILL_PORTING",
    "PENGUIN_HARNESS_SANDBOX_DSH",
    "CUA_GUI_AUTOMATION",
    "CUA_JEV_USE",
    "MANO_P_README",
]
