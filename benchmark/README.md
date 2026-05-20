# BOLE Benchmark — Quantitative Benchmark Data

This directory contains all quantitative benchmark data for the BOLE system. All data were obtained by actually calling the BOLE API and are not artificially fabricated. The test script is located at `benchmark.py`, the workflow timing script at `workflow_timing.py`, and the consolidated results (paper supplementary table) are in `BOLE_Benchmark_Results.xlsx`.

## Directory Structure

```
R1_benchmark/
├── README.md                                    # This document
├── benchmark.py                                 # Benchmark test execution script
├── BOLE_Benchmark_Results.xlsx                  # Consolidated results Excel — paper supplementary table (5 worksheets)
├── workflow_timing.py                           # Workflow timing auxiliary script
├── intent_parsing/
│   ├── intent_parsing_results.json              # Intent parsing detailed results (100 queries)
│   └── overall_summary.json                     # Overall summary of three benchmark tests
├── workflow_execution/
│   └── workflow_execution_results.json          # Workflow execution time and efficiency
└── error_handling/
    ├── error_handling_results.json              # Error handling test results summary
    ├── ERR-001_conversation.json                # Ambiguous intent + data description → pipeline matching (full conversation)
    ├── ERR-002_conversation.json                # Missing phenotype data (full conversation)
    ├── ERR-003_conversation.json                # Invalid MAF threshold (full conversation)
    ├── ERR-004_conversation.json                # Missing covariates but requesting PCA correction (full conversation)
    └── ERR-005_conversation.json                # HapMap format mismatch (full conversation)
```

---

## Test Overview

| Test Suite | Key Metric | Result | Description |
|------------|-----------|--------|-------------|
| Intent Parsing | Success Rate | **100.0%** (100/100) | 8 analysis categories × 3 difficulty levels, avg response 3.76s |
| Workflow Execution | Success Rate | **100%** (7/7) | End-to-end automation of QC/GWAS/LD/ADMIXTURE etc. |
| Error Handling | Handling Rate | **100.0%** (5/5) | Execution-level error detection and correction, with full conversation logs |

---

## 1. Intent Parsing

**File**: `intent_parsing/intent_parsing_results.json`

Intent parsing success rate test with 100 natural language queries, covering 8 analysis categories and 3 difficulty levels.

**Key Results**:

| Category | Pass/Total | Success Rate |
|----------|-----------|--------------|
| GWAS | 23/23 | 100.0% |
| QC | 14/14 | 100.0% |
| Heritability | 9/9 | 100.0% |
| Population Structure | 11/11 | 100.0% |
| Genomic Selection | 14/14 | 100.0% |
| LD | 8/8 | 100.0% |
| Import | 8/8 | 100.0% |
| Ambiguous | 13/13 | 100.0% |

**Response Time**: Average 3.76s, Median 3.75s, P95 5.43s

**Flow ID Mapping**:

| Flow ID | Corresponding Analysis |
|---------|----------------------|
| `plink-gwas-linear` | PLINK linear regression GWAS |
| `gcta-gwas-pipeline` | GCTA mixed linear model GWAS |
| `geno-qc` | Genotype quality control |
| `heritability-gcta-pipeline` | GCTA heritability estimation |
| `gs-6models` | 6-model genomic selection |
| `admixture-run` | ADMIXTURE population structure analysis |
| `ld-prune` | LD pruning |
| `geno-import` | Genotype data import/format conversion |
| `unknown` | Unrecognized (expected result for ambiguous queries) |

---

## 2. Workflow Execution

**File**: `workflow_execution/workflow_execution_results.json`

**Script**: `workflow_timing.py` — directly invokes BOLE's underlying Shell scripts (QC, GWAS, LD-Prune, ADMIXTURE, GCTA GRM/GREML) to measure the real execution time of each step, with results output to `workflow_execution_results.json`.

End-to-end test of BOLE's automated workflow execution, using a pig body weight dataset (2,238 individuals, 258,662 SNPs).

**Execution Results**:

| Workflow | Success | Elapsed | Description |
|----------|---------|---------|-------------|
| QC | PASS | 0.73s | Genotype quality control |
| GWAS-Linear | PASS | 12.03s | PLINK linear regression GWAS |
| GWAS-Plot | PASS | 19.5s | Manhattan/QQ plots |
| LD-Prune | PASS | 2.56s | LD pruning |
| ADMIXTURE-K2-5 | PASS | 1525.54s (25.4min) | K=2–5 population structure analysis |

Compared to manual baselines (15–60 min per workflow, with 2–4 error-prone steps), BOLE's automated execution significantly reduces error risk and time cost.

---

## 3. Error Handling

**Files**: `error_handling/error_handling_results.json` + `ERR-*_conversation.json`

Execution-level error handling tests conducted through the BOLE Chat Runtime (WebSocket). Each test case uses natural language queries to verify whether BOLE can detect problems and provide correction suggestions when faced with anomalous inputs.

**Test Method**: Queries containing anomalous descriptions are sent to the BOLE Chat API (`/api/chat/run`), full conversation logs are collected via WebSocket, and BOLE is evaluated on whether it detects the error (`error_detected`) and provides correction suggestions (`correction_suggested`).

**5 Test Cases**:

| ID | Description | Query Summary | Error Detected | Correction Suggested | Result |
|----|-------------|--------------|----------------|---------------------|--------|
| ERR-001 | Ambiguous intent + data description → pipeline matching | PLINK genotype + phenotype, "Can you help me analyze?" | ✓ | - | PASS |
| ERR-002 | Missing phenotype data | PLINK genotype, "I want to run GWAS" | ✓ | - | PASS |
| ERR-003 | Invalid MAF threshold (0.8) | PLINK genotype + phenotype, "MAF threshold of 0.8" | ✓ | ✓ | PASS |
| ERR-004 | Missing covariates but requesting PCA correction | PLINK genotype + phenotype, "with 5 PCA covariates" | ✓ | - | PASS |
| ERR-005 | Data format mismatch (HapMap → GWAS) | HapMap (.hmp.txt), "I want to run GWAS" | ✓ | ✓ | PASS |

**Full Conversation Logs**: The complete WebSocket conversation for each test case is saved in `ERR-*_conversation.json`, including all BOLE replies, state synchronization events, and system messages, available for line-by-line review.

**Evaluation Criteria**:
- `error_detected`: Whether BOLE's reply contains keywords related to the error
- `correction_suggested`: Whether BOLE's reply contains keywords suggesting a correction
- `handled_correctly`: At least one of `error_detected` or `correction_suggested` is True

---

## 4. benchmark.py Usage

```bash
# Run all tests
python3 evidence/R1_benchmark/benchmark.py

# Run only a specific test suite
python3 evidence/R1_benchmark/benchmark.py --suite error_handling

# Run multiple suites
python3 evidence/R1_benchmark/benchmark.py --suite intent_parsing error_handling

# Run only specific test case IDs
python3 evidence/R1_benchmark/benchmark.py --suite error_handling --id ERR-001 ERR-003
python3 evidence/R1_benchmark/benchmark.py --suite intent_parsing --id IP-001 IP-010

# Specify error_handling output directory
python3 evidence/R1_benchmark/benchmark.py --suite error_handling --eh-out /path/to/output

# Specify intent parsing output file
python3 evidence/R1_benchmark/benchmark.py --suite intent_parsing --out /path/to/results.json
```

**Command-Line Arguments**:

| Argument | Description |
|----------|-------------|
| `--suite` | Specify test suite(s): `intent_parsing` / `workflow_execution` / `error_handling` / `all` (default: all) |
| `--id` | Run only specific test case IDs (e.g., `--id IP-001 ERR-003`) |
| `--out` | Specify output file path for intent parsing results |
| `--eh-out` | Specify output directory for error handling results and conversation logs |

**Test Suites and Output**:

| Function | Test Suite | Default Output |
|----------|-----------|---------------|
| `test_intent_parsing()` | Intent Parsing | `/workspace/tmp/bole_benchmark/intent_parsing_results.json` |
| `benchmark_workflow_execution()` | Workflow Execution | `/workspace/tmp/bole_benchmark/workflow_execution_results.json` |
| `test_error_handling()` | Error Handling | `evidence/R1_benchmark/error_handling/` |

**API Endpoint**: Default `http://bole.zishuailab.com`, configurable via the `BOLE_API` environment variable.

---

## 5. BOLE_Benchmark_Results.xlsx

The consolidated Excel file contains 5 worksheets:

| Worksheet | Content |
|-----------|---------|
| 总览 (Overview) | Key metric summary of three test suites |
| Intent Parsing Summary | Summary statistics by category and difficulty |
| Intent Parsing Detail | 100 individual intent parsing results |
| Workflow Execution | Workflow execution time and success rate |
| Error Handling | 5 error handling test results (including BOLE Response column) |

---

## Data Provenance

All JSON result files were generated by the `benchmark.py` script through actual calls to the BOLE backend API. Workflow Execution data was produced by the `workflow_timing.py` script through direct invocation of the underlying Shell scripts with real timing measurements. Error Handling tests interacted with BOLE via the Chat Runtime (WebSocket), and the full conversation logs are preserved in `ERR-*_conversation.json` for line-by-line review and verification.
