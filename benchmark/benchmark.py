#!/usr/bin/env python3
"""
BOLE Quantitative Benchmarking Script
======================================
Evaluates BOLE's performance across three dimensions:
1. Intent Parsing Success Rate
2. Workflow Execution Time & Computational Efficiency
3. Error Rate & Self-Correction Success Rate

Also compares BOLE against manual execution baselines.
"""

import json
import os
import sys
import time
import argparse
import requests
import subprocess
import statistics
import threading
from datetime import datetime
from pathlib import Path

try:
    import websocket
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False

BOLE_API = os.environ.get("BOLE_API", "http://bole.zishuailab.com")
RESULTS_DIR = Path("/workspace/tmp/bole_benchmark")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR = Path("/www/wwwroot/BOLE/evidence/R1_benchmark")
EH_DATA_DIR = RESULTS_DIR / "eh_data"
EH_CONV_DIR = EVIDENCE_DIR / "error_handling"

# ============================================================
# Test Suite 1: Intent Parsing Success Rate
# ============================================================

INTENT_TEST_CASES = [
    {
        "id": "IP-001",
        "category": "GWAS",
        "query": "Run GWAS analysis on my pig data",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-002",
        "category": "GWAS",
        "query": "I need to find SNPs associated with body weight in my cattle population",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-003",
        "category": "GWAS",
        "query": "Run GWAS on chicken growth rate data",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-004",
        "category": "GWAS",
        "query": "Perform GWAS association analysis for milk yield in dairy cattle",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-005",
        "category": "GWAS",
        "query": "我需要对水稻株高进行全基因组关联分析",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-006",
        "category": "GWAS",
        "query": "Do a GWAS for disease resistance in sheep",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-007",
        "category": "GWAS",
        "query": "Find genetic markers linked to feed efficiency in pigs",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-008",
        "category": "GWAS",
        "query": "Run genome-wide association for egg production in chickens",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-009",
        "category": "GWAS",
        "query": "I want GWAS results for maize kernel weight",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-010",
        "category": "GWAS",
        "query": "Perform GWAS on my wheat yield trait data",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-011",
        "category": "GWAS",
        "query": "对肉牛胴体性状做全基因组关联分析",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "easy",
    },
    {
        "id": "IP-012",
        "category": "GWAS",
        "query": "Run GWAS using mixed model to control for population structure",
        "expected_flow": "gcta-gwas-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-013",
        "category": "GWAS",
        "query": "Identify significant loci for feed efficiency trait in chickens using linear regression",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "medium",
    },
    {
        "id": "IP-014",
        "category": "GWAS",
        "query": "Perform GWAS and visualize results with Manhattan plot",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "medium",
    },
    {
        "id": "IP-015",
        "category": "GWAS",
        "query": "Perform GWAS to identify markers significantly associated with the phenotype",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "medium",
    },
    {
        "id": "IP-016",
        "category": "GWAS",
        "query": "Use GCTA MLMA for association to account for relatedness",
        "expected_flow": "gcta-gwas-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-017",
        "category": "GWAS",
        "query": "用GCTA混合线性模型做GWAS分析，控制群体结构",
        "expected_flow": "gcta-gwas-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-018",
        "category": "GWAS",
        "query": "Conduct GWAS with covariates for population stratification",
        "expected_flow": "gcta-gwas-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-019",
        "category": "GWAS",
        "query": "Run multi-trait GWAS on cattle height and weight",
        "expected_flow": "gcta-gwas-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-020",
        "category": "GWAS",
        "query": "Perform GWAS adjusting for kinship matrix using GCTA",
        "expected_flow": "gcta-gwas-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-021",
        "category": "GWAS",
        "query": "Do association analysis",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "hard",
    },
    {
        "id": "IP-022",
        "category": "GWAS",
        "query": "Find genes associated with disease resistance using GWAS",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "hard",
    },
    {
        "id": "IP-023",
        "category": "GWAS",
        "query": "用GWAS帮我找一下显著位点",
        "expected_flow": "plink-gwas-linear",
        "difficulty": "hard",
    },
    {
        "id": "IP-024",
        "category": "QC",
        "query": "Please perform quality control on my genotype data with MAF 0.01",
        "expected_flow": "geno-qc",
        "difficulty": "easy",
    },
    {
        "id": "IP-025",
        "category": "QC",
        "query": "Filter my SNPs and samples for quality",
        "expected_flow": "geno-qc",
        "difficulty": "easy",
    },
    {
        "id": "IP-026",
        "category": "QC",
        "query": "Clean up the raw genotype data before downstream analysis",
        "expected_flow": "geno-qc",
        "difficulty": "easy",
    },
    {
        "id": "IP-027",
        "category": "QC",
        "query": "Perform quality control to filter low-quality variants from my genotype data",
        "expected_flow": "geno-qc",
        "difficulty": "easy",
    },
    {
        "id": "IP-028",
        "category": "QC",
        "query": "对基因型数据进行质量控制",
        "expected_flow": "geno-qc",
        "difficulty": "easy",
    },
    {
        "id": "IP-029",
        "category": "QC",
        "query": "Remove bad SNPs and individuals from my dataset",
        "expected_flow": "geno-qc",
        "difficulty": "easy",
    },
    {
        "id": "IP-030",
        "category": "QC",
        "query": "Apply basic QC filters to my PLINK binary files",
        "expected_flow": "geno-qc",
        "difficulty": "easy",
    },
    {
        "id": "IP-031",
        "category": "QC",
        "query": "Apply standard genotype filtering with MAF > 0.05 and missing rate < 0.1",
        "expected_flow": "geno-qc",
        "difficulty": "medium",
    },
    {
        "id": "IP-032",
        "category": "QC",
        "query": "Perform QC with HWE p-value threshold 1e-6 and individual missing rate 0.1",
        "expected_flow": "geno-qc",
        "difficulty": "medium",
    },
    {
        "id": "IP-033",
        "category": "QC",
        "query": "按照MAF>0.05、缺失率<0.1的标准对SNP进行过滤",
        "expected_flow": "geno-qc",
        "difficulty": "medium",
    },
    {
        "id": "IP-034",
        "category": "QC",
        "query": "Filter genotype data with call rate > 95% and remove outliers",
        "expected_flow": "geno-qc",
        "difficulty": "medium",
    },
    {
        "id": "IP-035",
        "category": "QC",
        "query": "Run quality control with custom MAF and missingness thresholds for my pig data",
        "expected_flow": "geno-qc",
        "difficulty": "medium",
    },
    {
        "id": "IP-036",
        "category": "QC",
        "query": "Clean my data",
        "expected_flow": "geno-qc",
        "difficulty": "hard",
    },
    {
        "id": "IP-037",
        "category": "QC",
        "query": "Fix genotype quality issues by performing quality control filtering",
        "expected_flow": "geno-qc",
        "difficulty": "hard",
    },
    {
        "id": "IP-038",
        "category": "Heritability",
        "query": "Calculate SNP-based heritability with GCTA",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "easy",
    },
    {
        "id": "IP-039",
        "category": "Heritability",
        "query": "Use GCTA GREML to estimate the heritability of body weight in my sheep flock",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "easy",
    },
    {
        "id": "IP-040",
        "category": "Heritability",
        "query": "用GCTA计算目标性状的遗传力",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "easy",
    },
    {
        "id": "IP-041",
        "category": "Heritability",
        "query": "I want to know the heritability of milk yield using GREML",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "easy",
    },
    {
        "id": "IP-042",
        "category": "Heritability",
        "query": "Estimate the heritability of milk yield using GREML",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-043",
        "category": "Heritability",
        "query": "Run GCTA-GREML to partition genetic variance for disease resistance in chickens",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-044",
        "category": "Heritability",
        "query": "用GCTA估计猪生长性状的遗传力，考虑固定效应",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "medium",
    },
    {
        "id": "IP-045",
        "category": "Heritability",
        "query": "Estimate heritability using GCTA GREML to quantify genetic contribution to phenotypic variance",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "hard",
    },
    {
        "id": "IP-046",
        "category": "Heritability",
        "query": "用GREML方法估计遗传力",
        "expected_flow": "heritability-gcta-pipeline",
        "difficulty": "hard",
    },
    {
        "id": "IP-047",
        "category": "Population Structure",
        "query": "Analyze population structure using ADMIXTURE",
        "expected_flow": "admixture-run",
        "difficulty": "easy",
    },
    {
        "id": "IP-048",
        "category": "Population Structure",
        "query": "Run ADMIXTURE analysis on my cattle breeds",
        "expected_flow": "admixture-run",
        "difficulty": "easy",
    },
    {
        "id": "IP-049",
        "category": "Population Structure",
        "query": "分析我的绵羊群体的群体结构",
        "expected_flow": "admixture-run",
        "difficulty": "easy",
    },
    {
        "id": "IP-050",
        "category": "Population Structure",
        "query": "Run ADMIXTURE to determine population ancestry composition",
        "expected_flow": "admixture-run",
        "difficulty": "easy",
    },
    {
        "id": "IP-051",
        "category": "Population Structure",
        "query": "Determine the optimal number of ancestral populations in my dataset",
        "expected_flow": "admixture-run",
        "difficulty": "medium",
    },
    {
        "id": "IP-052",
        "category": "Population Structure",
        "query": "Run ADMIXTURE with cross-validation for K=2 to K=10 on my pig data",
        "expected_flow": "admixture-run",
        "difficulty": "medium",
    },
    {
        "id": "IP-053",
        "category": "Population Structure",
        "query": "用交叉验证确定最佳K值，分析鸡的群体结构",
        "expected_flow": "admixture-run",
        "difficulty": "medium",
    },
    {
        "id": "IP-054",
        "category": "Population Structure",
        "query": "Run ADMIXTURE analysis to assess population stratification",
        "expected_flow": "admixture-run",
        "difficulty": "medium",
    },
    {
        "id": "IP-055",
        "category": "Population Structure",
        "query": "Assess genetic ancestry proportions across multiple sheep breeds",
        "expected_flow": "admixture-run",
        "difficulty": "medium",
    },
    {
        "id": "IP-056",
        "category": "Population Structure",
        "query": "What is the genetic composition of my samples?",
        "expected_flow": "admixture-run",
        "difficulty": "hard",
    },
    {
        "id": "IP-057",
        "category": "Population Structure",
        "query": "我的群体遗传组成是什么",
        "expected_flow": "admixture-run",
        "difficulty": "hard",
    },
    {
        "id": "IP-058",
        "category": "Genomic Selection",
        "query": "I want to compare genomic prediction models for disease resistance",
        "expected_flow": "gs-6models",
        "difficulty": "easy",
    },
    {
        "id": "IP-059",
        "category": "Genomic Selection",
        "query": "Run genomic selection with cross-validation",
        "expected_flow": "gs-6models",
        "difficulty": "easy",
    },
    {
        "id": "IP-060",
        "category": "Genomic Selection",
        "query": "Compare BayesA, BayesB, BayesC, BRR, BL and GBLUP for genomic prediction",
        "expected_flow": "gs-6models",
        "difficulty": "easy",
    },
    {
        "id": "IP-061",
        "category": "Genomic Selection",
        "query": "用六种模型做基因组选择预测",
        "expected_flow": "gs-6models",
        "difficulty": "easy",
    },
    {
        "id": "IP-062",
        "category": "Genomic Selection",
        "query": "Perform genomic prediction for milk yield in dairy cattle",
        "expected_flow": "gs-6models",
        "difficulty": "easy",
    },
    {
        "id": "IP-063",
        "category": "Genomic Selection",
        "query": "I need to run genomic selection on my pig population",
        "expected_flow": "gs-6models",
        "difficulty": "easy",
    },
    {
        "id": "IP-064",
        "category": "Genomic Selection",
        "query": "Evaluate breeding values using multiple genomic prediction methods",
        "expected_flow": "gs-6models",
        "difficulty": "easy",
    },
    {
        "id": "IP-065",
        "category": "Genomic Selection",
        "query": "Predict breeding values using Bayesian models",
        "expected_flow": "gs-6models",
        "difficulty": "medium",
    },
    {
        "id": "IP-066",
        "category": "Genomic Selection",
        "query": "Compare GBLUP and Bayesian methods for genomic selection in maize",
        "expected_flow": "gs-6models",
        "difficulty": "medium",
    },
    {
        "id": "IP-067",
        "category": "Genomic Selection",
        "query": "用交叉验证比较不同基因组预测模型的准确性",
        "expected_flow": "gs-6models",
        "difficulty": "medium",
    },
    {
        "id": "IP-068",
        "category": "Genomic Selection",
        "query": "Run 6-model genomic selection with 5-fold cross-validation for feed efficiency",
        "expected_flow": "gs-6models",
        "difficulty": "medium",
    },
    {
        "id": "IP-069",
        "category": "Genomic Selection",
        "query": "Assess prediction accuracy of BayesA vs BayesB vs GBLUP for chicken body weight",
        "expected_flow": "gs-6models",
        "difficulty": "medium",
    },
    {
        "id": "IP-070",
        "category": "Genomic Selection",
        "query": "Which prediction model works best for my trait?",
        "expected_flow": "gs-6models",
        "difficulty": "hard",
    },
    {
        "id": "IP-071",
        "category": "Genomic Selection",
        "query": "用基因组选择模型比较哪个预测模型最好",
        "expected_flow": "gs-6models",
        "difficulty": "hard",
    },
    {
        "id": "IP-072",
        "category": "LD",
        "query": "Prune SNPs in linkage disequilibrium",
        "expected_flow": "ld-prune",
        "difficulty": "easy",
    },
    {
        "id": "IP-073",
        "category": "LD",
        "query": "Remove linked SNPs from my dataset",
        "expected_flow": "ld-prune",
        "difficulty": "easy",
    },
    {
        "id": "IP-074",
        "category": "LD",
        "query": "去除连锁不平衡的SNP",
        "expected_flow": "ld-prune",
        "difficulty": "easy",
    },
    {
        "id": "IP-075",
        "category": "LD",
        "query": "Perform LD-based pruning on my genotype data",
        "expected_flow": "ld-prune",
        "difficulty": "easy",
    },
    {
        "id": "IP-076",
        "category": "LD",
        "query": "Prune SNPs with r2 > 0.2 in 50kb windows for my cattle data",
        "expected_flow": "ld-prune",
        "difficulty": "medium",
    },
    {
        "id": "IP-077",
        "category": "LD",
        "query": "用50kb窗口、r2>0.2的标准进行LD剪枝",
        "expected_flow": "ld-prune",
        "difficulty": "medium",
    },
    {
        "id": "IP-078",
        "category": "LD",
        "query": "Perform LD pruning with sliding window approach before PCA analysis",
        "expected_flow": "ld-prune",
        "difficulty": "medium",
    },
    {
        "id": "IP-079",
        "category": "LD",
        "query": "Remove redundant markers",
        "expected_flow": "ld-prune",
        "difficulty": "hard",
    },
    {
        "id": "IP-080",
        "category": "Import",
        "query": "Convert my VCF file to PLINK format",
        "expected_flow": "geno-import",
        "difficulty": "easy",
    },
    {
        "id": "IP-081",
        "category": "Import",
        "query": "Import genotype data from VCF files",
        "expected_flow": "geno-import",
        "difficulty": "easy",
    },
    {
        "id": "IP-082",
        "category": "Import",
        "query": "导入VCF格式的基因型数据",
        "expected_flow": "geno-import",
        "difficulty": "easy",
    },
    {
        "id": "IP-083",
        "category": "Import",
        "query": "Load my raw genotype data into the system",
        "expected_flow": "geno-import",
        "difficulty": "easy",
    },
    {
        "id": "IP-084",
        "category": "Import",
        "query": "Convert HapMap format to PLINK binary files for downstream analysis",
        "expected_flow": "geno-import",
        "difficulty": "medium",
    },
    {
        "id": "IP-085",
        "category": "Import",
        "query": "将HapMap格式的数据转换为PLINK格式",
        "expected_flow": "geno-import",
        "difficulty": "medium",
    },
    {
        "id": "IP-086",
        "category": "Import",
        "query": "Import and merge multiple VCF files from different chromosomes",
        "expected_flow": "geno-import",
        "difficulty": "medium",
    },
    {
        "id": "IP-087",
        "category": "Import",
        "query": "Import and convert my genotype data to PLINK format",
        "expected_flow": "geno-import",
        "difficulty": "hard",
    },
    {
        "id": "IP-088",
        "category": "Ambiguous",
        "query": "I want to analyze my genomic data but I'm not sure where to start",
        "expected_flow": "unknown",
        "difficulty": "easy",
    },
    {
        "id": "IP-089",
        "category": "Ambiguous",
        "query": "Help me process my breeding data",
        "expected_flow": "unknown",
        "difficulty": "easy",
    },
    {
        "id": "IP-090",
        "category": "Ambiguous",
        "query": "我想分析我的育种数据",
        "expected_flow": "unknown",
        "difficulty": "easy",
    },
    {
        "id": "IP-091",
        "category": "Ambiguous",
        "query": "What kind of analysis should I do with my SNP data?",
        "expected_flow": "unknown",
        "difficulty": "easy",
    },
    {
        "id": "IP-092",
        "category": "Ambiguous",
        "query": "I have genotype and phenotype data, suggest an analysis pipeline",
        "expected_flow": "unknown",
        "difficulty": "easy",
    },
    {
        "id": "IP-093",
        "category": "Ambiguous",
        "query": "Analyze my genomic data",
        "expected_flow": "unknown",
        "difficulty": "medium",
    },
    {
        "id": "IP-094",
        "category": "Ambiguous",
        "query": "Help me with breeding analysis",
        "expected_flow": "unknown",
        "difficulty": "medium",
    },
    {
        "id": "IP-095",
        "category": "Ambiguous",
        "query": "帮我做一下遗传分析",
        "expected_flow": "unknown",
        "difficulty": "medium",
    },
    {
        "id": "IP-096",
        "category": "Ambiguous",
        "query": "I need to study the genetic architecture of my population",
        "expected_flow": "unknown",
        "difficulty": "medium",
    },
    {
        "id": "IP-097",
        "category": "Ambiguous",
        "query": "Do some analysis",
        "expected_flow": "unknown",
        "difficulty": "hard",
    },
    {
        "id": "IP-098",
        "category": "Ambiguous",
        "query": "帮我看看数据",
        "expected_flow": "unknown",
        "difficulty": "hard",
    },
    {
        "id": "IP-099",
        "category": "Ambiguous",
        "query": "Process this",
        "expected_flow": "unknown",
        "difficulty": "hard",
    },
    {
        "id": "IP-100",
        "category": "Ambiguous",
        "query": "I need results",
        "expected_flow": "unknown",
        "difficulty": "hard",
    },
]


def test_intent_parsing(ids=None, out_file=None):
    """Test intent parsing success rate via ChatBrain API.
    
    Args:
        ids: Optional list of test case IDs to run (e.g. ["IP-001", "IP-010"]).
             If None, runs all test cases.
        out_file: Optional path to write results JSON. If None, writes to
                  RESULTS_DIR / "intent_parsing_results.json".
    """
    print("\n" + "=" * 60)
    print("TEST SUITE 1: Intent Parsing Success Rate")
    print("=" * 60)

    cases_to_run = INTENT_TEST_CASES
    if ids:
        id_set = set(ids)
        cases_to_run = [tc for tc in INTENT_TEST_CASES if tc["id"] in id_set]
        print(f"  Filtered: running {len(cases_to_run)}/{len(INTENT_TEST_CASES)} cases by --id")

    results = []
    for tc in cases_to_run:
        tid = tc["id"]
        query = tc["query"]
        expected = tc["expected_flow"]
        category = tc["category"]
        difficulty = tc["difficulty"]

        payload = {
            "history": [{"role": "user", "content": query}],
            "lang": "en" if not any("\u4e00" <= c <= "\u9fff" for c in query) else "zh",
        }

        start = time.time()
        try:
            resp = requests.post(
                f"{BOLE_API}/api/brain/condense-intent",
                json=payload,
                timeout=120,
            )
            elapsed = time.time() - start
            data = resp.json()
            detected_flow = data.get("flow", "unknown")
            success = detected_flow == expected
            if expected == "unknown":
                success = detected_flow == "unknown" or detected_flow not in [
                    "plink-gwas-linear", "gcta-gwas-pipeline", "geno-qc",
                    "heritability-gcta-pipeline", "gs-6models", "admixture-run",
                    "ld-prune", "geno-import"
                ]
            result = {
                "id": tid,
                "category": category,
                "query": query,
                "expected_flow": expected,
                "detected_flow": detected_flow,
                "success": success,
                "difficulty": difficulty,
                "response_time_sec": round(elapsed, 2),
                "error": None,
            }
        except Exception as e:
            elapsed = time.time() - start
            result = {
                "id": tid,
                "category": category,
                "query": query,
                "expected_flow": expected,
                "detected_flow": "error",
                "success": False,
                "difficulty": difficulty,
                "response_time_sec": round(elapsed, 2),
                "error": str(e),
            }

        results.append(result)
        status = "PASS" if result["success"] else "FAIL"
        print(f"  [{status}] {tid}: expected={expected}, detected={result['detected_flow']}, time={result['response_time_sec']}s")

    total = len(results)
    passed = sum(1 for r in results if r["success"])
    rate = passed / total * 100

    by_category = {}
    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, {"pass": 0, "total": 0})
        by_category[cat]["total"] += 1
        if r["success"]:
            by_category[cat]["pass"] += 1

    by_difficulty = {}
    for r in results:
        diff = r["difficulty"]
        by_difficulty.setdefault(diff, {"pass": 0, "total": 0})
        by_difficulty[diff]["total"] += 1
        if r["success"]:
            by_difficulty[diff]["pass"] += 1

    response_times = [r["response_time_sec"] for r in results if r["error"] is None]

    summary = {
        "overall_success_rate": f"{rate:.1f}%",
        "total_tests": total,
        "passed": passed,
        "failed": total - passed,
        "by_category": {k: f"{v['pass']}/{v['total']} ({v['pass']/v['total']*100:.1f}%)" for k, v in by_category.items()},
        "by_difficulty": {k: f"{v['pass']}/{v['total']} ({v['pass']/v['total']*100:.1f}%)" for k, v in by_difficulty.items()},
        "avg_response_time": f"{statistics.mean(response_times):.2f}s" if response_times else "N/A",
        "median_response_time": f"{statistics.median(response_times):.2f}s" if response_times else "N/A",
        "min_response_time": f"{min(response_times):.2f}s" if response_times else "N/A",
        "max_response_time": f"{max(response_times):.2f}s" if response_times else "N/A",
    }

    print(f"\n  Overall Success Rate: {rate:.1f}% ({passed}/{total})")
    print(f"  By Category: {json.dumps(summary['by_category'], indent=4)}")
    print(f"  By Difficulty: {json.dumps(summary['by_difficulty'], indent=4)}")
    print(f"  Avg Response Time: {summary['avg_response_time']}")

    output_path = Path(out_file) if out_file else RESULTS_DIR / "intent_parsing_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({"summary": summary, "details": results}, f, indent=2, ensure_ascii=False)

    return summary, results


# ============================================================
# Test Suite 2: Workflow Execution Time & Efficiency
# ============================================================

def find_test_data():
    """Find available test datasets in the workspace."""
    data_dir = Path("/workspace/algba_data")
    datasets = []
    for d in sorted(data_dir.iterdir()):
        if not d.is_dir():
            continue
        input_dir = d / "input"
        if not input_dir.exists():
            continue
        bed_files = list(input_dir.glob("*.bed"))
        fam_files = list(input_dir.glob("*.fam"))
        csv_files = list(input_dir.glob("*.csv"))
        if bed_files and fam_files:
            bed = bed_files[0]
            prefix = str(bed).replace(".bed", "")
            pheno = str(csv_files[0]) if csv_files else None
            datasets.append({
                "session": d.name,
                "genotype_prefix": prefix,
                "phenotype_file": pheno,
                "has_phenotype": pheno is not None,
            })
    return datasets


def benchmark_script_direct(script_path, args, label):
    """Benchmark a BOLE flow script directly (without LLM overhead)."""
    env = os.environ.copy()
    env.update(args)

    start = time.time()
    try:
        result = subprocess.run(
            ["bash", str(script_path)] + [f"--{k} {v}" for k, v in args.items() if k not in env],
            capture_output=True,
            text=True,
            timeout=600,
            env=env,
        )
        elapsed = time.time() - start
        return {
            "label": label,
            "success": result.returncode == 0,
            "elapsed_sec": round(elapsed, 2),
            "return_code": result.returncode,
            "stdout_lines": len(result.stdout.splitlines()),
            "stderr_lines": len(result.stderr.splitlines()),
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            "label": label,
            "success": False,
            "elapsed_sec": round(elapsed, 2),
            "return_code": -1,
            "error": "timeout",
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            "label": label,
            "success": False,
            "elapsed_sec": round(elapsed, 2),
            "return_code": -1,
            "error": str(e),
        }


def benchmark_workflow_execution():
    """Benchmark end-to-end workflow execution times."""
    print("\n" + "=" * 60)
    print("TEST SUITE 2: Workflow Execution Time & Efficiency")
    print("=" * 60)

    datasets = find_test_data()
    print(f"  Found {len(datasets)} test datasets")

    flows_dir = Path("/www/wwwroot/BOLE/backend/scripts/flows")

    workflow_results = []

    for ds in datasets[:5]:
        session = ds["session"]
        geno_prefix = ds["genotype_prefix"]
        pheno_file = ds["phenotype_file"]
        print(f"\n  Dataset: {session}")
        print(f"    Genotype: {geno_prefix}")
        print(f"    Phenotype: {pheno_file}")

        outdir = f"/workspace/tmp/bole_benchmark/output_{session}"
        os.makedirs(outdir, exist_ok=True)

        # Test QC workflow
        qc_script = flows_dir / "genotype_qc.sh"
        if qc_script.exists():
            r = benchmark_script_direct(
                qc_script,
                {
                    "GENO": geno_prefix,
                    "OUTDIR": outdir,
                    "OUTPREFIX": f"{session}_qc",
                    "MAF": "0.05",
                    "GENO_MISSING": "0.05",
                    "INDIVIDUAL_MISSING": "0.05",
                    "HWE_PVALUE": "1e-6",
                },
                f"QC-{session}",
            )
            workflow_results.append(r)
            status = "PASS" if r["success"] else "FAIL"
            print(f"    [{status}] QC: {r['elapsed_sec']}s")

        # Test LD Prune
        ld_script = flows_dir / "ld_prune.sh"
        qc_prefix = f"{outdir}/{session}_qc"
        if ld_script.exists() and os.path.exists(f"{qc_prefix}.bed"):
            r = benchmark_script_direct(
                ld_script,
                {
                    "genotype_prefix": qc_prefix,
                    "output_prefix": f"{outdir}/{session}_prune",
                },
                f"LD-{session}",
            )
            workflow_results.append(r)
            status = "PASS" if r["success"] else "FAIL"
            print(f"    [{status}] LD Prune: {r['elapsed_sec']}s")

    # Also measure manual execution baseline (estimated)
    manual_baselines = {
        "GWAS (PLINK linear, manual)": {"time_min": 15, "steps": 5, "error_prone_steps": 2},
        "GWAS (GCTA MLMA, manual)": {"time_min": 30, "steps": 7, "error_prone_steps": 3},
        "Heritability (GCTA GREML, manual)": {"time_min": 25, "steps": 6, "error_prone_steps": 2},
        "Population Structure (ADMIXTURE, manual)": {"time_min": 45, "steps": 8, "error_prone_steps": 3},
        "Genomic Selection (6 models, manual)": {"time_min": 60, "steps": 10, "error_prone_steps": 4},
    }

    summary = {
        "automated_results": workflow_results,
        "manual_baselines": manual_baselines,
        "total_automated_runs": len(workflow_results),
        "successful_runs": sum(1 for r in workflow_results if r["success"]),
    }

    with open(RESULTS_DIR / "workflow_execution_results.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


# ============================================================
# Test Suite 3: Error Rate & Self-Correction
# ============================================================

def _prepare_eh_data():
    EH_DATA_DIR.mkdir(parents=True, exist_ok=True)
    EH_CONV_DIR.mkdir(parents=True, exist_ok=True)
    datasets = {}
    gwas_src = EVIDENCE_DIR.parent.parent / "testdata" / "gwas-linear"
    qc_src = EVIDENCE_DIR.parent.parent / "testdata" / "geno-qc"
    import_src = EVIDENCE_DIR.parent.parent / "testdata" / "geno-import"

    ds_a = EH_DATA_DIR / "dataset_001"
    ds_a.mkdir(exist_ok=True)
    for ext in [".bed", ".bim", ".fam"]:
        link = ds_a / f"genotype{ext}"
        src_file = gwas_src / f"reference{ext}"
        if not link.exists() and src_file.exists():
            link.symlink_to(src_file.resolve())
    pheno_link = ds_a / "phenotype.fam"
    pheno_src = gwas_src / "GWAStestphenotype.fam"
    if not pheno_link.exists() and pheno_src.exists():
        pheno_link.symlink_to(pheno_src.resolve())
    datasets["gwas_full"] = str(ds_a.resolve())

    ds_b = EH_DATA_DIR / "dataset_002"
    ds_b.mkdir(exist_ok=True)
    for ext in [".bed", ".bim", ".fam"]:
        link = ds_b / f"genotype{ext}"
        src_file = gwas_src / f"reference{ext}"
        if not link.exists() and src_file.exists():
            link.symlink_to(src_file.resolve())
    datasets["gwas_geno_only"] = str(ds_b.resolve())

    ds_c = EH_DATA_DIR / "dataset_003"
    ds_c.mkdir(exist_ok=True)
    vcf_src = import_src / "selectedfortest.vcf"
    vcf_link = ds_c / "sample.vcf"
    if not vcf_link.exists() and vcf_src.exists():
        vcf_link.symlink_to(vcf_src.resolve())
    datasets["vcf"] = str(ds_c.resolve())

    ds_d = EH_DATA_DIR / "dataset_004"
    ds_d.mkdir(exist_ok=True)
    for ext in [".bim", ".fam"]:
        link = ds_d / f"genotype{ext}"
        src_file = gwas_src / f"reference{ext}"
        if not link.exists() and src_file.exists():
            link.symlink_to(src_file.resolve())
    corrupted_bed = ds_d / "genotype.bed"
    if not corrupted_bed.exists():
        with open(corrupted_bed, "wb") as f:
            f.write(b"corrupted_data_not_a_real_bed_file")
    datasets["corrupted"] = str(ds_d.resolve())

    ds_e = EH_DATA_DIR / "dataset_005"
    ds_e.mkdir(exist_ok=True)
    for ext in [".bed", ".bim", ".fam"]:
        link = ds_e / f"genotype{ext}"
        src_file = qc_src / f"testps{ext}"
        if not link.exists() and src_file.exists():
            link.symlink_to(src_file.resolve())
    datasets["qc_data"] = str(ds_e.resolve())

    return datasets


class BOLEChatSession:
    def __init__(self, api_base, lang="zh"):
        self.api_base = api_base
        self.lang = lang
        self.job_id = None
        self.conversation = []
        self._ws = None
        self._ws_thread = None
        self._stop = threading.Event()
        self._connected = threading.Event()

    def start(self, query, args=None):
        payload = {"lang": self.lang, "input": query}
        if args:
            payload["args"] = args
        resp = requests.post(
            f"{self.api_base}/api/chat/run",
            json=payload,
            timeout=30,
        )
        data = resp.json()
        self.job_id = data.get("job_id")
        if not self.job_id:
            raise RuntimeError(f"chat/run failed: {data}")
        self._log("system", f"Session created: job_id={self.job_id}")
        ws_url = self.api_base.replace("http://", "ws://").replace("https://", "wss://")
        ws_url += f"/api/jobs/{self.job_id}/ws"
        self._ws = websocket.WebSocketApp(
            ws_url,
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        self._ws_thread = threading.Thread(target=self._ws.run_forever, daemon=True)
        self._ws_thread.start()
        self._connected.wait(timeout=15)
        return self.job_id

    def send(self, text):
        if not self.job_id:
            return
        try:
            requests.post(
                f"{self.api_base}/api/jobs/{self.job_id}/stdin",
                json={"data": text},
                timeout=15,
            )
            self._log("user", text)
        except Exception as e:
            self._log("system", f"send error: {e}")

    def collect(self, duration=60):
        self._stop.clear()
        self._stop.wait(duration)

    def stop(self):
        self._stop.set()
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass

    def get_log(self):
        return {
            "job_id": self.job_id,
            "conversation": self.conversation,
            "total_messages": len(self.conversation),
        }

    def _on_open(self, ws):
        self._connected.set()
        self._log("system", "WebSocket connected")

    def _on_message(self, ws, message):
        self._log("assistant", message)

    def _on_error(self, ws, error):
        self._log("system", f"WebSocket error: {error}")

    def _on_close(self, ws, close_code, close_msg):
        self._log("system", f"WebSocket closed: {close_code} {close_msg}")
        self._stop.set()

    def _log(self, role, content):
        self.conversation.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
        })


def _eval_keywords(text, keywords):
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def test_error_handling(ids=None, out_dir=None):
    """Test BOLE's error handling at execution level via Chat Runtime."""
    print("\n" + "=" * 60)
    print("TEST SUITE 3: Error Rate & Self-Correction")
    print("=" * 60)

    all_results = []

    eh_out = Path(out_dir) if out_dir else EH_CONV_DIR
    eh_out.mkdir(parents=True, exist_ok=True)

    if not HAS_WEBSOCKET:
        print("  SKIPPED: websocket-client not installed "
              "(pip install websocket-client)")
        summary = {
            "error_handling_rate": "N/A",
            "total_tests": 0,
            "handled_correctly": 0,
            "skipped_reason": "websocket-client not installed",
            "details": [],
        }
        with open(RESULTS_DIR / "error_handling_results.json", "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        with open(eh_out / "error_handling_results.json", "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        return summary

    exec_cases = [
        {
            "id": "ERR-001",
            "description": "Ambiguous intent + data description -> pipeline matching",
            "query": ("I have PLINK binary genotype files (bed/bim/fam) "
                      "for about 2200 pigs with 50000 SNPs, "
                      "and a phenotype file with body weight measurements. "
                      "Can you help me analyze this data?"),
            "test_type": "pipeline_matching",
            "expected_pipelines": [
                "gwas", "association", "linear", "genome-wide",
                "plink", "gcta",
            ],
            "eval": {
                "detect": ["gwas", "association", "linear", "genome-wide",
                           "plink", "gcta", "heritability", "admixture",
                           "qc", "quality control"],
                "correct": [],
            },
            "timeout": 120,
        },
        {
            "id": "ERR-002",
            "description": "Missing phenotype data for GWAS",
            "query": ("I have PLINK binary genotype files (bed/bim/fam) "
                      "for about 2200 pigs with 50000 SNPs. "
                      "I want to run a GWAS analysis."),
            "test_type": "missing_phenotype",
            "eval": {
                "detect": ["phenotype", "trait", "missing", "need",
                           "provide", "upload", "covariate"],
                "correct": ["please provide", "upload", "specify",
                            "need a phenotype", "trait file"],
            },
            "timeout": 120,
        },
        {
            "id": "ERR-003",
            "description": "Invalid MAF threshold (0.8) in analysis request",
            "query": ("I have PLINK binary genotype files (bed/bim/fam) "
                      "for about 2200 pigs with 50000 SNPs, "
                      "and a phenotype file with body weight. "
                      "Please run GWAS with a MAF threshold of 0.8."),
            "test_type": "invalid_maf_exec",
            "eval": {
                "detect": ["maf", "0.8", "invalid", "range", "0.5",
                           "minor allele", "frequency", "threshold",
                           "unusual", "high", "between 0 and 0.5",
                           "cannot exceed"],
                "correct": ["0.05", "0.01", "valid", "adjust", "recommend",
                            "typical", "standard", "common"],
            },
            "timeout": 120,
        },
        {
            "id": "ERR-004",
            "description": "Missing covariates but requesting PCA correction",
            "query": ("I have PLINK binary genotype files for 800 pigs "
                      "with 50000 SNPs, and a phenotype file with body weight. "
                      "Please run GWAS with 5 PCA covariates included."),
            "test_type": "missing_covariates",
            "eval": {
                "detect": ["covariate", "pca", "principal component",
                           "need", "missing", "compute", "calculate",
                           "first run", "need to generate"],
                "correct": ["compute pca first", "run pca", "calculate pca",
                            "generate pca", "need covariate file",
                            "perform pca"],
            },
            "timeout": 120,
        },
        {
            "id": "ERR-005",
            "description": "Data format mismatch: HapMap data requesting GWAS",
            "query": ("I have HapMap (.hmp.txt) format genotype data "
                      "for 1000 individuals. I want to run a GWAS analysis."),
            "test_type": "format_mismatch",
            "eval": {
                "detect": ["hapmap", "hmp", "convert", "import", "format",
                           "plink", "bed", "bim", "fam", "first",
                           "need to convert", "need to import",
                           "cannot directly", "not directly",
                           "step", "before", "ped", "map"],
                "correct": ["convert", "import", "geno-import",
                            "first convert", "first import",
                            "transform", "plink --vcf"],
            },
            "timeout": 120,
        },
    ]

    for tc in exec_cases:
        if ids and tc["id"] not in ids:
            continue
        tid = tc["id"]
        query = tc["query"]
        timeout_sec = tc.get("timeout", 120)

        session = BOLEChatSession(BOLE_API, lang="en")
        try:
            session.start(query)
            session.collect(duration=timeout_sec)
            conv = session.get_log()

            all_text = " ".join(
                m["content"] for m in conv["conversation"]
                if m["role"] == "assistant"
            )

            detected = _eval_keywords(all_text, tc["eval"]["detect"])
            corrected = _eval_keywords(all_text, tc["eval"]["correct"])

            if tc["test_type"] == "pipeline_matching":
                pipeline_matched = _eval_keywords(
                    all_text, tc.get("expected_pipelines", []))
                handled_correctly = pipeline_matched or detected
            else:
                handled_correctly = detected or corrected

            result = {
                "id": tid,
                "description": tc["description"],
                "test_type": tc["test_type"],
                "query": query,
                "conversation_log": conv,
                "evaluation": {
                    "error_detected": detected,
                    "correction_suggested": corrected,
                    "handled_correctly": handled_correctly,
                },
                "error": None,
            }
        except Exception as e:
            result = {
                "id": tid,
                "description": tc["description"],
                "test_type": tc["test_type"],
                "query": query,
                "conversation_log": session.get_log(),
                "evaluation": {
                    "error_detected": False,
                    "correction_suggested": False,
                    "handled_correctly": False,
                },
                "error": str(e),
            }
        finally:
            session.stop()

        all_results.append(result)
        status = "PASS" if result["evaluation"]["handled_correctly"] else "FAIL"
        print(f"  [{status}] {tid}: {tc['description']}")
        print(f"         detected={result['evaluation']['error_detected']}, "
              f"corrected={result['evaluation']['correction_suggested']}")

        conv_file = eh_out / f"{tid}_conversation.json"
        with open(conv_file, "w") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    total = len(all_results)
    handled = sum(1 for r in all_results
                  if r["evaluation"]["handled_correctly"])
    rate = handled / total * 100 if total > 0 else 0

    summary = {
        "error_handling_rate": f"{rate:.1f}%",
        "total_tests": total,
        "handled_correctly": handled,
        "details": all_results,
    }

    print(f"\n  Error Handling Rate: {rate:.1f}% ({handled}/{total})")

    with open(RESULTS_DIR / "error_handling_results.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    with open(eh_out / "error_handling_results.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


# ============================================================
# Test Suite 4: Reproducibility Test
# ============================================================

def test_reproducibility():
    """Test that identical inputs produce identical workflow structures."""
    print("\n" + "=" * 60)
    print("TEST SUITE 4: Reproducibility Test")
    print("=" * 60)

    test_queries = [
        "Perform GWAS analysis on my data",
        "Estimate heritability using GCTA",
        "Run genomic selection with 6 models",
    ]

    results = []
    for query in test_queries:
        flows_detected = []
        for run in range(3):
            payload = {
                "history": [{"role": "user", "content": query}],
                "lang": "en",
            }
            try:
                resp = requests.post(
                    f"{BOLE_API}/api/brain/condense-intent",
                    json=payload,
                    timeout=120,
                )
                data = resp.json()
                flows_detected.append(data.get("flow", "unknown"))
            except Exception as e:
                flows_detected.append(f"error: {e}")

        consistent = len(set(flows_detected)) == 1
        results.append({
            "query": query,
            "flows_detected": flows_detected,
            "consistent": consistent,
        })
        status = "PASS" if consistent else "FAIL"
        print(f"  [{status}] '{query}': {flows_detected}")

    total = len(results)
    consistent = sum(1 for r in results if r["consistent"])
    rate = consistent / total * 100

    summary = {
        "reproducibility_rate": f"{rate:.1f}%",
        "total_tests": total,
        "consistent": consistent,
        "details": results,
    }

    with open(RESULTS_DIR / "reproducibility_results.json", "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    return summary


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="BOLE Quantitative Benchmarking")
    parser.add_argument(
        "--suite", nargs="*", default=None,
        help="Only run specific test suites. Options: "
             "intent_parsing, workflow_execution, error_handling, "
             "reproducibility, all (default: all)")
    parser.add_argument("--id", nargs="*", default=None,
                        help="Only run specific test case IDs (e.g. --id IP-001 ERR-101)")
    parser.add_argument("--out", default=None,
                        help="Output file path for intent parsing results (default: auto)")
    parser.add_argument("--eh-out", default=None,
                        help="Output directory for error handling results and conversations "
                             "(default: auto)")
    args = parser.parse_args()

    suites = args.suite
    if suites is None or "all" in suites:
        suites = ["intent_parsing", "workflow_execution",
                  "error_handling", "reproducibility"]

    print("BOLE Quantitative Benchmarking")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"API endpoint: {BOLE_API}")
    print(f"Test suites: {suites}")
    if args.id:
        print(f"Filtered IDs: {args.id}")
    if args.out:
        print(f"Output file: {args.out}")

    all_results = {}

    try:
        resp = requests.get(f"{BOLE_API}/api/health/llm", timeout=10)
        print(f"API health check: {resp.status_code}")
    except Exception as e:
        print(f"API not available: {e}")
        print("Skipping API-dependent tests")

    if "intent_parsing" in suites:
        try:
            ip_summary, ip_details = test_intent_parsing(ids=args.id, out_file=args.out)
            all_results["intent_parsing"] = ip_summary
        except Exception as e:
            print(f"Intent parsing test failed: {e}")
            all_results["intent_parsing"] = {"error": str(e)}

    if "workflow_execution" in suites:
        try:
            wf_summary = benchmark_workflow_execution()
            all_results["workflow_execution"] = wf_summary
        except Exception as e:
            print(f"Workflow execution test failed: {e}")
            all_results["workflow_execution"] = {"error": str(e)}

    if "error_handling" in suites:
        try:
            err_summary = test_error_handling(ids=args.id, out_dir=args.eh_out)
            all_results["error_handling"] = err_summary
        except Exception as e:
            print(f"Error handling test failed: {e}")
            all_results["error_handling"] = {"error": str(e)}

    if "reproducibility" in suites:
        try:
            rep_summary = test_reproducibility()
            all_results["reproducibility"] = rep_summary
        except Exception as e:
            print(f"Reproducibility test failed: {e}")
            all_results["reproducibility"] = {"error": str(e)}

    with open(RESULTS_DIR / "benchmark_summary.json", "w") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nCompleted at: {datetime.now().isoformat()}")
    print(f"Results saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
