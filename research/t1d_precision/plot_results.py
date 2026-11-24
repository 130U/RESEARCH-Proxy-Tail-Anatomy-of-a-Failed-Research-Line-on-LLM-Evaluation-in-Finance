"""Three-panel T1D figure from complete saved results; no model calls."""
from pathlib import Path
import argparse
import json
import math
import sys

ROOT = Path(__file__).resolve().parent
try:
    import matplotlib
except ImportError:
    sys.path.insert(0, str(ROOT.parents[2] / 'tmp/tail_plot_deps'))
    import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import font_manager
import numpy as np

COLORS = {'A': '#7b7b7b', 'B': '#246b9e', 'C': '#bd691d'}
MARKERS = {'A': 'o', 'B': 's', 'C': '^'}


def metric(result, condition, name):
    return result['summary_table'][condition]['metrics'][name]


def precision_panel(ax, rows):
    all_x, all_y = [], []
    labels = {'A': 'A: printed digits', 'B': 'B: self-reported reliable digits', 'C': 'C: self-reported reliable digits'}
    for condition in ('A', 'B', 'C'):
        sample = [r for r in rows if r['condition'] == condition and r['scorable']]
        x = [r['d_star'] for r in sample]
        y = [r['claimed_digits'] for r in sample]
        all_x.extend(x); all_y.extend(y)
        ax.scatter(x, y, marker=MARKERS[condition], s=19 if condition == 'A' else 25,
                   c=COLORS[condition], alpha=.43 if condition == 'A' else .65,
                   linewidths=0, label=f'{labels[condition]} (n={len(sample)})', rasterized=True)
    if not all_x:
        ax.text(.5, .5, 'No scorable responses yet', transform=ax.transAxes, ha='center')
    else:
        lo = min(-.3, math.floor(min(all_x) * 2) / 2 - .2)
        hi = max(1, math.ceil(max(all_x) * 2) / 2 + .3)
        ax.set_xlim(lo, hi)
        ax.set_ylim(min(-.5, min(all_y) - .5), max(2, max(all_y) + 1))
        line_lo, line_hi = max(lo, -.5), min(hi, ax.get_ylim()[1])
        ax.plot([line_lo, line_hi], [line_lo, line_hi], color='#2c2c2c', linestyle='--', linewidth=1, zorder=0)
    ax.set_xlabel(r'True reliable digits $d^*=\log_{10}(|c|/h^*)$')
    ax.set_ylabel('Printed digits / self-reported reliable digits')
    ax.set_title('a  Reported digits vs. true precision', loc='left', fontweight='bold')
    ax.legend(frameon=False, fontsize=8, loc='upper right')


def interval_panel(ax, rows):
    positives = []
    counts = {}
    for condition in ('B', 'C'):
        values = np.array([r['r'] for r in rows if r['condition'] == condition and r['scorable']], dtype=float)
        positive = np.sort(values[values > 0])
        nonpositive = int(np.sum(values <= 0))
        counts[condition] = nonpositive
        positives.extend(positive)
        if len(positive):
            y = 100 * (np.arange(1, len(positive) + 1) + nonpositive) / len(values)
            ax.step(positive, y, where='post', color=COLORS[condition], linewidth=1.8,
                    label=f'{condition} (n={len(values)})')
        elif len(values):
            ax.plot([], [], color=COLORS[condition], label=f'{condition}: all r≤0 (n={len(values)})')
    ax.set_xscale('log')
    lo = min(.1, min(positives) / 1.4) if positives else .1
    hi = max(10, max(positives) * 1.4) if positives else 10
    ax.set_xlim(lo, hi)
    ax.axvspan(.5, 2, color='#dce7e3', alpha=.8, zorder=-3)
    for boundary in (.5, 2):
        ax.axvline(boundary, color='#55665f', linestyle='--', linewidth=1, zorder=-1)
    ax.text(1, 4, 'Width accurate', fontsize=8, ha='center', rotation=90, va='bottom', color='#40564c')
    ax.set_ylim(0, 103)
    ax.set_xlabel(r'Width ratio $r=(high-low)/(U^*-L^*)$ (log scale)')
    ax.set_ylabel('Cumulative share (%)')
    ax.set_title('b  Width of self-reported intervals', loc='left', fontweight='bold')
    if ax.get_legend_handles_labels()[0]:
        ax.legend(frameon=False, fontsize=9, loc='lower right')
    ax.text(.01, -.25, f'Non-positive width ratios (r≤0): B={counts.get("B", 0)}, C={counts.get("C", 0)}\n(counted in the cumulative share, not placed on the log axis as fake positive values)',
            transform=ax.transAxes, fontsize=7.5, color='#555555', va='top')


def plot_point(ax, x, summary, condition, label_offset=0, label_alignment='center'):
    value, interval = summary.get('estimate'), summary.get('ci95')
    if value is None:
        return
    ax.scatter([x], [100 * value], color=COLORS[condition], marker=MARKERS[condition], s=42, zorder=5)
    if interval is not None:
        # Draw interval endpoints directly so percentile CIs need not be forced
        # to contain the point estimate by clipping an errorbar size.
        ax.vlines(x, 100 * interval[0], 100 * interval[1], color=COLORS[condition], linewidth=1.5)
        ax.hlines([100 * interval[0], 100 * interval[1]], x - .045, x + .045, color=COLORS[condition], linewidth=1.2)
    ax.annotate(f'{100 * value:.1f}', (x, 100 * value), xytext=(label_offset, 7), textcoords='offset points', ha=label_alignment, fontsize=8, color=COLORS[condition])


def accuracy_panel(ax, result):
    plot_point(ax, 0, metric(result, 'B', 'onepct_accuracy'), 'B')
    plot_point(ax, 1, metric(result, 'C', 'onepct_accuracy'), 'C')
    for x, name in ((2, 'first_order_accuracy'), (3, 'always_certain_accuracy')):
        plot_point(ax, x - .12, metric(result, 'B', name), 'B', -3, 'right')
        plot_point(ax, x + .12, metric(result, 'C', name), 'C', 3, 'left')
    ax.set_xlim(-.45, 3.45)
    ax.set_ylim(0, 109)
    ax.set_xticks([0, 1, 2, 3], ['B', 'C', 'First-order\nrule', 'Always answer\ncertain'])
    ax.set_ylabel('1% certainty judgment accuracy (%)')
    ax.set_title('c  Can the model recognize 1% certainty?', loc='left', fontweight='bold')
    handles = [Line2D([], [], marker=MARKERS[c], color=COLORS[c], linestyle='None', markersize=6,
                      label=f'{c}: computed on its own formulas and scorable questions') for c in ('B', 'C')]
    ax.legend(handles=handles, frameon=False, fontsize=7.8, loc='lower left')
    ax.text(.01, -.25, 'Vertical lines: 95% intervals from the page-cluster bootstrap.\nEach baseline uses the truth values from the\ncorresponding condition\'s own formulas.',
            transform=ax.transAxes, fontsize=7.5, color='#555555', va='top')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-incomplete', action='store_true')
    args = parser.parse_args()
    result = json.loads((ROOT / 'results.json').read_text(encoding='utf8'))
    if not result['complete'] and not args.allow_incomplete:
        raise SystemExit('Do not generate a final figure before inference and adjudication are complete.')
    rows = [json.loads(s) for s in (ROOT / 'per_response.jsonl').read_text(encoding='utf8').splitlines() if s.strip()]
    rows = [r for r in rows if r['condition'] in ('A', 'B', 'C')]
    if result['sample']['C_design'] == 'half':
        c_ids = set(json.loads((ROOT / 'private/c_half_ids.json').read_text(encoding='utf8')))
        rows = [r for r in rows if r['condition'] != 'C' or r['call_id'] in c_ids]
    for condition in ('A', 'B', 'C'):
        available = [r for r in rows if r['condition'] == condition]
        scorable = [r for r in available if r['scorable']]
        summary = result['summary_table'][condition]
        if len(available) != summary['available_n'] or len(scorable) != summary['scorable_n']:
            raise SystemExit('Scored rows changed after analysis; rerun analyze_precision.py before plotting.')
        if scorable:
            for source_field, metric_name in (('claimed_digits', 'claimed_digits'), ('d_star', 'true_digits')):
                if not math.isclose(float(np.median([r[source_field] for r in scorable])), summary['metrics'][metric_name]['estimate'], rel_tol=1e-12, abs_tol=1e-12):
                    raise SystemExit('Scored precision values changed after analysis; rerun analysis before plotting.')
    selected_font = None
    for font in ('Arial', 'Helvetica', 'DejaVu Sans'):
        try:
            font_manager.findfont(font, fallback_to_default=False)
            selected_font = font
            break
        except ValueError:
            continue
    if selected_font is None:
        raise SystemExit('A sans-serif font (Arial, Helvetica or DejaVu Sans) is required before rendering.')
    plt.rcParams.update({'font.family': selected_font, 'axes.unicode_minus': False,
                         'font.size': 9, 'axes.titlesize': 10.5, 'axes.labelsize': 9,
                         'xtick.labelsize': 8.5, 'ytick.labelsize': 8.5, 'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.9), gridspec_kw={'width_ratios': [1.1, 1, 1.05]})
    for ax in axes:
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', linewidth=.5, color='#e7e7e7', zorder=-5)
        ax.tick_params(length=3)
    precision_panel(axes[0], rows)
    interval_panel(axes[1], rows)
    accuracy_panel(axes[2], result)
    title = 'T1D · Can the model judge the precision of its own formula?'
    if not result['complete']:
        title = 'Incomplete preview · ' + title
    fig.suptitle(title, x=.065, ha='left', y=.98, fontsize=14, fontweight='bold')
    nb, nc = result['sample']['expected_by_condition']['B'], result['sample']['expected_by_condition']['C']
    fig.text(.065, .055, f'A reuses the original answers; B asks about precision; C additionally teaches a rule paragraph. Planned questions for B/C: {nb}/{nc}; all three panels use scorable responses.', fontsize=8, color='#444444')
    fig.text(.065, .025, 'A\'s printed digits are not an active statement of reliable digits. B was told that the inputs are rounded. Exact truth intervals are computed from the model\'s own formula and its bound sources.', fontsize=8, color='#444444')
    fig.subplots_adjust(left=.065, right=.985, top=.85, bottom=.29, wspace=.34)
    stem = 't1d_results' if result['complete'] else 't1d_preview_incomplete'
    fig.savefig(ROOT / f'{stem}.png', dpi=200, facecolor='white')
    fig.savefig(ROOT / f'{stem}.pdf', facecolor='white')
    plt.close(fig)
    print(json.dumps({'figure': stem, 'complete': result['complete']}))


if __name__ == '__main__':
    main()
