#!/usr/bin/env python3
"""
Prepare phenotype files from PLINK .fam files.
Extract phenotype values (column 6) from each trait's .fam file
and merge into two phenotype files:
  1. giab048_phenotypes.txt - with header, FID+IID format (for GWAS)
  2. giab048_phenotypes_h2.txt - no header, IID only format (for heritability)
"""

WORK_DIR = "/workspace/tmp/giab048_case_study"
DATA_DIR = "/workspace/giab048"
TRAITS = ["bf", "lmd", "lmp", "ltn", "rtn", "tpd", "ttn"]

import os
os.makedirs(WORK_DIR, exist_ok=True)

# Read all FAM files and extract phenotypes
sample_order = None
phenotypes = {}

for trait in TRAITS:
    fam_file = os.path.join(DATA_DIR, f"{trait}.fam")
    trait_phenos = {}
    with open(fam_file) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 6:
                fid, iid, pheno = parts[0], parts[1], parts[5]
                trait_phenos[iid] = (fid, iid, pheno)

    if sample_order is None:
        sample_order = list(trait_phenos.keys())
    phenotypes[trait] = trait_phenos

# Write giab048_phenotypes.txt (with header, FID+IID)
with open(os.path.join(WORK_DIR, "giab048_phenotypes.txt"), "w") as out:
    out.write("FID\tIID\t" + "\t".join(TRAITS) + "\n")
    for iid in sample_order:
        fid = phenotypes[TRAITS[0]][iid][0]
        vals = []
        for trait in TRAITS:
            vals.append(phenotypes[trait].get(iid, ("", "", "NA"))[2])
        out.write(fid + "\t" + iid + "\t" + "\t".join(vals) + "\n")

# Write giab048_phenotypes_h2.txt (no header, IID only)
with open(os.path.join(WORK_DIR, "giab048_phenotypes_h2.txt"), "w") as out:
    for iid in sample_order:
        vals = []
        for trait in TRAITS:
            vals.append(phenotypes[trait].get(iid, ("", "", "NA"))[2])
        out.write(iid + "\t" + "\t".join(vals) + "\n")

print(f"Phenotype files created in {WORK_DIR}")
print(f"  Samples: {len(sample_order)}")
print(f"  Traits: {TRAITS}")
