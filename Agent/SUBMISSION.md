# Submission 清单

本目录只包含 **HT-Researcher 智能体本身**（架构、代码、资产、测试），**不包含**任何反例研究的结果、论文或实验输出。

## 包含内容

| 路径 | 说明 |
|---|---|
| `README.md` | 智能体架构与核心文件说明 |
| `AGENT_BUILD.md` | 搭建细节：如何改造 Moonshine、调用链、安装运行 |
| `pyproject.toml` | 包定义（`ht-moonshine`） |
| `run_ht_agent.py` | 启动器：`config / doctor / run / ask / shell` |
| `ht_moonshine/` | 核心包：精确工具、门禁、账本、桥接、LaTeX、自检 |
| `assets/` | 18 个工具定义、4 个领域 skill、1 个领域 agent |
| `integration/install_into_moonshine.py` | in-place 安装器 |
| `requirements.txt` | Moonshine 运行时依赖清单 |
| `paper/` | 论文模板（`template.tex`、`template-midterm.tex`、`template.md`），供 `ht_template` 使用 |
| `tests/` | 16 个测试文件、122 个测试用例 |

## 有意排除

- `Result by Statistics/`：研究结果与论文；
- `Stastistics/scripts/`：结果相关的边界检查脚本；
- `Stastistics/prompt*.txt`：任务提示词（含研究目标）；
- `Stastistics/examples/`：结果示例 JSON；
- `Stastistics/runtime/`：本地 Moonshine 副本（含 home 配置与本地数据）；提交不携带，需按下面步骤自行安装 Moonshine。
- `Stastistics/workspace/`、`deliverables/`、`docs/`、`paper/` 中的生成物。

## 安装

依赖 Python 3.8+、一个可用的 Moonshine 安装；LLM provider 由 Moonshine 配置。

```bash
# 0) 安装 Moonshine 本体（本仓库不携带其源码）
pip install -r requirements.txt
pip install -e /path/to/Moonshine

# 1) 给已有 Moonshine 安装打补丁、装资产、seed 项目
python integration/install_into_moonshine.py --inplace \
  --source /path/to/Moonshine \
  --home /path/to/moonshine-data \
  --no-settings --seed-project --project ht_r3
```

## 自检

```bash
python run_ht_agent.py --root /path/to/Moonshine \
  --home /path/to/moonshine-data doctor

python -m unittest discover -s tests -q
python -m ht_moonshine selftest
```

`doctor` 检查 agent / skills / tools / project / provider 五项；`selftest` 应全部通过（22/22）。
请在已安装 Moonshine 的 Python 环境中运行；测试需要可写的临时目录。
