"""
Generate English versions of the 3 thesis figures for Chapter 3.
Outputs saved as *_en.png in notebooks/figures/ (originals untouched).

Usage:
    python scripts/generate_thesis_figures_en.py
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT       = os.path.join(os.path.dirname(__file__), '..')
OUT_DIR    = os.path.join(ROOT, 'notebooks', 'figures')
MASTER     = os.path.join(ROOT, 'data', 'phuket_master.csv')
SUMMARIES  = os.path.join(ROOT, 'tomtom_phuket', 'processed', 'summaries_all.csv')

# ── Shared corridor config ────────────────────────────────────────────────────

# summaries_all.csv uses "to" not "→"
ROUTE_SHORT = {
    'Airport Road (Route 402)':          'Airport Rd',
    'Patong Hill (Route 4029)':           'Patong Hill',
    'Phuket Town to Rawai (Route 4022)':  'Town→Rawai',
    'Bypass Road (Route 4027)':           'Bypass Rd',
}
# master.csv uses "→"
MASTER_SHORT = {
    'Airport Road (Route 402)':           'Airport Rd',
    'Patong Hill (Route 4029)':            'Patong Hill',
    'Phuket Town → Rawai (Route 4022)':   'Town→Rawai',
    'Bypass Road (Route 4027)':            'Bypass Rd',
}

COLORS = {
    'Airport Rd':   '#4C72B0',
    'Patong Hill':  '#DD8452',
    'Town→Rawai':   '#55A868',
    'Bypass Rd':    '#C44E52',
}

CORRIDORS_ORDER = ['Airport Rd', 'Patong Hill', 'Town→Rawai', 'Bypass Rd']


# ── Figure 1: Monthly TTR evolution ──────────────────────────────────────────
def fig1_ttr_monthly():
    df = pd.read_csv(SUMMARIES)
    df['month_date'] = pd.to_datetime(df['date_from'])
    df['short'] = df['route_name'].map(ROUTE_SHORT)

    PANELS = [
        ('Weekday_AM1',    'AM Peak (07h–09h)'),
        ('Weekday_Midday', 'Off-peak (10h–15h)'),
        ('Weekday_PM1',    'PM Peak (17h–19h)'),
        ('Weekend_AM1',    'Weekend Morning'),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle(
        'Monthly Travel Time Ratio (TTR) by corridor\n'
        'Source: TomTom MOVE - January 2023 to December 2024',
        fontsize=13, fontweight='bold'
    )

    for ax, (ts, title) in zip(axes.flat, PANELS):
        sub = df[df['timeset_name'] == ts].sort_values('month_date')
        for short in CORRIDORS_ORDER:
            s = sub[sub['short'] == short]
            ax.plot(
                s['month_date'], s['avg_travel_time_ratio'],
                'o-', linewidth=2, markersize=4,
                label=short, color=COLORS[short]
            )

        ax.set_title(title, fontsize=11)
        ax.set_ylabel('TTR')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.tick_params(axis='x', rotation=45)
        ax.legend(fontsize=9, loc='upper right')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'fig_ttr_monthly_evolution_en.png')
    plt.savefig(out, bbox_inches='tight', dpi=150)
    plt.close()
    print(f'Saved {out}')


# ── Figure 2: Corridor ranking ────────────────────────────────────────────────
def fig2_corridor_ranking():
    df = pd.read_csv(SUMMARIES)
    df['short'] = df['route_name'].map(ROUTE_SHORT)

    METRICS = [
        ('Weekday_AM1',  'avg_travel_time_ratio', 'TTR - Weekday AM Peak',        True),
        ('Weekday_PM1',  'avg_travel_time_ratio', 'TTR - Weekday PM Peak',        True),
        ('Weekday_AM1',  'planning_time_index',   'Planning Time Index (mean)',    True),
        ('Weekday_AM1',  'harmonic_avg_speed',    'Speed - Weekday AM Peak (km/h)', False),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(18, 5))
    fig.suptitle(
        'Corridor Profile Comparison - Average Traffic Indicators (January 2023 to December 2024)',
        fontsize=12, fontweight='bold'
    )

    for ax, (ts, col, label, higher_worse) in zip(axes, METRICS):
        means = (
            df[df['timeset_name'] == ts]
            .groupby('short')[col].mean()
            .sort_values(ascending=not higher_worse)
            .reset_index()
        )
        colors = [COLORS[c] for c in means['short']]
        ax.barh(means['short'], means[col], color=colors, edgecolor='white')
        ax.set_title(label, fontsize=9)
        for i, (_, row) in enumerate(means.iterrows()):
            ax.text(
                row[col] * 0.03, i,
                f'{row[col]:.3f}',
                va='center', fontsize=9, color='white', fontweight='bold'
            )
        ax.grid(True, axis='x', alpha=0.3)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'fig_corridor_ranking_en.png')
    plt.savefig(out, bbox_inches='tight', dpi=150)
    plt.close()
    print(f'Saved {out}')


# ── Figure 3: Season distributions ───────────────────────────────────────────
def fig3_season_distributions():
    df = pd.read_csv(MASTER)
    df_agg = (
        df.groupby(['year', 'month', 'season'])[['flt_total_pax', 'wx_rain_mm_sum']]
        .mean()
        .reset_index()
    )

    SEASON_ORDER  = ['high_peak', 'shoulder', 'monsoon']
    SEASON_LABELS = {'high_peak': 'High Season', 'shoulder': 'Shoulder', 'monsoon': 'Monsoon'}
    SEASON_COLORS = {'high_peak': '#4CAF50',     'shoulder': '#FFC107',   'monsoon': '#2196F3'}

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(
        'Distribution of Exogenous Variables by Season (January 2023 to December 2024)',
        fontsize=12, fontweight='bold'
    )

    for ax, (col, label) in zip(axes, [
        ('flt_total_pax',  'HKT Total Passengers'),
        ('wx_rain_mm_sum', 'Monthly Rainfall (mm)'),
    ]):
        present   = [s for s in SEASON_ORDER if s in df_agg['season'].values]
        data_list = [df_agg[df_agg['season'] == s][col].values for s in present]
        xlabels   = [SEASON_LABELS[s] for s in present]
        bp = ax.boxplot(data_list, labels=xlabels, patch_artist=True)
        for patch, s in zip(bp['boxes'], present):
            patch.set_facecolor(SEASON_COLORS[s])
            patch.set_alpha(0.75)
        ax.set_title(label, fontsize=11)
        ax.tick_params(axis='x', rotation=10)
        ax.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'fig_season_distributions_en.png')
    plt.savefig(out, bbox_inches='tight', dpi=150)
    plt.close()
    print(f'Saved {out}')


if __name__ == '__main__':
    fig1_ttr_monthly()
    fig2_corridor_ranking()
    fig3_season_distributions()
    print('Done.')
