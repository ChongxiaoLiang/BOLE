#!/usr/bin/env bash
# GCTA GWAS pipeline
# Input: QC'ed genotype (bed/bim/fam), phenotype file
# Output: GRM, per-trait GWAS, Manhattan/Q-Q plots, significant SNPs

set -euo pipefail

__alba_bin="${ALBA_BIN_DIR:-${ALBA_APP_BIN:-/workspace/app/bin}}"
if [[ -d "$__alba_bin" ]]; then
    export PATH="$__alba_bin:$PATH"
fi

# -----------------------------
# Parameters
# -----------------------------
GENO="${GENO:-}"
PHENO="${PHENO:-}"
OUTPUT="${OUTPUT:-}"
THREADS="${THREADS:-}"
COVAR="${COVAR:-}"
QCOVAR="${QCOVAR:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --genotype_prefix|--geno|--bfile)
            GENO="${2:-}"
            shift 2
            ;;
        --phenotype_file|--pheno)
            PHENO="${2:-}"
            shift 2
            ;;
        --output_prefix|--output|--outprefix|--out_prefix)
            OUTPUT="${2:-}"
            shift 2
            ;;
        --threads)
            THREADS="${2:-}"
            shift 2
            ;;
        --covar)
            COVAR="${2:-}"
            shift 2
            ;;
        --qcovar)
            QCOVAR="${2:-}"
            shift 2
            ;;
        *)
            if [[ "$1" == --* ]]; then
                if [[ $# -ge 2 && "${2:-}" != --* ]]; then
                    shift 2
                else
                    shift 1
                fi
            else
                shift 1
            fi
            ;;
    esac
done

if [[ -z "${GENO}" || -z "${PHENO}" ]]; then
    echo "Error: missing required arguments: genotype_prefix and phenotype_file" >&2
    exit 2
fi

THREADS=${THREADS:-4}
OUTPUT=${OUTPUT:-"gcta_gwas"}

if [[ -n "${ALBA_INDIR:-}" ]]; then
    if [[ -n "${GENO:-}" && "${GENO}" != /* && "${GENO}" != ./* && "${GENO}" != ../* ]]; then
        GENO="${ALBA_INDIR%/}/${GENO}"
    fi
    if [[ -n "${PHENO:-}" && "${PHENO}" != /* && "${PHENO}" != ./* && "${PHENO}" != ../* ]]; then
        PHENO="${ALBA_INDIR%/}/${PHENO}"
    fi
    if [[ -n "${COVAR:-}" && "${COVAR}" != /* && "${COVAR}" != ./* && "${COVAR}" != ../* ]]; then
        COVAR="${ALBA_INDIR%/}/${COVAR}"
    fi
    if [[ -n "${QCOVAR:-}" && "${QCOVAR}" != /* && "${QCOVAR}" != ./* && "${QCOVAR}" != ../* ]]; then
        QCOVAR="${ALBA_INDIR%/}/${QCOVAR}"
    fi
fi

if [[ -n "${OUTDIR:-${ALBA_OUTDIR:-}}" && "${OUTPUT}" != /* && "${OUTPUT}" != ./* && "${OUTPUT}" != ../* ]]; then
    OUTPUT="${OUTDIR:-${ALBA_OUTDIR}}/${OUTPUT}"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# -----------------------------
# 1. Calculate GRM
# -----------------------------
echo "=== Step 1: Calculating GRM ==="
gcta --bfile "${GENO}" \
       --autosome \
       --maf 0.01 \
       --make-grm \
       --out "${OUTPUT}_grm" \
       --thread-num "${THREADS}"

# -----------------------------
# 2. Run per-trait MLMA GWAS
# -----------------------------
echo "=== Step 2: Running per-trait GWAS ==="

R_CMD_ARGS=(
  --phenotype_file "${PHENO}"
  --grm_prefix "${OUTPUT}_grm"
  --genotype_prefix "${GENO}"
  --output_prefix "${OUTPUT}"
  --outdir "${OUTDIR:-${ALBA_OUTDIR:-.}}"
)

if [[ -n "${COVAR:-}" ]]; then
    R_CMD_ARGS+=(--covar "${COVAR}")
fi

if [[ -n "${QCOVAR:-}" ]]; then
    R_CMD_ARGS+=(--qcovar "${QCOVAR}")
fi

"${ALBA_RSCRIPT_BIN:-Rscript}" "${SCRIPT_DIR}/gcta_gwas_run.R" "${R_CMD_ARGS[@]}"

echo "=== GCTA GWAS pipeline finished ==="
