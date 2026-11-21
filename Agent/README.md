# HT-Researcher

一个基于 Moonshine（DeepMathLLM）改造的**统计研究智能体**，面向 Horvitz–Thompson 包含概率类问题。
本文档只介绍智能体本身的架构、改造方式与核心文件用途，不涉及具体研究成果。

---

## 1 设计目标与原则

目标不是再写一个通用聊天机器人，而是把“统计反例研究”拆成可执行、可裁决、可追溯的流程。

三条原则：

1. **循环不动**：Moonshine 的研究循环、项目记忆、工具注册表、skill/agent 机制全部保留。
2. **领域层重写**：skill 内容、agent 行为准则、活动绑定、失败语义、评审顺序按统计研究改写。
3. **判定与证据叠加**：在 LLM 之外加一层确定性判定（精确工具 + 门禁）和一层证据管理（陈述账本）。

---

## 2 整体架构

```
                    ┌─────────────────────────────┐
                    │  用户 prompt / 任务文件       │
                    └──────────────┬──────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │  run_ht_agent.py 启动器       │
                    │  config / doctor / run / ask  │
                    └──────────────┬──────────────┘
                                   ▼
                    ┌─────────────────────────────┐
                    │  moonshine_bridge            │
                    │  注册工具、装 skill/agent、   │
                    │  给 Moonshine 源码打补丁      │
                    └──────────────┬──────────────┘
                                   ▼
        ┌──────────────────────────────────────────────────┐
        │              Moonshine 研究运行时                  │
        │  活动机 · 项目记忆 · 工具注册表 · skill/agent 加载  │
        └───────┬───────────────────────────────┬──────────┘
                ▼                               ▼
    ┌───────────────────────┐      ┌──────────────────────────┐
    │  领域 skill / agent    │      │  ht_* 精确工具（18 个）    │
    │  协议、选型、换路线、  │      │  设计、包含概率、秩、      │
    │  成稿                  │      │  谱、极限律、门禁、账本    │
    └───────────┬───────────┘      └────────────┬─────────────┘
                └───────────────┬───────────────┘
                                ▼
                 ┌──────────────────────────────┐
                 │  ht_verify_bundle 确定性门禁  │
                 │  逐项检查 + claim_id          │
                 └──────────────┬───────────────┘
                                ▼
                 ┌──────────────────────────────┐
                 │  StatementLedger 陈述账本     │
                 │  gated/derived/cited/unproved │
                 └──────────────┬───────────────┘
                                ▼
                 ┌──────────────────────────────┐
                 │  输出：报告 / 论文 / 失败记录 │
                 └──────────────────────────────┘
```

分层看：

- **运行时层**：Moonshine 原生的活动机、记忆、注册表、沙箱；
- **协议层**：4 个领域 skill + 1 个领域 agent，规定“什么时候做什么”；
- **计算层**：18 个 `ht_*` 工具，全部精确算术；
- **判定层**：`ht_verify_bundle` 一票否决 + `claim_id`；
- **证据层**：陈述账本，四状态管理；
- **产出层**：报告与 LaTeX 成稿。

---

## 3 对 Moonshine 的改造

| 类别 | 内容 |
|---|---|
| **改写**（动到原行为） | 重写 4 个领域 skill 的内容；重写领域 agent 行为准则；新增并绑定研究活动；把 `record_failed_path` 从研究模式的隐藏名单移出；在 `verify_overall` 之前插入确定性门禁 |
| **叠加**（新增能力） | 18 个精确工具；`ht_verify_bundle` 与 `claim_id`；陈述账本；LaTeX 成稿流水线；in-place 安装器 |
| **保留**（未动） | 研究循环；项目记忆；工具注册表机制；skill/agent 加载；`run_python_script` 沙箱 |

### 3.1 活动机扩展

在原有 `problem_solving` 之外新增三个领域活动，并各绑定一个 skill：

- `design_synthesis`：选设计、判强度、量出逆问题；
- `population_backsolve`：反解总体，或记录精确的秩阻塞；
- `limit_law_check`：检查块总和律与 SRSWOR 侧的中心极限定理条件。

### 3.2 失败语义

原版研究模式下 `record_failed_path` 被隐藏。补丁把它移出隐藏名单，使失败必须被**主动**记录：

- 卡在哪一步；
- 精确数字（秩、维数亏、见证子集）；
- 障碍类别；
- 下一步候选路线。

失败记录进入 `memory/by_type/failed_path.md`，成为可检索资产。

### 3.3 评审顺序

原版只有 `verify_overall`（LLM 三维评审）。改造后：

1. 先跑 `ht_verify_bundle`（确定性、一票否决）；
2. 通过后再跑 `verify_overall` 审散文；
3. 两者冲突判 `inconclusive`。

LLM 负责“解释与写作”，工具负责“裁决数字”。

---

## 4 核心文件与用途

### 4.1 入口

| 文件 | 用途 |
|---|---|
| `run_ht_agent.py` | 启动器：解析 `--root / --home / --project`，提供 `config`、`doctor`、`run`、`ask`、`shell`；流式输出与推理段落打印；`--prompt-file` 从 UTF-8 文件读任务 |
| `ht_moonshine/cli.py` | 包内 CLI 入口 |
| `ht_moonshine/__main__.py` | `python -m ht_moonshine` 入口 |

### 4.2 领域算法与精确工具

| 文件 | 用途 |
|---|---|
| `ht_moonshine/exact.py` | `Fraction` 精确算术、紧凑输出 |
| `ht_moonshine/fields.py` | 有限域 `GF(p^k)`、Singer 差集 |
| `ht_moonshine/designs.py` | 设计族构造、强度检查、λ 剖面 |
| `ht_moonshine/inclusion.py` | 逐子集包含概率、与 SRSWOR 对比 |
| `ht_moonshine/algebra.py` | `A y = w` 反解、`rank`/`augmented_rank`、方差恒等式 |
| `ht_moonshine/laws.py` | 分位点、中心化、矩/偏度/KS、Hájek 比 |
| `ht_moonshine/hyperplane.py` | 仿射超平面族、bent 总体、阶数强度剖面 |
| `ht_moonshine/explore.py` | 设计搜索、权重搜索、置换搜索、模拟 |
| `ht_moonshine/tools_impl.py` | 18 个工具 handler 的统一实现 |

### 4.3 判定、证据与协议

| 文件 | 用途 |
|---|---|
| `ht_moonshine/bundle.py` | `verify_bundle` 确定性门禁；`claim_id` 哈希；逐项检查结果 |
| `ht_moonshine/ledger.py` | 陈述账本 `add / list / update / check / render`；四状态校验 |
| `ht_moonshine/brief.py` | 项目任务书、规则、论文模板的 seed |
| `ht_moonshine/moonshine_bridge.py` | 注册表子类、工具注册、资产安装、源码补丁、settings |
| `assets/agents/builtin/ht-researcher/AGENT.md` | 领域 agent 行为准则 |
| `assets/skills/builtin/*/SKILL.md` | 4 个领域 skill（协议、选设计、换路线、成稿） |
| `assets/tools/definitions/*` | 18 个工具的 Markdown 定义、JSON schema、Usage Hint |

### 4.4 输出与工程

| 文件 | 用途 |
|---|---|
| `ht_moonshine/latex.py` | XeLaTeX 两遍编译，返回 `pages` 与首错 |
| `ht_moonshine/typeset.py` | 无 LaTeX 时的 reportlab 兜底排版 |
| `ht_moonshine/selftest.py` | 22 项自检 |
| `integration/install_into_moonshine.py` | in-place 安装器：打补丁、装资产、seed 项目 |
| `tests/` | 16 个测试文件、122 个测试用例 |
| `scripts/` | 边界检查与独立复核脚本 |

---

## 5 四个 skill 的职责

| skill | 触发 | 职责 |
|---|---|---|
| `ht-counterexample-protocol` | 每次领域尝试 | 五元组协议、九步流程、失败记录 schema |
| `ht-r-design-search` | 进入设计构造 | 先判强度、再判方阵、再看块大小 |
| `ht-method-portfolio` | 默认路线卡住 | 七条路线与阻塞信号，显式切换 |
| `ht-paper-drafting` | 从计算转为写作 | 账本驱动、证明、排版 |

每个 skill 都是 `SKILL.md`：YAML frontmatter（`name`、`description`、`allowed-tools` 白名单）+ `Usage Hint` + `Execution Steps` + `Tool Calls` + `Output Contract`。

---

## 6 一次研究回合的调用链

1. 用户给出 prompt（建议用 `--prompt-file`）；
2. `run_ht_agent.py` 解析路径，构造运行时；
3. `moonshine_bridge` 注册 `ht_*` 工具、安装 skill/agent、打补丁；
4. Moonshine 研究循环启动，加载 `AGENT.md` 与 skill 的 `Usage Hint`；
5. agent 选择活动，调用 `ht_*` 工具；所有数字来自工具输出；
6. 需要时写 `failed_path`，记录结构化失败；
7. 收束时跑 `ht_verify_bundle`，通过则生成 `claim_id`；
8. 结论写入 `statements.jsonl`，按四状态管理；
9. 写作阶段用账本生成报告/论文，`check` 通过后排版。

---

## 7 安装与运行

依赖 Python 3.8+、一个可用的 Moonshine 安装与已配置的 LLM provider。本仓库不携带 Moonshine 源码，
需先安装：

```bash
pip install -r requirements.txt
pip install -e /path/to/Moonshine
```

然后：

```bash
# 1) 给已有 editable 安装打补丁、装资产、seed 项目
python integration/install_into_moonshine.py --inplace \
  --source /path/to/Moonshine \
  --home /path/to/moonshine-data \
  --no-settings --seed-project --project ht_r3

# 2) 检查接线
python run_ht_agent.py --root /path/to/Moonshine \
  --home /path/to/moonshine-data doctor

# 3) 跑研究循环
python run_ht_agent.py --root /path/to/Moonshine \
  --home /path/to/moonshine-data --project ht_r3 \
  run --iterations 3 --prompt-file your_prompt.txt
```

`doctor` 报 agent / skills / tools / project / provider 五项；`ready: no` 时先配置 provider。

---

## 8 自检与目录布局

```bash
python -m pytest tests -q
python -m ht_moonshine selftest
```

```text
moonshine-data/projects/ht_r3/
├─ workspace/            # 每轮产物：problem.md、脚本、JSON、paper.tex
├─ memory/by_type/       # verified_conclusion、failed_path、research_note 等
└─ reports/              # 研究回合报告
```

---

## 9 边界

- 门禁只覆盖有限实例；全族结论仍是解析证明。
- `verify_overall` 是 LLM 评审，不是证明检查器。
- 工具与协议绑定 Horvitz–Thompson 问题；换问题需重写判定层与工具层，循环、账本、排版可复用。
