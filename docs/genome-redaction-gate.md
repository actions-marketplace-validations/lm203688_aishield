# Genome 分发链缺的那一环：redaction gate

记录 2026-09-18 对 CosmosMind `RSI-Harness` / **Genome** 分发链的一次外部评估。
结论：它自己声明了一个缺口，那个缺口正好是 AIShield 的主产品面。本文记录评估
结论与要做什么，**尚未实现任何代码**。

---

## 一、Genome 是什么

Genome 是 RSI-Harness 的载体格式：一个目录，装下某个 RSI 实验的全部可复现状态。
官方定义是「harness + data + model + 元数据」的打包单元，用来把一次 RSI 运行的
结果传给另一次运行——论文、代码、权重、日志一起分发，接收方不必重建环境。

它的定位是**分发格式**，不是运行时。这意味着它天然要经过别人的机器，而别人机器
上跑什么、会不会把内容带出内网，是格式本身管不了的事。

## 二、它自己声明的缺口

`RSI-Harness` 的 README 在「Known gaps」一节写了一句：

> There is no pre-publish redaction gate either — a Genome is distilled from
> private transcripts, and before sharing it must be able to flag absolute paths,
> intranet domains, and likely secrets.

拆成三件具体的事：

| 缺口 | 具体要拦什么 |
|---|---|
| 发布前脱敏 | Genome 是从私有 transcript 蒸馏出来的，里面会残留原始路径、域名、凭据 |
| 绝对路径 | `/root/user/projects/x` 之类，泄露目录结构与主机拓扑 |
| 内网域名 | `*.corp.internal`、`10.x.x.x`、`192.168.x.x`，泄露网络边界 |
| 疑似密钥 | 高熵字符串、`sk-...`、`AKIA...` 之类前缀特征 |

注意这句话的主语是 **Genome**，不是 RSI-Harness 本体。也就是说这个缺口在官方
仓库里已经被认账，但**没人填**——它不在任何已知路线图项上。

## 三、AIShield 的位置

这条缺口和 AIShield 现有产品面的对应关系是直接的：

| Genome 需要的 | AIShield 已有的 |
|---|---|
| 发布前扫描 | `scanner/scan()` 整仓扫描，输出 SARIF/JSON |
| 密钥检测 | `MCP01` 类别规则 + 高熵检测 |
| 内网地址识别 | `scanner/rules.py` 里的私网段与内网域名规则 |
| 结构化结果给 CI 消费 | SARIF + `exit_code`，fail-closed |
| 可当闸门挂 CI | `--shadow` / 非零退出码（见 `docs/radar-shadow-gate.md`） |

换句话说 AIShield 今天就能跑一遍 Genome 目录并把这三类问题报出来。缺的不是检测
能力，是**面向 Genome 的适配层**：知道哪些字段是文本内容、哪些是二进制要跳过、
哪些路径是格式自身必需因而应当白名单。

## 四、要做成什么

一个 `--genome` 模式或独立的 `scripts/genome_gate.py`，输入一个 Genome 目录，
输出「能不能发」。最小闭环：

1. **遍历** Genome 目录，按扩展名分流：`.py / .md / .json / .yaml / .txt` 走文本
   扫描；`.pth / .pt / .safetensors / .bin / .npy` 走哈希记录（只记指纹不读内容，
   也避免大文件拖慢闸门）。
2. **三类命中**分别上报：绝对路径、内网地址、疑似密钥。密钥命中必须给出行号与
   脱敏后的前后文片段，否则接收方无从判断是误报还是真泄露。
3. **格式必需白名单**。Genome 的清单文件本身会引用相对路径，`.gitignore` 式的路
   径模式不是泄露。这一层要显式声明，否则会退化成"报了一堆没法修的误报"。
4. **fail-closed + 明确退出码**，可直接挂进发布流水线。

第 3 步是这里唯一的真难点，也是不能跳的一步：不做白名单，闸门的第一次上线就会被
误报淹没，然后被加 `|| true` 关掉。

## 五、明确不做什么

- **不实现 Genome 格式本身**。它是 RSI-Harness 的产物，有自己的规范与兼容矩阵；
  AIShield 只做消费侧的闸门。
- **不把 RSI-Harness 的代码搬进来**。它带自己的运行时依赖，AIShield 保持零第三方
  依赖（`requirements.txt` 只有 pytest 一项，仅测试用）。
- **不在本机搭 Genome 实验**。本机是 Windows + WorkBuddy 沙箱，`bash` shim 是坏的
  （`dirname` / `cd` / `head` 都不可用），而且没有 RSI-Harness 的运行环境。适配层
  可以先靠 fixture 目录开发，不需要真的跑一个 RSI 实验。
- **不承诺 Genome 白名单规则的完备性**。它随 Genome 规范演进，第一次接入前必须
  拿一个真实 Genome 样本校准，否则白名单是猜的。

## 六、评估时确认过的边界条件

- 本机**无法**直接验证 Genome 的真实目录结构。本文对 Genome 布局的描述来自 RSI-
  Harness 的公开 README，**没有**在本地或 CI 上验证过。写第 1 步的分流规则前，
  需要拿到一个真实样本或一份确切的文件清单。
- RSI-Harness 的许可条款未在本文核过。要做消费侧集成（读它的目录结构）不涉及代码
  复用，但发布一个宣称兼容某格式的闸门属于公开声明，**上线前必须**确认许可与
  命名是否允许。
- "已知缺口无人填"这个判断只对**评估时点**成立。RSI-Harness 是活跃项目，接入前
  应复查一次该 README 段落是否已经消失。
