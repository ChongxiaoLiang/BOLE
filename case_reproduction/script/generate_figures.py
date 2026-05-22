#!/usr/bin/env python3
"""
Part 2 Visualization: Correlation Scatter Plots + Mirrored Manhattan
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from scipy import stats
import re
import os
import openpyxl

BASE_DIR = "/www/wwwroot/BOLE/evidence/case_reproduce"
BOLE_DIR = "/www/wwwroot/BOLE/evidence/case_study/results/gwas_results"
PAPER_PV_DIR = "/workspace/giab048/pvalue"
PAPER_XLSX = "/www/wwwroot/BOLE/evidence/case_study/paper/Supplementary Table S7.xlsx"
OUT_DIR = os.path.join(BASE_DIR, "results/reproducibility_analysis")

TRAIT_FILES = {
    "TTN": "giab048_gwas_ttn.mlma",
    "LTN": "giab048_gwas_ltn.mlma",
    "RTN": "giab048_gwas_rtn.mlma",
    "BF": "giab048_gwas_bf_cov.mlma",
    "LMD": "giab048_gwas_lmd_cov.mlma",
    "LMP": "giab048_gwas_lmp_cov_only.mlma",
    "TPD": "giab048_gwas_tpd_cov.mlma",
}

TRAIT_LABELS = {
    "TTN": "Total Teat Number",
    "LTN": "Left Teat Number",
    "RTN": "Right Teat Number",
    "BF": "Backfat Thickness",
    "LMD": "Loin Muscle Depth",
    "LMP": "Loin Muscle Area",
    "TPD": "Time Spent Eating Perday",
}

SIG_THRESHOLD = 5e-8
SUGGESTIVE_THRESHOLD = 1e-5

CHR_COLORS = ['#2166AC', '#4393C3']
CHR_COLORS_ALT = ['#2166AC', '#B2182B']

plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 10,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'xtick.major.size': 4,
    'ytick.major.size': 4,
    'figure.dpi': 300,
    'savefig.dpi': 300,
})


def load_bole_results(trait):
    fname = TRAIT_FILES[trait]
    fpath = os.path.join(BOLE_DIR, fname)
    df = pd.read_csv(fpath, sep=r'\s+')
    df['neg_log10_p'] = -np.log10(df['p'].replace(0, 1e-300))
    return df


def load_paper_pvalues(trait):
    trait_lower = trait.lower()
    fpath = os.path.join(PAPER_PV_DIR, f"{trait_lower}.pvalue")
    df = pd.read_csv(fpath, sep=r'\s+', header=None, names=['idx', 'chr', 'bp', 'pvalue'])
    df['neg_log10_p'] = -np.log10(df['pvalue'].replace(0, 1e-300))
    df['snp_id'] = df['chr'].astype(str) + ':' + df['bp'].astype(str)
    return df


def extract_paper_qtls():
    wb = openpyxl.load_workbook(PAPER_XLSX)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    qtl_records = []
    current_trait = None
    for i, row in enumerate(rows):
        if i <= 1:
            continue
        if row[0] is not None:
            trait_val = str(row[0]).strip()
            if trait_val.startswith('Reference') or trait_val.startswith('['):
                continue
            current_trait = trait_val
        if current_trait and row[1] is not None:
            qtl_str = str(row[1]).strip()
            lead_snp_str = str(row[2]).strip() if row[2] else None
            for m in re.finditer(r'(\d+):([\d,]+)-([\d,]+)', qtl_str):
                chrom = int(m.group(1))
                start = int(m.group(2).replace(',', ''))
                end = int(m.group(3).replace(',', ''))
                lead_chr, lead_bp = None, None
                if lead_snp_str:
                    lm = re.match(r'(\d+):([\d,]+)', lead_snp_str.strip())
                    if lm:
                        lead_chr = int(lm.group(1))
                        lead_bp = int(lm.group(2).replace(',', ''))
                qtl_records.append({
                    "Trait": current_trait,
                    "QTL_chr": chrom,
                    "QTL_start": start,
                    "QTL_end": end,
                    "Lead_SNP_chr": lead_chr,
                    "Lead_SNP_bp": lead_bp,
                })
    return pd.DataFrame(qtl_records)


def compute_chr_offsets(bole_df):
    chr_max = bole_df.groupby('Chr')['bp'].max()
    chr_list = sorted(bole_df['Chr'].unique())
    offsets = {}
    cumulative = 0
    for c in chr_list:
        offsets[c] = cumulative
        cumulative += chr_max[c] + 5e6
    return offsets, chr_list


def plot_correlation_scatter(trait, ax):
    bole = load_bole_results(trait)
    paper = load_paper_pvalues(trait)
    bole['snp_id'] = bole['Chr'].astype(str) + ':' + bole['bp'].astype(str)
    paper['snp_id'] = paper['chr'].astype(str) + ':' + paper['bp'].astype(str)

    merged = pd.merge(
        paper[['snp_id', 'pvalue', 'neg_log10_p']].rename(
            columns={'pvalue': 'Paper_P', 'neg_log10_p': 'Paper_neglog10P'}
        ),
        bole[['snp_id', 'p', 'neg_log10_p']].rename(
            columns={'p': 'BOLE_P', 'neg_log10_p': 'BOLE_neglog10P'}
        ),
        on='snp_id', how='inner'
    )

    paper_top100 = paper.nsmallest(100, 'pvalue')
    merged_top100 = merged[merged['snp_id'].isin(paper_top100['snp_id'])]

    if len(merged_top100) < 5:
        ax.text(0.5, 0.5, 'Insufficient data', ha='center', va='center', transform=ax.transAxes)
        return

    x = merged_top100['Paper_neglog10P']
    y = merged_top100['BOLE_neglog10P']

    ax.scatter(x, y, s=12, alpha=0.6, color='#2166AC', edgecolors='none', zorder=2)

    max_val = max(x.max(), y.max()) * 1.05
    ax.plot([0, max_val], [0, max_val], 'k--', linewidth=0.8, alpha=0.5, zorder=1)

    pearson_r, _ = stats.pearsonr(x, y)
    spearman_r, _ = stats.spearmanr(x, y)

    ax.text(0.05, 0.95, f'Pearson r = {pearson_r:.4f}\nSpearman ρ = {spearman_r:.4f}\nn = {len(merged_top100)}',
            transform=ax.transAxes, fontsize=8, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='gray', alpha=0.9))

    ax.set_xlabel('Published −log$_{10}$(P)', fontsize=9)
    ax.set_ylabel('BOLE −log$_{10}$(P)', fontsize=9)
    ax.set_title(TRAIT_LABELS.get(trait, trait), fontsize=10, fontweight='bold')
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.set_aspect('equal', adjustable='box')
    ax.tick_params(labelsize=8)


def plot_correlation_all():
    traits = list(TRAIT_FILES.keys())
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes_flat = axes.flatten()

    for i, trait in enumerate(traits):
        plot_correlation_scatter(trait, axes_flat[i])

    axes_flat[-1].set_visible(False)

    fig.suptitle('P-value Correlation: Published vs BOLE (Top 100 SNPs)', fontsize=13, fontweight='bold', y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.95])

    for fmt in ['pdf', 'png']:
        outpath = os.path.join(OUT_DIR, 'correlation_plots', f'pvalue_correlation_all.{fmt}')
        fig.savefig(outpath, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: correlation_plots/pvalue_correlation_all.pdf/png")

    for trait in traits:
        fig, ax = plt.subplots(1, 1, figsize=(5, 5))
        plot_correlation_scatter(trait, ax)
        fig.tight_layout()
        for fmt in ['pdf', 'png']:
            outpath = os.path.join(OUT_DIR, 'correlation_plots', f'{trait.lower()}_correlation.{fmt}')
            fig.savefig(outpath, bbox_inches='tight')
        plt.close(fig)
    print(f"  Saved: individual correlation plots for each trait")


def plot_mirrored_manhattan(trait, ax_top, ax_bot, paper_qtls):
    bole = load_bole_results(trait)
    paper = load_paper_pvalues(trait)

    offsets, chr_list = compute_chr_offsets(bole)

    bole['plot_pos'] = bole.apply(lambda r: offsets.get(r['Chr'], 0) + r['bp'], axis=1)
    paper['plot_pos'] = paper.apply(lambda r: offsets.get(r['chr'], 0) + r['bp'], axis=1)

    trait_qtls = paper_qtls[paper_qtls['Trait'] == trait] if paper_qtls is not None else pd.DataFrame()

    for c in chr_list:
        color = CHR_COLORS_ALT[c % 2]

        bole_c = bole[bole['Chr'] == c]
        ax_top.scatter(bole_c['plot_pos'], bole_c['neg_log10_p'],
                       s=2, alpha=0.5, color=color, edgecolors='none', rasterized=True)

        paper_c = paper[paper['chr'] == c]
        ax_bot.scatter(paper_c['plot_pos'], -paper_c['neg_log10_p'],
                       s=2, alpha=0.5, color=color, edgecolors='none', rasterized=True)

    for _, qtl in trait_qtls.iterrows():
        qtl_chr = qtl['QTL_chr']
        if qtl_chr not in offsets:
            continue
        x_start = offsets[qtl_chr] + qtl['QTL_start']
        x_end = offsets[qtl_chr] + qtl['QTL_end']

        max_y_top = ax_top.get_ylim()[1] if ax_top.get_ylim()[1] > 0 else 15
        rect_top = mpatches.FancyBboxPatch(
            (x_start, 0), x_end - x_start, max_y_top,
            boxstyle="square,pad=0", facecolor='red', alpha=0.08, edgecolor='none'
        )
        ax_top.add_patch(rect_top)
        ax_bot.add_patch(mpatches.FancyBboxPatch(
            (x_start, -max_y_top), x_end - x_start, max_y_top,
            boxstyle="square,pad=0", facecolor='red', alpha=0.08, edgecolor='none'
        ))

        if qtl['Lead_SNP_chr'] is not None and not pd.isna(qtl['Lead_SNP_bp']):
            lead_x = offsets[qtl['Lead_SNP_chr']] + qtl['Lead_SNP_bp']
            ax_top.scatter([lead_x], [bole[bole['Chr'] == qtl['Lead_SNP_chr']].nlargest(1, 'neg_log10_p')['neg_log10_p'].values[0] if len(bole[bole['Chr'] == qtl['Lead_SNP_chr']]) > 0 else 0],
                          marker='v', s=40, color='red', zorder=5, edgecolors='darkred', linewidths=0.5)
            ax_bot.scatter([lead_x], [-paper[paper['chr'] == qtl['Lead_SNP_chr']].nlargest(1, 'neg_log10_p')['neg_log10_p'].values[0] if len(paper[paper['chr'] == qtl['Lead_SNP_chr']]) > 0 else 0],
                          marker='^', s=40, color='red', zorder=5, edgecolors='darkred', linewidths=0.5)

    sig_y = -np.log10(SIG_THRESHOLD)
    ax_top.axhline(y=sig_y, color='red', linestyle='--', linewidth=0.8, alpha=0.7)
    ax_bot.axhline(y=-sig_y, color='red', linestyle='--', linewidth=0.8, alpha=0.7)

    sugg_y = -np.log10(SUGGESTIVE_THRESHOLD)
    ax_top.axhline(y=sugg_y, color='gray', linestyle=':', linewidth=0.6, alpha=0.5)
    ax_bot.axhline(y=-sugg_y, color='gray', linestyle=':', linewidth=0.6, alpha=0.5)

    chr_ticks = []
    chr_labels = []
    for c in chr_list:
        chr_max = bole[bole['Chr'] == c]['bp'].max()
        chr_ticks.append(offsets[c] + chr_max / 2)
        chr_labels.append(str(c))

    ax_top.set_xticks(chr_ticks)
    ax_top.set_xticklabels([])
    ax_bot.set_xticks(chr_ticks)
    ax_bot.set_xticklabels(chr_labels, fontsize=12)

    max_p_top = max(bole['neg_log10_p'].max(), sig_y + 2)
    ax_top.set_ylim(0, max_p_top * 1.05)
    ax_bot.set_ylim(-max_p_top * 1.05, 0)

    ax_top.set_ylabel('BOLE\n−log$_{10}$(P)', fontsize=9)
    ax_bot.set_ylabel('Published\n−log$_{10}$(P)', fontsize=9)
    ax_bot.set_xlabel('Chromosome', fontsize=12)

    ax_top.set_title(TRAIT_LABELS.get(trait, trait), fontsize=11, fontweight='bold')

    ax_top.spines['bottom'].set_visible(False)
    ax_bot.spines['top'].set_visible(False)
    ax_top.tick_params(bottom=False)
    ax_bot.tick_params(top=False)


def plot_mirrored_manhattan_all():
    paper_qtls = extract_paper_qtls()
    traits = list(TRAIT_FILES.keys())

    for trait in traits:
        fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(14, 5), gridspec_kw={'height_ratios': [1, 1], 'hspace': 0.05})
        plot_mirrored_manhattan(trait, ax_top, ax_bot, paper_qtls)
        fig.tight_layout()
        for fmt in ['pdf', 'png']:
            outpath = os.path.join(OUT_DIR, 'mirrored_manhattan', f'{trait.lower()}_mirrored_manhattan.{fmt}')
            fig.savefig(outpath, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved: mirrored_manhattan/{trait.lower()}_mirrored_manhattan.pdf/png")

    fig_all, axes_all = plt.subplots(14, 1, figsize=(14, 35))
    for i, trait in enumerate(traits):
        plot_mirrored_manhattan(trait, axes_all[i * 2], axes_all[i * 2 + 1], paper_qtls)
    fig_all.suptitle('Mirrored Manhattan Plots: BOLE (top) vs Published (bottom)', fontsize=14, fontweight='bold', y=0.995)
    fig_all.tight_layout(rect=[0, 0, 1, 0.99])
    for fmt in ['pdf', 'png']:
        outpath = os.path.join(OUT_DIR, 'mirrored_manhattan', f'all_traits_mirrored_manhattan.{fmt}')
        fig_all.savefig(outpath, bbox_inches='tight')
    plt.close(fig_all)
    print(f"  Saved: mirrored_manhattan/all_traits_mirrored_manhattan.pdf/png")


def main():
    print("=" * 60)
    print("Part 2: Correlation Scatter Plots")
    print("=" * 60)
    plot_correlation_all()

    print("\n" + "=" * 60)
    print("Part 3: Mirrored Manhattan Plots")
    print("=" * 60)
    plot_mirrored_manhattan_all()

    print("\nAll visualizations generated successfully!")


if __name__ == "__main__":
    main()
