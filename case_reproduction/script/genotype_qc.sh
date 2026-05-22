#!/usr/bin/env bash
set -euo pipefail

__alba_bin="${ALBA_BIN_DIR:-${ALBA_APP_BIN:-/workspace/app/bin}}"
if [[ -d "$__alba_bin" ]]; then
    export PATH="$__alba_bin:$PATH"
fi

usage() {
    cat <<'EOF'
Usage: genotype_qc.sh --genotype_prefix <plink_prefix> [options]

Options:
  --output_prefix <prefix>       Output prefix name (default: basename of genotype_prefix)
  --outdir <dir>                 Output directory (default: OUTDIR or ALBA_OUTDIR)
  --maf <float>                  Default 0.05
  --geno_missing <float>         Default 0.05
  --individual_missing <float>   Default 0.05
  --hwe_pvalue <float>           Default 1e-6
  --help                         Show this help
EOF
}

GENO_PREFIX="${GENO:-${GENOTYPE_PREFIX:-}}"
OUTDIR_PATH="${OUTDIR:-}"
OUTPREFIX="${OUTPREFIX:-${OUTPUT_PREFIX:-}}"
MAF_VAL="${MAF:-}"
GENO_MISSING_VAL="${GENO_MISSING:-}"
INDIVIDUAL_MISSING_VAL="${INDIVIDUAL_MISSING:-}"
HWE_PVALUE_VAL="${HWE_PVALUE:-}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --genotype_prefix|--geno|--bfile)
            GENO_PREFIX="${2:-}"
            shift 2
            ;;
        --output_prefix|--outprefix|--out)
            OUTPREFIX="${2:-}"
            shift 2
            ;;
        --outdir|--output_dir)
            OUTDIR_PATH="${2:-}"
            shift 2
            ;;
        --maf)
            MAF_VAL="${2:-}"
            shift 2
            ;;
        --geno_missing)
            GENO_MISSING_VAL="${2:-}"
            shift 2
            ;;
        --individual_missing|--mind|--sample_missing)
            INDIVIDUAL_MISSING_VAL="${2:-}"
            shift 2
            ;;
        --hwe_pvalue|--hwe)
            HWE_PVALUE_VAL="${2:-}"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            shift 1
            ;;
    esac
done

if [[ -z "${GENO_PREFIX:-}" ]]; then
    usage
    echo "Error: missing genotype_prefix" >&2
    exit 2
fi

if [[ -n "${ALBA_INDIR:-}" && "${GENO_PREFIX}" != /* && "${GENO_PREFIX}" != ./* && "${GENO_PREFIX}" != ../* ]]; then
    GENO_PREFIX="${ALBA_INDIR%/}/${GENO_PREFIX}"
fi

OUTDIR_PATH="${OUTDIR_PATH:-${ALBA_OUTDIR:-}}"
if [[ -z "${OUTDIR_PATH:-}" ]]; then
    OUTDIR_PATH="."
fi
mkdir -p "${OUTDIR_PATH}"

MAF_VAL="${MAF_VAL:-0.05}"
GENO_MISSING_VAL="${GENO_MISSING_VAL:-0.05}"
INDIVIDUAL_MISSING_VAL="${INDIVIDUAL_MISSING_VAL:-0.05}"
HWE_PVALUE_VAL="${HWE_PVALUE_VAL:-1e-6}"

OUTPREFIX="${OUTPREFIX:-$(basename "${GENO_PREFIX}")}"
OUT_PREFIX="${OUTDIR_PATH%/}/${OUTPREFIX}_qc"

plink --bfile "${GENO_PREFIX}" \
      --maf "${MAF_VAL}" \
      --geno "${GENO_MISSING_VAL}" \
      --mind "${INDIVIDUAL_MISSING_VAL}" \
      --hwe "${HWE_PVALUE_VAL}" \
      --make-bed \
      --out "${OUT_PREFIX}"
