# BOLE 复现分析 — 大规模公开数据集 GWAS 结果复现

本目录包含使用 BOLE pipeline 对已发表论文 GWAS 结果进行完整复现的全部脚本和数据。所有分析均通过实际调用 BOLE 内置脚本完成，非人工拟造。

## 复现论文

**Accelerated Deciphering of the Genetic Architecture of Agricultural Economic Traits in Pigs Using the Low Coverage Whole-genome Sequencing Strategy**

- 期刊：*GigaScience*（2021）
- DOI：10.1093/gigascience/giab048
- 公开数据：2,797 个体，258,662 SNPs，7 个经济性状
- 数据下载：https://gigadb.org/dataset/100894
- 数据路径：`giab048/`

## 目录结构

```
case_reproduction/
├── README.md                                          # 本文档（英文版）
├── README-zh.md                                       # 本文档（中文版）
├── script/
│   ├── genotype_qc.sh                                 # BOLE 内置：基因型质控
│   ├── prepare_phenotypes.py                          # 表型文件准备
│   ├── gcta_gwas_pipeline.sh                          # BOLE 内置：GCTA GWAS 流程
│   ├── gcta_gwas_run.R                                # BOLE 内置：逐性状 MLMA
│   └── generate_figures.py                            # 复现可视化（散点图 + 镜像 Manhattan）
└── giab048/                                           # 公开数据集（需从 GigaDB 下载：https://gigadb.org/dataset/100894）
    ├── {trait}.phe.bed/bim/fam                        # 7 个性状的 PLINK 二进制基因型（含表型）
    ├── {trait}.log                                    # PLINK 日志文件
    ├── {trait}.nosex                                  # PLINK 排除个体列表
    ├── cov/
    │   └── {trait}.cov                                # 各性状协变量文件（年份、月份、场等）
    └── pvalue/
        └── {trait}.pvalue                             # 论文发表的 P 值文件
```

---

## 数据集概览

| 属性 | 值 |
|------|-----|
| 来源论文 | GigaScience, 2021, giab048 |
| 物种 | 猪（*Sus scrofa*） |
| 个体数 | 2,797 |
| SNP 数 | 258,662 |
| 测序策略 | 低覆盖度全基因组测序（Low-coverage WGS） |
| 性状数 | 7 |

**7 个经济性状**：

| 缩写 | 全称 | 中文 | 个体数 |
|------|------|------|--------|
| TTN | Total Teat Number | 总乳头数 | 2,797 |
| LTN | Left Teat Number | 左侧乳头数 | 2,797 |
| RTN | Right Teat Number | 右侧乳头数 | 2,797 |
| BF | Backfat Thickness | 背膘厚 | 2,797 |
| LMD | Loin Muscle Depth | 腰肌深度 | 2,797 |
| LMP | Loin Muscle Percentage | 腰肌面积 | 2,797 |
| TPD | Time Spent Eating Per Day | 日采食时间 | 2,797 |

---

## Pipeline 总览

```
giab048/ (原始数据)
        │
        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 1: genotype_qc.sh          BOLE 内置脚本                         │
│   PLINK 基因型质控：MAF ≥ 0.01, SNP缺失率 < 0.05,                      │
│   个体缺失率 < 0.1, HWE P > 1e-6                                      │
│                                                                      │
│ Step 2: prepare_phenotypes.py                                        │
│   从 7 个性状的 .fam 文件中提取表型值，合并为统一表型文件                 │
│                                                                      │
│ Step 3: gcta_gwas_pipeline.sh   BOLE 内置脚本                         │
│   ① GRM 计算（GCTA --make-grm）                                       │
│   ② 逐性状 MLMA（GCTA --mlma），支持 --covar/--qcovar                  │
│     └── gcta_gwas_run.R         BOLE 内置脚本                         │
│                                                                      │
│ Step 4: generate_figures.py                                          │
│   复现可视化：相关性散点图 + 镜像 Manhattan                             │
└──────────────────────────────────────────────────────────────────────┘
        │
        ▼
correlation_plots/  +  mirrored_manhattan/ 
```

---

## 脚本说明

### Step 1：`genotype_qc.sh`（BOLE 内置脚本）

**来源**：`backend/scripts/flows/genotype_qc.sh`

执行 PLINK 基因型质控：

```bash
genotype_qc.sh \
  --genotype_prefix giab048/bf \
  --output_prefix giab048_qc \
  --outdir /workspace/tmp/giab048_case_study \
  --maf 0.01 --geno_missing 0.05 --individual_missing 0.1 --hwe_pvalue 1e-6
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--genotype_prefix` | PLINK 二进制文件前缀 | 必需 |
| `--output_prefix` | 输出前缀 | 输入文件 basename |
| `--outdir` | 输出目录 | `.` |
| `--maf` | 最小等位基因频率阈值 | 0.05 |
| `--geno_missing` | SNP 缺失率阈值 | 0.05 |
| `--individual_missing` | 个体缺失率阈值 | 0.05 |
| `--hwe_pvalue` | HWE P 值阈值 | 1e-6 |

**输出**：`{output_prefix}_qc.bed/bim/fam`

### Step 2：`prepare_phenotypes.py`

**来源**：`evidence/case_reproduction/script/prepare_phenotypes.py`

从 PLINK `.fam` 文件提取表型值，合并为单一表型文件。

```bash
python3 prepare_phenotypes.py
```

该脚本读取 `giab048/` 下 7 个性状的 `.fam` 文件，生成：

- `giab048_phenotypes.txt` — 带表头，FID+IID 格式（用于 GWAS）
- `giab048_phenotypes_h2.txt` — 无表头，仅 IID 格式（用于遗传力估计）

**输出**：GCTA 格式的表型文件

### Step 3：`gcta_gwas_pipeline.sh` + `gcta_gwas_run.R`（BOLE 内置脚本）

**来源**：`backend/scripts/flows/gcta_gwas_pipeline.sh` 和 `gcta_gwas_run.R`

两步 GCTA-MLMA GWAS 流程：

1. **GRM 计算**（`--make-grm`）
2. **逐性状 MLMA**（`--mlma`），支持可选协变量（`--covar` / `--qcovar`）

```bash
# 带离散协变量（BF/LMD/LMP/TPD 等）
gcta_gwas_pipeline.sh \
  --genotype_prefix giab048_qc_qc \
  --pheno giab048_phenotypes.txt \
  --output giab048_gwas \
  --covar giab048/cov/bf.cov \
  --threads 4
```

| 参数 | 说明 | 是否必需 |
|------|------|---------|
| `--genotype_prefix` | QC 后的 PLINK 二进制文件前缀 | 是 |
| `--pheno` | 表型文件（FID, IID, 性状列） | 是 |
| `--output` | 输出前缀 | 是 |
| `--threads` | 线程数 | 否（默认 4） |
| `--covar` | 离散协变量文件 | 否 |
| `--qcovar` | 连续协变量文件 | 否 |

**输出**：`{output}_{trait}.mlma` — 每个性状的 GCTA-MLMA 结果

---

## 数据流

```
giab048/
├── {trait}.phe.bed/bim/fam       ──genotype_qc.sh──►  giab048_qc_qc.bed/bim/fam
├── cov/
│   └── {trait}.cov               ───────────────────────────────────────┐
└── pvalue/                                                              │
    └── {trait}.pvalue             ──────────────────────────────┐       │
                                                                 │       │
giab048_qc_qc.bed/bim/fam                                        │       │
giab048_phenotypes.txt  ──gcta_gwas_pipeline.sh──►  .mlma files ─┤       │
                                        ▲                        │       │
                                   --covar bf.cov ───────────────┘       │
                                        │                                │
                                        ▼                                │
                              generate_figures.py ◄──────────────────────┘
                                        │
                                        ▼
                    correlation_plots/  +  mirrored_manhattan/
```

---

## 依赖

- **PLINK**（1.9+）：基因型质控
- **GCTA**（1.94+）：GRM 和 MLMA
- **R**（4.0+）：需安装 `data.table`、`qqman`、`ggplot2` 包
- **Python**（3.8+）：需安装 `pandas`、`numpy`、`scipy`、`matplotlib`、`openpyxl`

## 环境变量

| 变量 | 说明 | 示例 |
|------|------|------|
| `ALBA_RSCRIPT_BIN` | Rscript 路径 | `/workspace/miniconda3/envs/R/bin/Rscript` |
| `ALBA_BIN_DIR` | GCTA/PLINK 二进制文件路径 | `/workspace/app/bin` |

---

## 数据溯源

所有 GWAS 结果均由 BOLE 内置脚本（`genotype_qc.sh`、`gcta_gwas_pipeline.sh`、`gcta_gwas_run.R`）通过实际调用 PLINK 和 GCTA 生成。论文 P 值来源于 giab048 论文公开数据。可视化由 `generate_figures.py` 脚本生成。所有中间文件和最终结果均可追溯和验证。
