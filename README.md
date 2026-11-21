# <p align="center">HT-Researcher：面向统计研究的智能体</p>

<p align="center">于家伟 同济大学数学科学学院统计学专业</p>

这是一个基于DeepMath团队的Moonshine `https://github.com/DeepMathLLM/Moonshine` 进行改造以面向“高阶包含概率能否决定 Horvitz-Thompson 估计量的渐近分布”这一统计学领域开放性问题的智能体.它将此问题拆分成可判定的五元组，并用精确的计算工具加以辅助裁决，代码见`Stastistics/`.

---

# PART1 关于选题

**<p align="center">低阶包含概率能否决定 Horvitz-Thompson 估计量的渐近分布？</p>**

## 1.1问题背景

在抽样调查中，Horvitz-Thompson(HT)估计量是估计有限总体总量的标准工具：
```math
\hat{Y}_{\mathrm{HT}} = \sum_{i \in s} \frac{y_i}{\pi_i}
```
其中 $$\pi_i$$ 是单元 $$i$$ 的**一阶包含概率**(被抽入样本的概率).HT 估计量的期望由一阶包含概率决定，方差由一阶和二阶包含概率(任意两个单元同时入样的概率)共同决定.

一个自然的问题是：**低阶包含概率是否足以决定 HT 估计量的渐近分布？** 如果两个抽样方案在所有 $$r$$ 阶及以下的包含概率上完全相同，那么在一个方案下渐近正态的 HT 估计量，在另一个方案下是否也必然渐近正态？

这个问题的重要性在于：包含概率是抽样设计的内在特征，不需要描述完整概率分布就能指定.如果低阶包含概率足以决定极限分布，那么复杂抽样设计下的中心极限定理就可以建立在透明、可验证的低阶量之上，而不必针对每个设计单独证明.

## 1.2已知结果： $$r=2$$ 的反例

Jiahua Chen证明了：**对于 $$r=2$$ 答案是否定的.**

他的文章做了如下三件事情：

1. **设计—包含概率的桥**(定理 2.1)：任意 `t-(N, n, λ_t)` 设计，均匀选一个块作为样本，
   则 `s ≤ t` 阶包含概率恰为 `C(n,s)/C(N,s)`，与 SRSWOR 完全相同.也就是说，"低阶一致"
   并不稀有——任何 `t`-设计都自动提供它.

2. **r = 2 的反例**(第 3–4 节)：取射影平面 `PG(2,q)` 的 BIBD，参数为
   `N = B = q² + q + 1`、`n = q + 1`、`λ = 1`，且 `A Aᵀ = qI + J`.先指定块总和 `w`
   为中心化指数分位点，用 `y = Aᵀ w / q` 反解总体；再利用 `w` 坐标的置换自由度，
   配合 Hoeffding–Serfling 不等式选出一个置换使 `max_i |y_i| = o(1)`，从而 SRSWOR 侧
   仍满足中心极限定理.

3. **极限律不同**(定理 4.1)：BIBD 下样本总量趋于 `E − 1`（`E ~ Exp(1)`），SRSWOR 下
   趋于 `N(0,1)`；在每个 `q` 上两者均值、方差都相同，且共同方差趋于 1.数值演示取
   `q = 2¹⁰`（`N ≈ 1.05 × 10⁶`、`n = 1025`），做 2 万次 SRSWOR 抽样.

结论是：一阶、二阶包含概率不能把 SRSWOR 的中心极限定理"传递"给另一个设计；
低阶包含概率并不控制样本指示变量的整体依赖结构.

这个反例的构造依赖两个关键要素：

1. **有限射影平面上的平衡不完全区组设计(BIBD)**：射影平面 $$PG(2,q)$$ 产生一个 strength-2 的区组设计，其组合结构保证了一阶和二阶包含概率与 SRSWOR 精确一致(定理 2.1 的一般性结论).
2. **排列论证**：通过随机排列预设的区组总量，并用无放回抽样的指数不等式证明存在一个排列，使得构造出的有限总体满足 SRSWOR 中心极限定理的充分条件($$\max |y_i| \to 0$$)，同时保持 BIBD 抽样下的非正态极限分布.

## 1.3开放猜想：任意固定阶数 $$r$$

论文在引言和讨论中明确提出一个更一般的猜想：

> 对于任意固定的整数 $$r$$，仅靠 $$r$$ 阶包含概率的一致，不足以保证共同的极限分布.

论文只证明了 $$r=2$$ 的情形.对于 $$r \ge 3$$，猜想是否成立，目前是开放的.

这个猜想的理论意义在于：它断言低阶包含概率只能控制 HT 估计量的低阶矩，却无法控制样本指示变量的全局依赖结构.而正是这种依赖结构，即使在所有低阶矩完全一致时，仍然会体现在极限分布中.


**核心文献**

Jiahua Chen. *Low-Order Inclusion Probabilities Do Not Determine Asymptotic Normality.* arXiv:2610.09168, 2026.

论文作者介绍：
> Jiahua Chen(陈家骅)是加拿大不列颠哥伦比亚大学(UBC)统计系终身教授，加拿大皇家科学院院士，在抽样调查、经验似然与有限混合模型领域有奠基性贡献.他本科毕业于中国科学技术大学，硕士就读于中国科学院系统科学研究所，1990年在美国威斯康星大学麦迪逊分校获博士学位，师从吴建福(Jeff Wu)教授.他于2007年至2020年担任加拿大国家一级讲座教授(Canada Research Chair, Tier I)，曾任泛华统计学会主席、加拿大统计杂志主编，是数理统计学会(IMS)与美国统计协会(ASA)会士.他最具代表性的工作之一是将经验似然方法引入有限总体抽样(1993年发表于 *Biometrika*)，这篇论文是该领域的高被引经典.他于2014年获加拿大统计学会最高荣誉金质奖章，2016年获泛华统计协会杰出成就奖，2022年当选加拿大皇家科学院院士.

---

# PART2 关于智能体
## 2.1 总体思路
目标是将“统计反例研究”这一问题拆成可执行、可裁决、可追溯的流程.构想如下：

A. **循环不动**，将Moonshine 的研究循环、项目记忆、工具注册表、skill/agent 机制全部保留.

B. **领域层重写**，skill 内容、agent 行为准则、活动绑定、失败语义、评审顺序按统计研究改写.

C. **判定与证据叠加**，在 LLM 之外加一层确定性判定和一层证据管理.

## 2.2 整体架构设计
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

- **运行时层**：Moonshine 原生的活动机、记忆、注册表、沙箱.
- **协议层**：4 个领域 skill + 1 个领域 agent，规定“什么时候做什么”.
- **计算层**：18 个 `ht_*` 工具，全部精确算术.
- **判定层**：`ht_verify_bundle` 一票否决 + `claim_id`.
- **证据层**：陈述账本，四状态管理.
- **产出层**：报告与撰写成稿.

## 2.3 对Moonshine智能体的改造

| 类别 | 内容 |
|---|---|
| **改写** | 重写 4 个领域 skill 的内容；重写领域 agent 行为准则；新增并绑定研究活动；把 `record_failed_path` 从研究模式的隐藏名单移出；在 `verify_overall` 之前插入确定性门禁 |
| **叠加** | 18 个精确工具；`ht_verify_bundle` 与 `claim_id`；陈述账本；LaTeX 成稿流水线；in-place 安装器 |
| **保留** | 研究循环；项目记忆；工具注册表机制；skill/agent 加载；`run_python_script` 沙箱 |

### 2.3.1 活动机扩展

在原有 `problem_solving` 之外新增三个领域活动，并各绑定一个 skill：

- `design_synthesis`：选设计、判强度、量出逆问题；
- `population_backsolve`：反解总体，或记录精确的秩阻塞；
- `limit_law_check`：检查块总和律与 SRSWOR 侧的中心极限定理条件。

### 2.3.2 失败语义

原版研究模式下 `record_failed_path` 被隐藏.补丁把它移出隐藏名单，使失败必须被**主动**记录：

- 卡在哪一步；
- 精确数字(秩、维数亏、见证子集)；
- 障碍类别；
- 下一步候选路线.

失败记录进入 `memory/by_type/failed_path.md`，成为可检索资产.

### 2.3.3 评审顺序

原版只有 `verify_overall`(LLM 三维评审)，而经改造后我们有：

A.先跑 `ht_verify_bundle`（确定性、一票否决）；
 
B.通过后再跑 `verify_overall` 审散文；

C.两者冲突判 `inconclusive`。

LLM 负责“解释与写作”，工具负责“裁决数字”.

## 2.4 智能体核心文件介绍
### 2.4.1 入口

| 文件 | 用途 |
|---|---|
| `run_ht_agent.py` | 启动器：解析 `--root / --home / --project`，提供 `config`、`doctor`、`run`、`ask`、`shell`；流式输出与推理段落打印；`--prompt-file` 从 UTF-8 文件读任务 |
| `ht_moonshine/cli.py` | 包内 CLI 入口 |
| `ht_moonshine/__main__.py` | `python -m ht_moonshine` 入口 |

### 2.4.2 领域算法与精确工具

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

### 2.4.3 判定、证据与协议

| 文件 | 用途 |
|---|---|
| `ht_moonshine/bundle.py` | `verify_bundle` 确定性门禁；`claim_id` 哈希；逐项检查结果 |
| `ht_moonshine/ledger.py` | 陈述账本 `add / list / update / check / render`；四状态校验 |
| `ht_moonshine/brief.py` | 项目任务书、规则、论文模板的 seed |
| `ht_moonshine/moonshine_bridge.py` | 注册表子类、工具注册、资产安装、源码补丁、settings |
| `assets/agents/builtin/ht-researcher/AGENT.md` | 领域 agent 行为准则 |
| `assets/skills/builtin/*/SKILL.md` | 4 个领域 skill（协议、选设计、换路线、成稿） |
| `assets/tools/definitions/*` | 18 个工具的 Markdown 定义、JSON schema、Usage Hint |

### 2.4.4 输出与工程

| 文件 | 用途 |
|---|---|
| `ht_moonshine/latex.py` | XeLaTeX 两遍编译，返回 `pages` 与首错 |
| `ht_moonshine/typeset.py` | 无 LaTeX 时的 reportlab 兜底排版 |
| `ht_moonshine/selftest.py` | 22 项自检 |
| `integration/install_into_moonshine.py` | in-place 安装器：打补丁、装资产、seed 项目 |
| `tests/` | 16 个测试文件、122 个测试用例 |
| `scripts/` | 边界检查与独立复核脚本 |

## 2.5 四个skills介绍
| skill | 触发 | 职责 |
|---|---|---|
| `ht-counterexample-protocol` | 每次领域尝试 | 五元组协议、九步流程、失败记录 schema |
| `ht-r-design-search` | 进入设计构造 | 先判强度、再判方阵、再看块大小 |
| `ht-method-portfolio` | 默认路线卡住 | 七条路线与阻塞信号，显式切换 |
| `ht-paper-drafting` | 从计算转为写作 | 账本驱动、证明、排版 |


## 2.6 如何进行研究
### 2.6.1 调用流程
1. 用户给出 prompt（建议用 `--prompt-file`）；
2. `run_ht_agent.py` 解析路径，构造运行时；
3. `moonshine_bridge` 注册 `ht_*` 工具、安装 skill/agent、打补丁；
4. Moonshine 研究循环启动，加载 `AGENT.md` 与 skill 的 `Usage Hint`；
5. agent 选择活动，调用 `ht_*` 工具；所有数字来自工具输出；
6. 需要时写 `failed_path`，记录结构化失败；
7. 收束时跑 `ht_verify_bundle`，通过则生成 `claim_id`；
8. 结论写入 `statements.jsonl`，按四状态管理；
9. 写作阶段用账本生成报告/论文，`check` 通过后排版.

### 2.6.2 安装与运行
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

`doctor` 报 agent / skills / tools / project / provider 五项；`ready: no` 时先配置 provider.

### 2.6.3自检与目录布局
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

**<p align="center">智能体相关文件见Agent文件夹</p>**

---

# PART3 逐步优化记录

本研究所接的Deepseek V4 Pro的API Key，所得成果总结如下：

>关于 $$r=2$$ ：对Chen关于 $$r=2$$ 的构造进行了结构性加强，明确给出该反例的构造思路无法推广到 $$r \ge 3$$ 的理由，详情见`Result/PResults/r2.pdf`.(记录于2026.11.01)

>关于 $$r = 3$$ ：构造出了r=3情况下的反例，大致思路：用F₂m的全部仿射超平面构造强度恰为3的设计，再配一个bent二次型总体，使每个块的总和恒为±1/2(样本总量服从 ±1 两点律)，而SRSWOR侧由有限总体CLT趋于正态——于是三阶以内包含概率一致，极限律却不同.详情见`Result/PResults/r3.pdf`.(记录于2026.11.21)

