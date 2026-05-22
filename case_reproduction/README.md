# BOLE Reproducibility Analysis — GWAS Result Reproduction on a Large-Scale Public Dataset

This directory contains all scripts and data for reproducing the GWAS findings of a published paper using the BOLE pipeline. All analyses were performed by actually invoking BOLE's built-in scripts and are not artificially fabricated.

## Reproduced Paper

**Accelerated Deciphering of the Genetic Architecture of Agricultural Economic Traits in Pigs Using the Low Coverage Whole-genome Sequencing Strategy**

- Journal: *GigaScience* (2021)
- DOI: 10.1093/gigascience/giab048
- Public data: 2,797 individuals, 258,662 SNPs, 7 economic traits
- Data download: https://gigadb.org/dataset/100894
- Data path: `giab048/`

## Directory Structure

```
case_reproduction/
├── README.md                                          # This document (English)
├── README-zh.md                                       # This document (Chinese)
├── script/
│   ├── genotype_qc.sh                                 # BOLE built-in: genotype QC
│   ├── prepare_phenotypes.py                          # Phenotype file preparation
│   ├── gcta_gwas_pipeline.sh                          # BOLE built-in: GCTA GWAS pipeline
│   ├── gcta_gwas_run.R                                # BOLE built-in: per-trait MLMA
│   └── generate_figures.py                            # Visualization (scatter plots + mirrored Manhattan)
└── giab048/                                           # Public dataset (download from GigaDB: https://gigadb.org/dataset/100894)
    ├── {trait}.phe.bed/bim/fam                        # PLINK binary genotypes with phenotypes (7 traits)
    ├── {trait}.log                                    # PLINK log files
    ├── {trait}.nosex                                  # PLINK excluded individuals
    ├── cov/
    │   └── {trait}.cov                                # Covariate files per trait (year, month, farm, etc.)
    └── pvalue/
        └── {trait}.pvalue                             # Published P-value files from the paper
```

---

## Dataset Overview

| Property | Value |
|----------|-------|
| Source paper | GigaScience, 2021, giab048 |
| Species | Pig (*Sus scrofa*) |
| Number of individuals | 2,797 |
| Number of SNPs | 258,662 |
| Sequencing strategy | Low-coverage whole-genome sequencing (WGS) |
| Number of traits | 7 |

**7 Economic Traits**:

| Abbreviation | Full Name | Individuals |
|-------------|-----------|-------------|
| TTN | Total Teat Number | 2,797 |
| LTN | Left Teat Number | 2,797 |
| RTN | Right Teat Number | 2,797 |
| BF | Backfat Thickness | 2,797 |
| LMD | Loin Muscle Depth | 2,797 |
| LMP | Loin Muscle Percentage | 2,797 |
| TPD | Time Spent Eating Per Day | 2,797 |

---

## Pipeline Overview

```
giab048/ (raw data)
        │
        ▼
┌──────────────────────────────────────────────────────────────────────┐
│ Step 1: genotype_qc.sh          BOLE built-in script                 │
│   PLINK genotype QC: MAF ≥ 0.01, SNP missing < 0.05,                 │
│   individual missing < 0.1, HWE P > 1e-6                             │
│                                                                      │
│ Step 2: prepare_phenotypes.py                                        │
│   Extract phenotype values from 7 trait .fam files,                  │
│   merge into a unified phenotype file                                │
│                                                                      │
│ Step 3: gcta_gwas_pipeline.sh   BOLE built-in script                 │
│   ① GRM calculation (GCTA --make-grm)                                │
│   ② Per-trait MLMA (GCTA --mlma) with --covar/--qcovar               │
│     └── gcta_gwas_run.R         BOLE built-in script                 │
│                                                                      │
│ Step 4: generate_figures.py                                          │
│   Visualization: correlation scatter plots + mirrored Manhattan      │
└──────────────────────────────────────────────────────────────────────┘
        │
        ▼
correlation_plots/  +  mirrored_manhattan/
```

---

## Script Descriptions

### Step 1: `genotype_qc.sh` (BOLE built-in)

**Source**: `backend/scripts/flows/genotype_qc.sh`

Performs PLINK genotype quality control:

```bash
genotype_qc.sh \
  --genotype_prefix giab048/bf \
  --output_prefix giab048_qc \
  --outdir /workspace/tmp/giab048_case_study \
  --maf 0.01 --geno_missing 0.05 --individual_missing 0.1 --hwe_pvalue 1e-6
```

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--genotype_prefix` | PLINK binary file prefix | required |
| `--output_prefix` | Output prefix | basename of input |
| `--outdir` | Output directory | `.` |
| `--maf` | Minor allele frequency threshold | 0.05 |
| `--geno_missing` | SNP missing rate threshold | 0.05 |
| `--individual_missing` | Individual missing rate threshold | 0.05 |
| `--hwe_pvalue` | HWE P-value threshold | 1e-6 |

**Output**: `{output_prefix}_qc.bed/bim/fam`

### Step 2: `prepare_phenotypes.py`

**Source**: `evidence/case_reproduction/script/prepare_phenotypes.py`

Extracts phenotype values from PLINK `.fam` files and merges into a single phenotype file.

```bash
python3 prepare_phenotypes.py
```

This script reads all 7 trait `.fam` files from `giab048/` and produces:

- `giab048_phenotypes.txt` — with header, FID+IID format (for GWAS)
- `giab048_phenotypes_h2.txt` — no header, IID only format (for heritability)

**Output**: Phenotype files in GCTA format

### Step 3: `gcta_gwas_pipeline.sh` + `gcta_gwas_run.R` (BOLE built-in)

**Source**: `backend/scripts/flows/gcta_gwas_pipeline.sh` and `gcta_gwas_run.R`

Two-step GCTA-MLMA GWAS pipeline:

1. **GRM calculation** (`--make-grm`)
2. **Per-trait MLMA** (`--mlma`) with optional covariates (`--covar` / `--qcovar`)

```bash
# With discrete covariates (BF/LMD/LMP/TPD etc.)
gcta_gwas_pipeline.sh \
  --genotype_prefix giab048_qc_qc \
  --pheno giab048_phenotypes.txt \
  --output giab048_gwas \
  --covar giab048/cov/bf.cov \
  --threads 4
```

| Parameter | Description | Required |
|-----------|-------------|----------|
| `--genotype_prefix` | QC'ed PLINK binary file prefix | Yes |
| `--pheno` | Phenotype file (FID, IID, traits) | Yes |
| `--output` | Output prefix | Yes |
| `--threads` | Thread count | No (default 4) |
| `--covar` | Discrete covariate file for GCTA `--covar` | No |
| `--qcovar` | Quantitative covariate file for GCTA `--qcovar` | No |

**Output**: `{output}_{trait}.mlma` — GCTA-MLMA result for each trait

---

## Data Flow

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

## Dependencies

- **PLINK** (1.9+): genotype QC
- **GCTA** (1.94+): GRM and MLMA
- **R** (4.0+): with `data.table`, `qqman`, `ggplot2` packages
- **Python** (3.8+): with `pandas`, `numpy`, `scipy`, `matplotlib`, `openpyxl`

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ALBA_RSCRIPT_BIN` | Path to Rscript binary | `/workspace/miniconda3/envs/R/bin/Rscript` |
| `ALBA_BIN_DIR` | Path to GCTA/PLINK binaries | `/workspace/app/bin` |

---

## Data Provenance

All GWAS results were generated by BOLE's built-in scripts (`genotype_qc.sh`, `gcta_gwas_pipeline.sh`, `gcta_gwas_run.R`) through actual invocation of PLINK and GCTA. Published P-values were sourced from the giab048 paper's public data. Visualizations were generated by the `generate_figures.py` script. All intermediate files and final results are traceable and verifiable.
