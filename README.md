# 麋鹿ai测试集

**Elk AI Test Set**

**从产品需求出发，建立有覆盖、有标准、能复核的 AI 评测集。**

`elk-ai-test-set` 是一个用于 AI 产品评测设计的 Skill。它帮助你明确测试目标、构造样本、制定评分规则，并整理成 CSV 或 Excel，支持单版本验收、版本比较和回归测试。

指标由产品场景决定。你可以用它评测知识库问答、内容生成、代码助手、工具调用 Agent 或多模态产品，不需要沿用某个行业的固定评分项。

## 什么时候用

- **上线前验收**：哪些任务必须完成，哪些错误一旦出现就不能通过？
- **比较两个版本**：同一输入下，新 Prompt、新模型或新流程改善了什么，又退步了什么？
- **补齐回归测试**：真实问题已经出现，怎样将它变成可复用的测试案例？
- **统一评审标准**：怎样让评分者依据规则和证据打分，减少“凭感觉”？

本 Skill 负责评测设计与结果记录，不内置模型调用器，不会自动批量运行模型。评分需要被测系统的实际输出；关键业务目标、通过阈值和裁决角色由使用者确定。

## 工作流程

```mermaid
flowchart LR
    A[评测目标卡] --> B[覆盖矩阵]
    B --> C[测试样本]
    C --> D[评分方法]
    D --> E[评分标准]
    E --> F[表格与结果汇总]
```

默认分阶段推进，每阶段完成后确认。已有目标卡、覆盖矩阵或评分标准时，可以直接从对应阶段开始。

## 快速开始

### 1. 安装

下载本仓库，保留完整的 `elk-ai-test-set` 目录，包括 `SKILL.md`、参考文档、脚本和模板，放入你的 AI 工具所配置的技能目录。

Codex 用户级安装位置通常为 `$CODEX_HOME/skills/elk-ai-test-set/`；未设置 `CODEX_HOME` 时，可使用 `~/.codex/skills/elk-ai-test-set/`。

本仓库配置为显式调用，在对话中输入：

```text
$elk-ai-test-set
```

技能使用需要支持 Skill 的 AI 工具。CSV 校验脚本可独立运行，使用 Python 3.9+ 标准库，无需安装额外 Python 包。生成和校验 XLSX 需要宿主工具具备电子表格处理能力。

### 2. 描述产品与本次决策

复制下面的示例，替换成你的产品：

```text
$elk-ai-test-set

我要评测一个企业知识库问答助手。
用户是企业员工，输入制度问题，输出有依据的答案和下一步操作。
本次想判断新版 Prompt 能否替换旧版。
主要问题是编造制度、遗漏关键条件、遇到知识缺口仍给出确定答案。
我有 8 条真实问题，希望补成 30 条样本。

先帮我建立评测目标卡。
```

不必提前想好所有指标；提供真实任务、当前问题和要做的决策即可开始讨论。

### 3. 确认后继续

```text
目标卡确认，继续制定覆盖矩阵。
```

```text
覆盖矩阵确认，生成测试样本，先导出 CSV。
```

也可以从已有材料开始：

```text
$elk-ai-test-set

下面是已确认的目标卡和覆盖矩阵。
请直接生成样本，不重复讨论目标。
```

## 会得到什么

除目标卡和覆盖矩阵外，完整 Excel 包含四张表：

| 工作表 | 记录内容 |
|---|---|
| 评测集 | 测试输入、预期行为、硬性约束、适用指标和来源 |
| 评分工作台 | 基线/候选输出、各项评分、规则证据与评测状态 |
| 评分标准 | 指标定义、评分锚点、正反例、裁决方式和硬门槛 |
| 评分汇总 | 按指标统计完成率、通过率、平均分、GSB 和否决记录 |

评分工作台按 **样本 × 指标 × 运行 × 评审者** 逐行记录。增加指标时增加记录，不需要为某个业务新增固定专用列。

默认每个工作簿对应一次运行、一名评审者和一组版本。多评审或多次运行需要分开汇总，避免混淆统计口径。

- [空白 Excel 模板](assets/评测集表格模板.xlsx)
- [目标卡模板](assets/eval-goal-card-template.md)
- [字段定义](assets/schema.json)
- [填写与汇总规则](references/sample-schema.md)

模板预留 30 条样本、90 条评分记录、20 个指标位，用于起始排版。正式交付时应按实际规模调整公式和数据验证范围。

## 三种评分方法

| 方法 | 适合的问题 | 如何记录 |
|---|---|---|
| 二值 | 是否满足明确规则？ | 通过 / 不通过 |
| 1–5 分 | 单个输出的质量处于哪个档位？ | 依据可观察锚点记录整数分 |
| GSB | 候选相对基线更好、持平还是更差？ | G / S / B，必须有成对输出 |

每次评分引用规则编号和可定位的输出证据。硬门槛失败不能被平均分抵消；输出缺失、未评分和不适用也不能当作通过。

需要加权总分时，先约定归一化方式、权重和缺失值处理，不直接混算不同指标的原始分数。

## 示例：知识库问答评测

仓库附带一轮可检查的[离线模拟示例](examples/knowledge-base-eval/README.md)：

- 12 条样本，覆盖常规、复杂、边界和对抗/高风险输入。
- 3 个指标，分别使用二值、1–5 分和 GSB。
- 36 条评分记录，其中 33 条已模拟评分，3 条因缺少候选输出而保持待输出。
- 一条模拟答复接受了伪制度，触发硬门槛，演示高平均分无法抵消否决。

**示例中的知识库、输出、评分与业务阈值均为合成数据。未调用真实被测模型，不代表任何真实产品性能。** 目前已完成这一个文本问答场景的离线演练，其他产品类型仍需按真实任务验证。

## 校验与测试

### 自动检查

[GitHub Actions](https://github.com/xiehang0616/elk-ai-test-set/actions/workflows/validate.yml) 会在提交到 `main`、创建或更新 PR 时自动检查，也支持在 Actions 页面手动运行。

检查在 Python 3.9 和 3.13 上分别执行：校验器单元测试、示例题库字段与覆盖率检查、评分工作台与初始空表检查，以及示例跨表关联与汇总检查。各步骤只使用 Python 标准库，不调用模型或付费 API。

PR 页面可查看检查结果和失败日志。这些检查验证 CSV 与脚本的一致性，不验证真实模型效果、人工评分质量或 Excel 模板；是否将检查设为合并的强制条件，需要另行配置分支规则。

### 本地运行

以下命令在仓库根目录运行。

检查题库字段、样本数及指标覆盖：

```bash
python3 scripts/validate_eval_csv.py examples/knowledge-base-eval/dataset.csv \
  --schema dataset --metrics M1 M2 M3 --min-coverage 5 --expected-count 12
```

检查已填评分与初始空值：

```bash
python3 scripts/validate_eval_csv.py examples/knowledge-base-eval/workbench.csv \
  --schema workbench --expected-count 36

python3 scripts/validate_eval_csv.py examples/knowledge-base-eval/workbench-initial.csv \
  --schema workbench --initial --expected-count 36
```

运行脚本回归检查及示例关联检查：

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 examples/knowledge-base-eval/check_example.py
```

校验器检查字段、枚举、部分覆盖要求和评分依赖。样本比例、语义重复、事实依据、评分锚点与评审一致性仍需复核。通用校验器目前按单表运行；示例的 `check_example.py` 额外核对该示例的跨表关联和汇总结果。

## 目录

```text
elk-ai-test-set/
├── .github/workflows/validate.yml  # PR 与主分支的自动检查
├── SKILL.md                  # 技能入口与工作规则
├── README.md                 # 使用说明
├── LICENSE.md                # 许可证文本
├── agents/openai.yaml        # 显示名称与调用策略
├── references/               # 目标、字段与评分方法
├── assets/                   # 字段定义、CSV 表头与 Excel 模板
├── scripts/                  # CSV 校验器与回归检查
└── examples/knowledge-base-eval/  # 可检查的合成示例
```

## 修改与适配

- **改工作流程**：编辑 `SKILL.md`。
- **改覆盖设计或评分方法**：编辑 `references/` 中对应文档。
- **改字段**：先更新 `assets/schema.json`，同步 CSV 表头、Excel 模板、校验逻辑和示例。
- **改显示名称或调用策略**：编辑 `agents/openai.yaml`；调用名称还需与 `SKILL.md` 的 `name` 和目录名一致。

具体项目的业务指标应写在该项目目标卡和评分标准中，避免把一次业务需求变成所有产品都必须遵守的规则。

## 许可证

当前仓库包含 [PolyForm Noncommercial License 1.0.0](LICENSE.md) 许可证文本。
