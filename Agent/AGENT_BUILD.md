# HT-Researcher 智能体搭建说明

> 这份文档回答三件事：我们怎么改造 Moonshine、核心文件各干什么、以及怎么把它跑起来。
> 面向展示与交接，不替代代码注释。

---

## 1 一句话定位

在 [Moonshine](../../Moonshine-main) 的研究循环上，叠加一层**领域判定与证据层**，得到一个专门攻击
“包含概率一致是否能决定 HT 极限律”这一统计猜想的智能体：`HT-Researcher`。

代码在 `Stastistics/`，运行数据在 `moonshine-data/`，成稿归档到项目输出目录。

---

## 2 底座与改造原则

### 2.1 保留的 Moonshine 机制

- 研究循环（活动机、`run_research_autopilot_events`）；
- 项目记忆（`research_log`、`by_type`、`query_memory`）；
- 工具注册表（Markdown 定义 + handler + schema）；
- skill / agent 加载机制；
- `run_python_script` 沙箱（30s / 120s 上限）；
- 项目 workspace 与归档。

### 2.2 改造原则

- **不重写循环**：循环是通用骨架，稳定；领域差异放在 skill、工具、判定层。
- **领域层重写**：skill 内容、agent 行为准则、活动绑定、失败可见性、评审顺序都按统计研究改写。
- **判定与证据叠加**：精确工具 + 确定性门禁 + 陈述账本 + 成稿流水线。

### 2.3 三类改动

| 类别 | 内容 |
|---|---|
| 改写（动到 Moonshine 行为） | skill 内容、agent 定义、活动绑定、`record_failed_path` 可见性、`verify_overall` 之前的门禁接线 |
| 叠加（新增能力） | 18 个精确工具、`ht_verify_bundle`、`claim_id`、陈述账本、LaTeX 流水线、in-place 安装器 |
| 保留（未动） | 研究循环、项目记忆、工具注册表机制、skill/agent 加载、`run_python_script` |

---

## 3 改造点逐条

### 3.1 确定性门禁 `ht_verify_bundle`

- 输入：一个 bundle（设计、包含概率、总体、SRSWOR 侧数字、目标律）。
- 输出：`overall: PASS/FAIL`、逐项检查结果、`claim_id`（spec 哈希）。
- 定位：在 LLM 的 `verify_overall` **之前**执行，一票否决；两者冲突判 `inconclusive`。
- 目的：算术错误不会被“读起来合理”的散文放过。

### 3.2 精确工具层（18 个）

全部基于 `fractions.Fraction`，覆盖证明链的每一步：

- 设计构造与强度：射影平面、Hadamard 3-设计、`AG(m,2)` 平面、仿射超平面；
- 包含概率：逐子集、逐阶，与 SRSWOR 对比；
- 线性代数：`A y = w` 反解、`rank` 与 `augmented_rank`；
- 矩与极限：方差恒等式、Walsh 谱、Hájek 比、块总和律、KS；
- 搜索：设计搜索、权重搜索、置换搜索、模拟；
- 门禁、账本、模板、编译。

### 3.3 陈述账本 `StatementLedger`

四状态：`gated`（工具认证，带 `claim_id`）、`derived`（文中证明，列 `depends_on`）、
`cited`（文献）、`unproved`（未证）。

- `check` 拒绝 `gated` 无证据、`cited` 无出处；
- 写作只能引用账本条目；
- 这是“证明链可审计”的基础。

### 3.4 活动机扩展

在原 `problem_solving` 之外新增：

- `design_synthesis`：选/建设计；
- `population_backsolve`：反解总体或记录秩阻塞；
- `limit_law_check`：块总和律与 SRSWOR 侧 CLT。

每个活动通过 `SKILL_ACTIVITY_HINTS` 绑定对应 skill。

### 3.5 四个领域 skill

| skill | 作用 |
|---|---|
| `ht-counterexample-protocol` | 主协议：五元组、九步流程、失败记录 schema |
| `ht-r-design-search` | 选设计：先判强度、再判方阵、再看块大小 |
| `ht-method-portfolio` | 七条路线与阻塞信号，卡住时显式换路线 |
| `ht-paper-drafting` | 账本驱动成稿、证明、排版 |

每个 skill 是 `SKILL.md`：frontmatter（`allowed-tools` 白名单）+ `Usage Hint` + `Execution Steps` + `Tool Calls` + `Output Contract`。

### 3.6 领域 agent

`assets/agents/builtin/ht-researcher/AGENT.md` 写死行为准则：

- 只接受推进五元组、否证旧结论、结构化失败；
- 数字必须来自 `ht_*` 工具；
- 量词优先（`r` 固定，`N,n→∞`）；
- 允许 `run_python_script` 探索，但结论必须有工具证据。

### 3.7 失败路径可见

- 原版在 `research` 模式下隐藏 `record_failed_path`；
- `moonshine_bridge.py` 打补丁把它移出 `MODE_HIDDEN_TOOLS`；
- 协议要求写 `failed_path`：`r`、设计族、参数、对称性/秩、`failed_at`、`witness`、障碍类别、下一步。

### 3.8 LaTeX 成稿流水线

- `ht_template`：期中/期刊模板；
- `ht_compile_latex`：XeLaTeX 两遍，返回 `pages`、首错；
- `ht_typeset_paper`：无 LaTeX 时兜底；
- 排版问题只改 `.tex`，不改渲染器。

### 3.9 安装与启动

- `integration/install_into_moonshine.py --inplace`：给已有 editable 安装打补丁、装资产、seed 项目；
- `run_ht_agent.py`：`config / doctor / run / ask / shell`；
- `--prompt-file`：从 UTF-8 文件读 prompt，避免 PowerShell 拆词；
- `doctor` 五项自检：agent / skills / tools / project / provider。

---

## 4 核心文件地图

### 4.1 入口

| 文件 | 功能 |
|---|---|
| `run_ht_agent.py` | 启动器：解析 `--root/--home/--project`，子命令 `config/doctor/run/ask/shell`；流式输出与推理段落打印 |
| `ht_moonshine/cli.py` | 包内 CLI 入口 |
| `ht_moonshine/__main__.py` | `python -m ht_moonshine` 入口 |

### 4.2 精确工具与领域算法

| 文件 | 功能 |
|---|---|
| `exact.py` | `Fraction` 精确算术、紧凑输出 |
| `fields.py` | `GF(p^k)`、Singer 差集 |
| `designs.py` | 设计族构造、强度检查、λ 剖面 |
| `inclusion.py` | 逐子集包含概率、与 SRSWOR 对比 |
| `algebra.py` | `A y = w` 反解、`rank`/`augmented_rank`、方差恒等式 |
| `laws.py` | 指数分位点、中心化、矩/偏度/KS、Hájek 比 |
| `hyperplane.py` | 仿射超平面族、bent 总体、`r` 阶强度剖面 |
| `explore.py` | 设计搜索、权重搜索、置换搜索、模拟 |
| `tools_impl.py` | 18 个工具 handler |

### 4.3 判定与证据

| 文件 | 功能 |
|---|---|
| `bundle.py` | `verify_bundle` 确定性门禁、`claim_id` 哈希 |
| `ledger.py` | 陈述账本：`add/list/update/check/render` |
| `brief.py` | 项目任务书、规则、论文模板 seed |
| `moonshine_bridge.py` | 注册表子类、资产安装、源码补丁、settings |

### 4.4 输出与自检

| 文件 | 功能 |
|---|---|
| `latex.py` | XeLaTeX 两遍编译、报 `pages`/首错 |
| `typeset.py` | reportlab 兜底排版 |
| `selftest.py` | 22 项自检 |
| `tests/` | 16 个测试文件、122 个测试用例 |
| `scripts/` | 可选的边界检查与复核脚本（不随本次提交） |

### 4.5 资产

| 路径 | 内容 |
|---|---|
| `assets/tools/definitions/` | 18 个工具的 Markdown 定义 + schema + Usage Hint |
| `assets/skills/builtin/` | 4 个领域 skill |
| `assets/agents/builtin/ht-researcher/` | 领域 agent 定义 |
| `integration/install_into_moonshine.py` | in-place 安装器 |

---

## 5 调用链：一次研究回合怎么走

```
prompt（--prompt-file）
   │
   ▼
run_ht_agent.py  ── 解析 root/home/project，构造 runtime
   │
   ▼
moonshine_bridge ── 注册 ht_* 工具、安装 skill/agent、打补丁
   │
   ▼
Moonshine 研究循环
   ├─ 加载 AGENT.md 与 skill Usage Hint
   ├─ 选择活动（problem_solving / design_synthesis / ...）
   ├─ 调 ht_* 工具（tools_impl → 精确算术）
   ├─ 需要时写 failed_path
   └─ 收束：ht_verify_bundle → claim_id
   │
   ▼
陈述账本（gated/derived/cited/unproved）
   │
   ▼
成稿：ht_template → ht_compile_latex（或 ht_typeset_paper）
```

关键点：

- **工具是唯一数字来源**；LLM 负责选择、解释、写证明散文。
- **门禁在评审前**；`verify_overall` 只审“散文是否成立”，不产生证据。
- **账本是写作的唯一入口**；`check` 不通过不排版。

---

## 6 安装与运行

### 6.1 安装（in-place，幂等）

```powershell
conda activate moonshine
cd "C:\Users\于家伟\Desktop\AI4Math\Stastistics"

python integration\install_into_moonshine.py --inplace `
  --source "C:\Users\于家伟\Desktop\Moonshine-main" `
  --home "C:\Users\于家伟\Desktop\moonshine-data" `
  --no-settings --seed-project --project ht_r3
```

### 6.2 自检

```powershell
python run_ht_agent.py --root "C:\Users\于家伟\Desktop\Moonshine-main" `
  --home "C:\Users\于家伟\Desktop\moonshine-data" doctor
```

`doctor` 报 agent / skills / tools / project / provider 五项；`ready: no` 先查 provider 凭据。

### 6.3 跑研究

```powershell
python run_ht_agent.py --root "C:\Users\于家伟\Desktop\Moonshine-main" `
  --home "C:\Users\于家伟\Desktop\moonshine-data" --project ht_r3 `
  run --iterations 3 --prompt-file prompt_r4b.txt
```

- `run`：多轮研究循环；
- `ask`：单轮问答；
- `shell`：交互式；
- `--prompt-file`：UTF-8（兼容 BOM）读入，避免 PowerShell 拆词。

### 6.4 单测与自检

```powershell
python -m pytest tests -q
python -m ht_moonshine selftest
```

---

## 7 数据与目录布局

```
moonshine-data/
└─ projects/ht_r3/
   ├─ workspace/            # 每轮产物：problem.md、脚本、JSON、paper.tex
   ├─ memory/by_type/       # verified_conclusion、failed_path、research_note 等
   └─ reports/              # 研究回合报告
```

- 账本：`workspace/statements.jsonl`（append-only）；
- 工具证据：`workspace/*.json`；
- 成稿：`workspace/paper.tex` / `paper.pdf`，归档到项目输出目录。

---

## 8 能力边界（必须与结论同时说）

1. **门禁只覆盖有限实例**；全族结论是解析证明，不能说“机器验证了整个猜想”。
2. `verify_overall` 是 LLM 评审，不是证明检查器；它抓不到“抄错门禁数字”这类错误。
3. 工具与协议绑定 HT 问题；换问题需要重写判定层与工具层，循环/账本/排版可复用。
4. 领域口径（如加权计划与均匀区组的区别）必须与结论同时陈述。
5. r≥6 未解决；五原子构造在六阶失效，`(s+1)` 原子族仍是猜想。
6. 不宣称“整个 Chen 猜想已解决”；只能说“r=2,3,4,5 的相应结论已给出证明/构造”。

---

## 9 复现与自检清单

- `doctor`：五项 ready；
- `selftest`：22/22；
- `pytest`：122 个用例；
- 任一 gated 结论：能从 `claim_id` 重放到同一 `PASS`；
- 任一论文数字：能追到账本条目或工具 JSON。

---

## 10 一句话总结

**Moonshine 提供循环与机制；我们重写了它的领域工作流，并在外面加了“精确工具 + 确定性门禁 + 陈述账本 + 成稿流水线”。**
