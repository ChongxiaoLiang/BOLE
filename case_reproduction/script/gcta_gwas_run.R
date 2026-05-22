#!/usr/bin/env Rscript
# GCTA MLMA GWAS runner and plotter
# Args: <phenotype_file> <grm_prefix> <genotype_prefix> <output_prefix>

suppressPackageStartupMessages({
  library(data.table)
  library(qqman)
  library(ggplot2)
})

args <- commandArgs(trailingOnly = TRUE)

`%||%` <- function(a, b) {
  if (is.null(a) || length(a) == 0L) b else a
}

parse_args <- function(argv) {
  opts <- list()
  pos <- character()
  i <- 1
  while (i <= length(argv)) {
    a <- argv[i]
    if (startsWith(a, "--")) {
      if (grepl("=", a, fixed = TRUE)) {
        parts <- strsplit(sub("^--", "", a), "=", fixed = TRUE)[[1]]
        key <- parts[1]
        val <- paste(parts[-1], collapse = "=")
        opts[[key]] <- val
        i <- i + 1
      } else {
        key <- sub("^--", "", a)
        if (i == length(argv) || startsWith(argv[i + 1], "--")) {
          opts[[key]] <- TRUE
          i <- i + 1
        } else {
          opts[[key]] <- argv[i + 1]
          i <- i + 2
        }
      }
    } else {
      pos <- c(pos, a)
      i <- i + 1
    }
  }
  list(opts = opts, pos = pos)
}

usage <- function() {
  cat("Usage: Rscript gcta_gwas_run.R --phenotype_file <file> --grm_prefix <prefix> --genotype_prefix <prefix> --output_prefix <prefix> [--outdir <dir>] [--covar <file>] [--qcovar <file>]\n")
}

parsed <- parse_args(args)
opts <- parsed$opts

pheno_file <- as.character(opts[["phenotype_file"]] %||% "")
grm_prefix <- as.character(opts[["grm_prefix"]] %||% "")
genotype_prefix <- as.character(opts[["genotype_prefix"]] %||% "")
output_prefix <- as.character(opts[["output_prefix"]] %||% "")
outdir <- as.character(opts[["outdir"]] %||% ".")
covar_file <- as.character(opts[["covar"]] %||% "")
qcovar_file <- as.character(opts[["qcovar"]] %||% "")
if (is.null(outdir) || nchar(outdir) == 0) outdir <- "."

if (pheno_file == "" || grm_prefix == "" || genotype_prefix == "" || output_prefix == "") {
  usage()
  stop("Missing required args: phenotype_file, grm_prefix, genotype_prefix, output_prefix")
}

if (!dir.exists(outdir)) dir.create(outdir, recursive = TRUE, showWarnings = FALSE)
if (!grepl("^/|^\\./|^\\.\\./", output_prefix)) {
  output_prefix <- file.path(outdir, output_prefix)
}

if (!file.exists(pheno_file)) {
  stop(sprintf("Phenotype file does not exist: %s", pheno_file))
}

# -----------------------------
# 1. Load phenotype
# -----------------------------
pheno <- fread(pheno_file)

# [修正] 自动处理没有表头的 .fam 或 .phen 格式
if (!all(c("FID", "IID") %in% names(pheno))) {
  cat("Headers 'FID'/'IID' not found. Assuming columns 1 and 2 are IDs.\n")
  setnames(pheno, 1:2, c("FID", "IID"))
}

# 提取性状列（排除 ID 列）
trait_cols <- setdiff(names(pheno), c("FID", "IID"))

# -----------------------------
# 2. GWAS function per trait
# -----------------------------
run_gwas <- function(trait) {
  temp_pheno <- paste0(output_prefix, "_", trait, "_temp.phen")
  
  # [修正] 使用更健壮的列选择方式，移除 with=FALSE 的冲突
  # 提取 FID, IID 和当前 trait 列
  temp_dt <- pheno[, c("FID", "IID", trait), with=FALSE]
  fwrite(temp_dt, temp_pheno, col.names = FALSE, sep = "\t")
  
  out_prefix <- paste0(output_prefix, "_", trait)
  
  gcta_cmd <- paste("gcta --bfile", genotype_prefix,
                    "--grm", grm_prefix,
                    "--pheno", temp_pheno)
  
  if (nchar(covar_file) > 0 && file.exists(covar_file)) {
    gcta_cmd <- paste(gcta_cmd, "--covar", covar_file)
  }
  
  if (nchar(qcovar_file) > 0 && file.exists(qcovar_file)) {
    gcta_cmd <- paste(gcta_cmd, "--qcovar", qcovar_file)
  }
  
  gcta_cmd <- paste(gcta_cmd, "--mlma --out", out_prefix)
  
  system(gcta_cmd)
  
  res_file <- paste0(out_prefix, ".mlma")
  if(file.exists(res_file)) {
    res <- fread(res_file)
    return(list(trait=trait, result=res, out_prefix=out_prefix))
  } else {
    warning(paste("No result for trait", trait))
    return(NULL)
  }
}

# -----------------------------
# 3. Loop through traits
# -----------------------------
for(trait in trait_cols) {
  cat("Running GWAS for trait:", trait, "\n")
  gwas <- run_gwas(trait)
  if(!is.null(gwas)) {
    res <- gwas$result
    out_prefix <- gwas$out_prefix
    
    # Manhattan plot
    png(paste0(out_prefix, "_manhattan.png"), width=1200, height=600)
    manhattan(res, chr="Chr", bp="bp", p="p", snp="SNP",
              main=paste("GWAS Manhattan -", trait))
    dev.off()
    
    # Q-Q plot
    png(paste0(out_prefix, "_qq.png"), width=600, height=600)
    qq(res$p, main=paste("Q-Q plot -", trait))
    dev.off()
    
    # Significant SNPs
    sig <- res[p < 5e-8]
    if(nrow(sig) > 0) fwrite(sig, paste0(out_prefix, "_significant.csv"))
    cat("Trait", trait, "found", nrow(sig), "significant SNPs\n")
  }
}

cat("=== GCTA GWAS complete ===\n")
