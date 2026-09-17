# 雷达规则的 shadow / enforce 双模式与加载期字段契约

记录 2026-09-18 对 Tech Radar 闭环两处缺口的修复：

1. `scripts/promote_rule.py` 增加 `--shadow`（只观测不写入的第三档判定）与 `--strict`。
2. `scanner/rules.py` 的雷达加载器增加字段契约，坏条目进可见隔离区而不是被静默丢弃。

测试：`tests/test_promote_rule_shadow.py`（29 个）。

---

## 一、原来缺的环节

`promote_rule.py` 原先只有"干"或"不干"两种结果。闸门的三道判定里，只有前两道
（schema / 良性语料零误报）在 `--check` 里可观测：

| 判定轴 | `--check` 看得见 | `--promote-all` 落库前能挡住 |
|---|---|---|
| schema / 无 TODO / 正则可编译 / 不过宽 / 不重复 | ✅ | ✅ |
| 良性语料零误报 | ✅ | ✅ |
| 攻击语料命中（catch） | ❌ | ❌ |

第三轴 `radar_effect.evaluate()` 只在**落库之后**跑，而且它的报告是非阻断的
（`"effect measurement must never break promotion"`）。后果是一条**零命中的死规则
会直接进线上**，之后才被当成"带刺的铃铛"事后报出来。

`rule-promoter.yml` 每周期都跑一次，所以这个问题不是偶发的：候选池里混进一条
新信号推导出的死规则，它就会在没有任何人在场的情况下成为一条线上规则。

## 二、三档判定

```
promote  -- 校验通过，且在攻击语料上有命中
warn     -- 校验通过，但攻击语料上零命中（死规则）
refuse   -- 校验失败，或误报良性语料
```

`--shadow` 对每个候选给出判定，**不写任何文件**：不落 `data/radar_rules.json`、
不建快照、不写台账、不归档候选、不改写 `data/state/radar_effect.json`。
效果测量通过 `radar_effect.evaluate(store=..., save=False)` 在内存里跑。

非零退出码在**任何**候选不是 `promote` 时给出，这样它可以直接挂进 CI 当观测门：

```bash
python scripts/promote_rule.py --shadow     # 只观测，写字数 = 0
```

## 三、为什么 warn 不是硬拒绝

这是这里最容易被"加固过度"弄坏的一个决定，记录下来以免下次被改掉。

雷达候选来自**新信号**。`ATTACK_SAMPLES` 是一份固定语料，全新攻击类型**天然不
在其中**。如果 `catch == false` 直接判 refuse，那么每当雷达抓到一个新的、语料里
还没有的攻击家族，晋升循环就会静默停摆——闸门会把最该晋升的东西挡在最前面。

所以 warn 的处理是：默认放行 + 大声告警，收紧留给有上下文的人显式开启：

```bash
python scripts/promote_rule.py --promote-all           # 历史行为：死规则进线上并告警
python scripts/promote_rule.py --promote-all --strict  # 收紧：死规则拒收，退出码 1
```

`--strict` 的退出码是非零的，目的是让 CI 能看见收紧发生了，而不是悄悄少晋升。

`rule-promoter.yml` 里**故意没有**加 `--strict`。自动循环的契约是"通过六道闸门
就晋升"，改这个契约需要一个懂信号来源的人在场，不是一个 CI 配置项能决定的事。

## 四、借了什么，没借什么

双模式这个**结构**来自 TypeSafe `pi-jev` 的 gate：shadow 默认、enforce 显式开启，
一次请求带多个判定阈值。

它的默认值**没有**借。`pi-jev` 所有错误路径都是 fail-open——缺 API key、超时、
HTTP 429、响应畸形，全部放行工具调用并继续执行。本项目的公开定位是 fail-closed，
两者不能共存。所以这里的实现是：`--shadow` 失败只影响它自己的退出码，绝不降级
成放行；`--promote` / `--promote-all` 遇到不确定的判定一律拒收。

阈值表驱动的写法也借用了（`_try_promote_one` 的 code 2 / code 3 是数据不是分支），
新增一档判定是加一行映射，不是加一个 if。

## 五、加载期字段契约

`scanner/rules.py` 的雷达加载器原先是：

```python
for pattern, meta in (data.get("rules") or {}).items():
    try:
        desc, severity = meta[0], meta[1]
    except (TypeError, IndexError, KeyError):
        continue
    RADAR_RULES[pattern] = (f"[雷达] {desc}", severity)
```

三个问题：

- `except: continue` **静默丢弃**。一条坏条目从此不存在于日志里。被吞的规则等于
  不存在的规则，而报告里看不出任何差异——这是本仓库反复出现的假绿反模式。
- `severity` 完全不校验。`"catastrophic"` 会原样进线上，排序和分级全部失效。
- 正则**完全不在加载期编译**。一条写坏的正则会等到第一次扫描时才 `re.error`，
  把整次扫描打崩——数据文件的瑕疵变成了扫描器不可用。

字段契约在加载期执行，越界的条目进 `_RADAR_QUARANTINE`：

```python
scanner.rules.get_radar_load_warnings()   # {pattern: [原因, ...]}，空 dict = 干净
scanner.rules.get_radar_rules_meta()["quarantined"]
```

校验内容：`pattern` 是非空字符串；value 是长度恰好 2 的 `[描述, 严重级别]`；
描述非空且不是 TODO 占位；严重级别在 `critical/high/medium/low/info` 之内；
正则可编译且不匹配空串或平凡输入（与晋升闸门同一组过宽判据）。

隔离是**条目级**的：同文件里的一条坏条目不会拖走其它正常条目。文件整体损坏或
缺失仍走原有的静默降级（基础规则不受影响），只有条目级问题才进隔离区——那是
唯一能定位到"哪一条有问题"的粒度。

契约本身只借 RSIH Genome 的一个想法：组件字段互斥、越界写在**加载期**失败，
而不是等到运行期才炸。仓库里的 1361 行规则文件**没有**为此重构。

## 六、怎么验证

```bash
python -m unittest tests.test_promote_rule_shadow -v     # 29 个
python -m unittest tests.test_rule_promotion_rollback -v  # 快照/回滚台账不受影响
python tests/run_all.py
```

关键钉点：

- `TestShadowWritesNothing` —— shadow 的字面契约是"一个字都不写"，重复运行输出
  必须逐字一致（无副作用才可重入）。
- `TestEnforceConsultsShadow` —— 默认行为向后兼容（`rule-promoter.yml` 依赖它），
  `--strict` 拒收死规则并返回非零。
- `TestSimulateAndInMemoryEffect` —— `simulate()` 不改输入 store；
  `evaluate(store=..., save=False)` 不改写线上文件。
- `TestRadarLoadContract` —— 12 个条目级隔离用例，以及文件缺失 / 整体损坏的
  静默降级路径。

## 七、已知边界

- shadow 的攻击语料仍然是**固定**的 `ATTACK_SAMPLES`。它只能回答"这条规则在现有
  攻击样本上会不会命中"，回答不了"它会不会命中明天出现的新样本"。warn 是信息，
  不是安全保证。
- `--shadow` 与 `--check` 现在都会跑，每周期多一次语料扫描。候选池是几十条量级，
  成本可忽略；如果将来候选池涨到成千上万，需要考虑把两者的语料扫描合并成一次。
- 隔离区是**内存态**的，不持久化。`get_radar_load_warnings()` 只在同一进程内可读。
  CI 想长期留证需要自己调一次扫描器并打印，本仓库目前没有这一步。
