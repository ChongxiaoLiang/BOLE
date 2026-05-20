# BOLE Benchmark — 定量基准测试数据

本目录包含 BOLE 系统的全部定量基准测试数据。所有数据均通过实际调用 BOLE API 获取，非人工拟造。测试脚本位于 `benchmark.py`，工作流计时脚本位于 `workflow_timing.py`，汇总结果（论文附表）见 `BOLE_Benchmark_Results.xlsx`。

## 目录结构

```
R1_benchmark/
├── README.md                                    # 本文档
├── benchmark.py                                 # 基准测试执行脚本
├── BOLE_Benchmark_Results.xlsx                  # 汇总结果 Excel — 论文附表（5 个工作表）
├── workflow_timing.py                           # 工作流计时辅助脚本
├── intent_parsing/
│   ├── intent_parsing_results.json              # 意图解析详细结果（100 条）
│   └── overall_summary.json                     # 四项基准测试汇总摘要
├── workflow_execution/
│   └── workflow_execution_results.json          # 工作流执行时间与效率
└── error_handling/
    ├── error_handling_results.json              # 错误处理测试结果摘要
    ├── ERR-001_conversation.json                # 模糊意图+数据描述→流水线匹配 完整对话
    ├── ERR-002_conversation.json                # 缺少表型数据 完整对话
    ├── ERR-003_conversation.json                # 无效MAF阈值 完整对话
    ├── ERR-004_conversation.json                # 缺少协变量但要求PCA校正 完整对话
    └── ERR-005_conversation.json                # HapMap格式不匹配 完整对话
```

---

## 测试总览

| 测试套件 | 核心指标 | 结果 | 说明 |
|---------|---------|------|------|
| Intent Parsing | 成功率 | **100.0%** (100/100) | 8 类分析 × 3 级难度，平均响应 3.76s |
| Workflow Execution | 成功率 | **100%** (7/7) | QC/GWAS/LD/ADMIXTURE 等全流程自动化 |
| Error Handling | 处理率 | **100.0%** (5/5) | 执行层面错误检测与修正，含完整对话记录 |

---

## 1. Intent Parsing（意图解析）

**文件**：`intent_parsing/intent_parsing_results.json`

100 条自然语言查询的意图解析测试，覆盖 8 个分析类别和 3 个难度级别。

**核心结果**：

| 类别 | 通过/总数 | 成功率 |
|------|----------|--------|
| GWAS | 23/23 | 100.0% |
| QC | 14/14 | 100.0% |
| Heritability | 9/9 | 100.0% |
| Population Structure | 11/11 | 100.0% |
| Genomic Selection | 14/14 | 100.0% |
| LD | 8/8 | 100.0% |
| Import | 8/8 | 100.0% |
| Ambiguous | 13/13 | 100.0% |

**响应时间**：平均 3.76s，中位数 3.75s，P95 5.43s

**流程 ID 映射**：

| 流程 ID | 对应分析 |
|---------|---------|
| `plink-gwas-linear` | PLINK 线性回归 GWAS |
| `gcta-gwas-pipeline` | GCTA 混合线性模型 GWAS |
| `geno-qc` | 基因型数据质控 |
| `heritability-gcta-pipeline` | GCTA 遗传力估计 |
| `gs-6models` | 6 模型基因组选择 |
| `admixture-run` | ADMIXTURE 群体结构分析 |
| `ld-prune` | LD 修剪 |
| `geno-import` | 基因型数据导入/格式转换 |
| `unknown` | 无法识别（模糊查询预期结果） |

---

## 2. Workflow Execution（工作流执行）

**文件**：`workflow_execution/workflow_execution_results.json`

**脚本**：`workflow_timing.py` — 直接调用 BOLE 底层 Shell 脚本（QC、GWAS、LD-Prune、ADMIXTURE、GCTA GRM/GREML），测量每个步骤的真实执行耗时，结果输出到 `workflow_execution_results.json`。

BOLE 自动化执行全流程的端到端测试，数据集为猪体重数据（2238 个体，258662 SNPs）。

**执行结果**：

| 工作流 | 成功 | 耗时 | 说明 |
|--------|------|------|------|
| QC | PASS | 0.73s | 基因型质控 |
| GWAS-Linear | PASS | 12.03s | PLINK 线性回归 GWAS |
| GWAS-Plot | PASS | 19.5s | Manhattan/QQ 图 |
| LD-Prune | PASS | 2.56s | LD 修剪 |
| ADMIXTURE-K2-5 | PASS | 1525.54s (25.4min) | K=2~5 群体结构分析 |

对比手动基线（15~60 分钟/流程，含 2~4 个易出错步骤），BOLE 自动化执行显著降低了出错风险和时间成本。

---

## 3. Error Handling（错误处理与自我修正）

**文件**：`error_handling/error_handling_results.json` + `ERR-*_conversation.json`

通过 BOLE Chat Runtime（WebSocket）进行执行层面的错误处理测试。每个测试用例通过真实提问，验证 BOLE 在面对异常输入时能否检测问题并给出修正建议。

**测试方法**：向 BOLE Chat API（`/api/chat/run`）发送包含异常描述的查询，通过 WebSocket 收集完整对话记录，评估 BOLE 是否检测到错误（`error_detected`）并给出修正建议（`correction_suggested`）。

**5 个测试用例**：

| ID | 描述 | Query 摘要 | 错误检测 | 修正建议 | 结果 |
|----|------|-----------|---------|---------|------|
| ERR-001 | 模糊意图+数据描述→流水线匹配 | PLINK 基因型+表型，"Can you help me analyze?" | ✓ | - | PASS |
| ERR-002 | 缺少表型数据 | PLINK 基因型，"I want to run GWAS" | ✓ | - | PASS |
| ERR-003 | 无效 MAF 阈值(0.8) | PLINK 基因型+表型，"MAF threshold of 0.8" | ✓ | ✓ | PASS |
| ERR-004 | 缺少协变量但要求 PCA 校正 | PLINK 基因型+表型，"with 5 PCA covariates" | ✓ | - | PASS |
| ERR-005 | 数据格式不匹配（HapMap→GWAS） | HapMap (.hmp.txt)，"I want to run GWAS" | ✓ | ✓ | PASS |

**完整对话记录**：每个测试用例的完整 WebSocket 对话保存在 `ERR-*_conversation.json` 中，包含 BOLE 的所有回复、状态同步事件和系统消息，可供逐条审查。

**评估标准**：
- `error_detected`：BOLE 回复中是否包含与错误相关的关键词
- `correction_suggested`：BOLE 回复中是否包含修正建议关键词
- `handled_correctly`：`error_detected` 或 `correction_suggested` 至少一项为 True

---

## 4. benchmark.py 使用说明

```bash
# 运行全部测试
python3 evidence/R1_benchmark/benchmark.py

# 仅运行特定测试套件
python3 evidence/R1_benchmark/benchmark.py --suite error_handling

# 运行多个套件
python3 evidence/R1_benchmark/benchmark.py --suite intent_parsing error_handling

# 仅运行指定 ID 的测试
python3 evidence/R1_benchmark/benchmark.py --suite error_handling --id ERR-001 ERR-003
python3 evidence/R1_benchmark/benchmark.py --suite intent_parsing --id IP-001 IP-010

# 指定 error_handling 结果输出目录
python3 evidence/R1_benchmark/benchmark.py --suite error_handling --eh-out /path/to/output

# 指定意图解析结果输出文件
python3 evidence/R1_benchmark/benchmark.py --suite intent_parsing --out /path/to/results.json
```

**命令行参数**：

| 参数 | 说明 |
|------|------|
| `--suite` | 指定测试套件：`intent_parsing` / `workflow_execution` / `error_handling` / `all`（默认 all） |
| `--id` | 指定只运行特定测试用例 ID（如 `--id IP-001 ERR-003`） |
| `--out` | 指定意图解析结果的输出文件路径 |
| `--eh-out` | 指定 error_handling 结果和对话记录的输出目录 |

**测试套件与输出**：

| 函数 | 测试套件 | 默认输出 |
|------|---------|---------|
| `test_intent_parsing()` | 意图解析 | `/workspace/tmp/bole_benchmark/intent_parsing_results.json` |
| `benchmark_workflow_execution()` | 工作流执行 | `/workspace/tmp/bole_benchmark/workflow_execution_results.json` |
| `test_error_handling()` | 错误处理 | `evidence/R1_benchmark/error_handling/` |

**API 端点**：默认 `http://bole.zishuailab.com`，可通过环境变量 `BOLE_API` 修改。

---

## 5. BOLE_Benchmark_Results.xlsx

汇总 Excel 文件包含 5 个工作表：

| 工作表 | 内容 |
|--------|------|
| 总览 | 三项测试的核心指标汇总 |
| Intent Parsing Summary | 按类别和难度汇总统计 |
| Intent Parsing Detail | 100 条意图解析逐条结果 |
| Workflow Execution | 工作流执行时间和成功率 |
| Error Handling | 5 条错误处理测试结果（含 BOLE Response 列） |

---

## 数据溯源

所有 JSON 结果文件中的数据均由 `benchmark.py` 脚本通过实际调用 BOLE 后端 API 生成，Workflow Execution 数据由 `workflow_timing.py` 脚本通过直接调用底层 Shell 脚本测量生成。Error Handling 测试通过 Chat Runtime（WebSocket）与 BOLE 完整交互，对话记录保存在 `ERR-*_conversation.json` 中，可供逐条审查验证。
