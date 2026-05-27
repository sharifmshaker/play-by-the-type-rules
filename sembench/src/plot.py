#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pandas",
#   "numpy",
#   "seaborn",
#   "matplotlib",
#   "altair",
#   "cairosvg",
#   "vl-convert-python"
# ]
# ///

import os
import math
import pandas as pd
import re
import seaborn as sns
import matplotlib.pyplot as plt
import altair as alt
from pathlib import Path
from typing import Optional, Literal
import warnings
import statistics
warnings.filterwarnings('ignore')

from src.closed_model_stats import MOVIE_STATS, ECOMM_STATS, MMQA_STATS, WILDLIFE_STATS, CARS_STATS

sns.set_palette("Spectral")
plt.rcParams['font.family'] = 'DeJavu Serif'
plt.rcParams['font.serif'] = ['Times New Roman']

# ── Config from environment ───────────────────────────────────────────────────
RESULTS_DIR = Path(os.environ["RESULTS_DIR"])
IS_COMPARABLE_TO_ORIGINAL_SEMBENCH = os.environ["IS_COMPARABLE_TO_ORIGINAL_SEMBENCH"] == '1'
sembench_split = os.environ["SEMBENCH_SPLIT"]

if sembench_split.startswith('movie'):
    stats = pd.DataFrame(MOVIE_STATS)
elif sembench_split.startswith('ecomm'):
    stats = pd.DataFrame(ECOMM_STATS)
elif sembench_split.startswith('mmqa'):
    stats = pd.DataFrame(MMQA_STATS)
elif sembench_split.startswith('wildlife'):
    stats = pd.DataFrame(WILDLIFE_STATS)
elif sembench_split.startswith('cars'):
    stats = pd.DataFrame(CARS_STATS)
else:
    raise ValueError(f"Unknown sembench split: {sembench_split}")

# Per-hour compute cost used to derive dollar cost from latency.
# Override via the HOURLY_RATE environment variable if needed.
LOCAL_HOURLY_RATE = float(os.environ.get("HOURLY_RATE", "0.18"))


def load_results(results_path: Path) -> pd.DataFrame:
    df = pd.read_csv(results_path)
    df = df.sort_values(by='system_name', ascending=True)
    print(f"Loaded {len(df)} rows from {results_path}")
    print(f"Systems: {df['system_name'].unique()}")
    print(f"Runs per system: {df.groupby('system_name')['run'].nunique().to_dict()}")
    print(f"Queries: {df['query_name'].unique()}\n")
    return df


def plot_performance_scatter_comparison(
    dfs: list[pd.DataFrame],
    subtitles: list[str],
    horizontal_line: Optional[float] = None,
    vertical_line: Optional[float] = None,
    save_path: Optional[Path] = None,
):
    n_plots = len(dfs)
    if n_plots < 1:
        raise ValueError("Must provide at least 1 DataFrame")
    if len(subtitles) != n_plots:
        raise ValueError("Number of subtitles must match number of DataFrames")

    max_cols = 2
    ncols = min(n_plots, max_cols)
    nrows = math.ceil(n_plots / ncols)
    figsize = (8 * ncols, 3 * nrows)

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, squeeze=False)
    plt.rc('font', size=14)

    axes_flat = axes.flatten()

    for i in range(n_plots, len(axes_flat)):
        axes_flat[i].set_visible(False)

    all_systems = pd.concat([df['system_name'] for df in dfs]).unique()
    colors = sns.color_palette("husl", len(all_systems))
    color_map = dict(zip(all_systems, colors))

    def plot_on_axis(ax, df, subtitle):
        if horizontal_line is not None:
            ax.axhline(y=horizontal_line, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, zorder=2)
        if vertical_line is not None:
            ax.axvline(x=vertical_line, color='gray', linestyle='--', linewidth=1.5, alpha=0.7, zorder=2)

        for system in df['system_name'].unique():
            system_df = df[df['system_name'] == system]
            color = color_map[system]

            ax.scatter(system_df['latency'], system_df['quality'],
                      label=system, alpha=0.6, s=50, color=color,
                      edgecolor='black', linewidth=0.5)

            for _, row in system_df.iterrows():
                query_label = row['query_name'] if row['query_name'].startswith('Q') else f"Q{row['query_name']}"
                ax.annotate(query_label, (row['latency'], row['quality']),
                           xytext=(3, 3), textcoords='offset points',
                           fontsize=7, alpha=0.7, color=color)

            mean_latency = system_df['latency'].mean()
            mean_quality = system_df['quality'].mean()
            ax.scatter(mean_latency, mean_quality, s=200, color=color, marker='D',
                      edgecolor='black', linewidth=2, label=f'{system} (mean)', zorder=5)

        ax.invert_xaxis()
        ax.set_title(subtitle, fontsize=16, style='italic')
        ax.set_xlabel('Latency (s)', fontsize=12)
        ax.set_ylabel('Quality', fontsize=12)
        ax.grid(True, alpha=0.3)

    for ax, df, subtitle in zip(axes_flat[:n_plots], dfs, subtitles):
        plot_on_axis(ax, df, subtitle)

    all_handles, all_labels = [], []
    for ax in axes_flat[:n_plots]:
        handles, labels = ax.get_legend_handles_labels()
        all_handles.extend(handles)
        all_labels.extend(labels)

    handles_labels = dict(zip(all_labels, all_handles))
    unique_labels = sorted(handles_labels.keys())
    unique_handles = [handles_labels[label] for label in unique_labels]

    for ax in axes_flat[:n_plots]:
        if ax.get_legend():
            ax.legend().remove()

    fig.legend(unique_handles, unique_labels,
               bbox_to_anchor=(0.5, 1.02), loc='lower center',
               borderaxespad=0, fontsize=13, frameon=True,
               fancybox=True, shadow=True, ncol=min(len(unique_labels), 6))

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=400, bbox_inches='tight')
        print(f"Saved plot to {save_path}")


def plot_cost_by_query(
    df: pd.DataFrame,
    hourly_rate: float,
    figsize=(14, 6),
    save_path: Optional[Path] = None,
):
    """Plot average compute cost per query, grouped by system, using Altair.

    Cost per row is ``latency * hourly_rate / 3600``.  No external baseline
    is shown — this chart only compares the systems present in *df*.
    """

    df = df.copy()
    df['cost'] = round(df['latency'] * hourly_rate / 3600.0, 2)

    cost_summary = (
        df.groupby(['query_name', 'system_name'])['cost']
        .sum()
        .reset_index()
    )
    cost_summary = cost_summary[~pd.isna(cost_summary['cost'])]

    # Format labels: scientific notation for < $0.01, fixed otherwise
    cost_summary['cost_label'] = cost_summary['cost'].apply(
        lambda v: f'{v:.1e}' if v < 0.01 else f'{v:.2f}'
    )

    queries = sorted(df['query_name'].unique())
    systems = ['blendsql', 'thalamusdb', 'lotus', 'palimpzest']

    colors = ['#f77189', '#3ba3ec', '#3fad2b', '#FFA500']

    chart_width = int(figsize[0] * 50)
    chart_height = int(figsize[1] * 50)

    bars = alt.Chart(cost_summary).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        stroke='black',
        strokeWidth=0.5,
        opacity=0.8
    ).encode(
        x=alt.X('query_name:N',
                 title='Query',
                 sort=queries,
                 axis=alt.Axis(labelAngle=-45)),
        xOffset=alt.XOffset('system_name:N', sort=systems),
        y=alt.Y('cost:Q',
                 title='Cost ($)'),
        color=alt.Color('system_name:N',
                         title='System',
                         scale=alt.Scale(domain=systems, range=colors[:len(systems)]),
                         legend=alt.Legend(
                             orient='none',
                             legendX=chart_width - 83,
                             legendY=0,
                             fillColor='rgba(255, 255, 255, 0.9)',
                             strokeColor='#cccccc',
                             padding=10,
                             cornerRadius=2,
                         ))
    )

    labels = alt.Chart(cost_summary).mark_text(
        dy=-5,
        fontSize=8
    ).encode(
        x=alt.X('query_name:N', sort=queries),
        xOffset=alt.XOffset('system_name:N', sort=systems),
        y=alt.Y('cost:Q'),
        text=alt.Text('cost_label:N'),
        color=alt.value('black')
    )

    chart = (bars + labels).properties(
        width=chart_width,
        height=chart_height
    ).configure(
        font='serif'
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12,
        labelFont='serif',
        titleFont='serif',
        grid=True,
        gridOpacity=0.3
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=10,
        labelFont='serif',
        titleFont='serif',
    ).configure_title(
        font='serif'
    )

    if save_path:
        save_path = Path(save_path)
        if save_path.suffix.lower() == '.pdf':
            svg_path = save_path.with_suffix('.svg')
            chart.save(str(svg_path))
            import cairosvg
            cairosvg.svg2pdf(url=str(svg_path), write_to=str(save_path))
            svg_path.unlink()
        else:
            chart.save(str(save_path))

    return chart


def plot_cost_comparison(
    df: pd.DataFrame,
    hourly_rate: float,
    baseline_stats: pd.DataFrame,
    aggregate_closed_on: Literal['sum', 'mean'],
    figsize=(6, 6),
    save_path: Optional[Path] = None,
):
    """Two-bar chart comparing the overall average cost of our systems vs.
    the SemBench baseline average.

    baseline_stats should already be filtered to only the queries present in df.
    """

    df = df.copy()
    df['cost'] = round(df['latency'] * hourly_rate / 3600.0, 2)
    n_runs = len(df['run'].unique())
    overall_sum = df['cost'].sum()
    open_bar_name = 'Local, Open LMs'
    closed_bar_name = 'Remote, Proprietary LMs'
    if aggregate_closed_on == 'sum':
        closed_model_cost = round(baseline_stats['cost'].sum() * n_runs, 2)

    elif aggregate_closed_on == 'mean':
        # Get mean for each system
        closed_model_cost = round(baseline_stats['cost'].mean() * n_runs, 2)

    compare_df = pd.DataFrame([
        {'source': open_bar_name, 'cost': round(overall_sum, 2)},
        {'source': closed_bar_name, 'cost': closed_model_cost},
    ])

    colors = ['#3ba3ec', '#f77189']

    chart_width = int(figsize[0] * 75)
    chart_height = int(figsize[1] * 50)

    bars = alt.Chart(compare_df).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        stroke='black',
        strokeWidth=0.5,
        opacity=0.8
    ).encode(
        x=alt.X('source:N',
                 title=None,
                 sort=[closed_bar_name, open_bar_name],
                 axis=alt.Axis(labelAngle=0)),
        y=alt.Y('cost:Q',
                 title=f'Total Cost, {n_runs} Runs'),
        color=alt.Color('source:N',
                         title=None,
                         scale=alt.Scale(
                             domain=[closed_bar_name, open_bar_name],
                             range=colors),
                         legend=None)
    )

    labels = alt.Chart(compare_df).mark_text(
        dy=-8,
        fontSize=12,
        fontWeight='bold'
    ).encode(
        x=alt.X('source:N', sort=[closed_bar_name, open_bar_name]),
        y=alt.Y('cost:Q'),
        text=alt.Text('cost:Q', format='$.2f'),
        color=alt.value('black')
    )

    chart = (bars + labels).properties(
        width=chart_width,
        height=chart_height
    ).configure(
        font='serif'
    ).configure_axis(
        labelFontSize=14,
        titleFontSize=14,
        labelFont='serif',
        titleFont='serif',
        grid=True,
        gridOpacity=0.3
    ).configure_title(
        font='serif'
    )

    if save_path:
        save_path = Path(save_path)
        if save_path.suffix.lower() == '.pdf':
            svg_path = save_path.with_suffix('.svg')
            chart.save(str(svg_path))
            import cairosvg
            cairosvg.svg2pdf(url=str(svg_path), write_to=str(save_path))
            svg_path.unlink()
        else:
            chart.save(str(save_path))

    return chart


def plot_generation_calls_by_query(
    df: pd.DataFrame,
    figsize=(14, 6),
    width=None,
    save_path: Optional[Path] = None
):
    """Plot average number of generation calls for each query, grouped by system using Altair."""

    df = df.copy()
    df = df[df['system_name'].isin(['blendsql', 'thalamusdb'])]
    df['num_generation_calls'] = df['num_generation_calls'].apply(lambda x: int(x))
    # Calculate average generation calls per query per system (averaged across runs)
    calls_summary = df.groupby(['query_name', 'system_name'])['num_generation_calls'].mean().reset_index()
    calls_summary = calls_summary[~pd.isna(calls_summary['num_generation_calls'])]
    calls_summary['num_generation_calls'] = calls_summary['num_generation_calls'].astype(int)

    # Get unique queries and systems
    queries = sorted(df['query_name'].unique())
    systems = list(df['system_name'].unique())

    colors = ['#f77189', '#3ba3ec', '#3fad2b']

    # Convert figsize (inches) to pixels (assuming ~80 pixels per inch for web display)
    chart_width = int(figsize[0] * 50)
    chart_height = int(figsize[1] * 50)

    # Create the grouped bar chart
    bars = alt.Chart(calls_summary).mark_bar(
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4,
        stroke='black',
        strokeWidth=0.5,
        opacity=0.8
    ).encode(
        x=alt.X('query_name:N',
                title='Query',
                sort=queries,
                axis=alt.Axis(labelAngle=-45)),
        xOffset=alt.XOffset('system_name:N', sort=systems),
        y=alt.Y('num_generation_calls:Q',
                title='# LM Generation Calls'),
        color=alt.Color('system_name:N',
                   title='System',
                   scale=alt.Scale(domain=systems, range=colors),
                   legend=alt.Legend(
                       orient='none',
                       legendX=chart_width - 83,  # Position from left
                       legendY=0,  # Position from top
                       fillColor='rgba(255, 255, 255, 0.9)',
                       strokeColor='#cccccc',
                       padding=10,
                       cornerRadius=2,
                   ))
    )

    # Add value labels on bars
    labels = alt.Chart(calls_summary).mark_text(
        dy=-5,
        fontSize=8
    ).encode(
        x=alt.X('query_name:N', sort=queries),
        xOffset=alt.XOffset('system_name:N', sort=systems),
        y=alt.Y('num_generation_calls:Q'),
        text=alt.Text('num_generation_calls:Q', format='d'),
        color=alt.value('black')
    )

    chart = (bars + labels).properties(
        width=chart_width,
        height=chart_height
    ).configure(
        font='serif'  # Use generic 'serif' for better PDF compatibility
    ).configure_axis(
        labelFontSize=12,
        titleFontSize=12,
        labelFont='serif',
        titleFont='serif',
        grid=True,
        gridOpacity=0.3
    ).configure_legend(
        titleFontSize=12,
        labelFontSize=10,
        labelFont='serif',
        titleFont='serif',
    ).configure_title(
        font='serif'
    )

    if save_path:
        # Save as SVG first, then convert to PDF for proper text embedding
        save_path = Path(save_path)
        if save_path.suffix.lower() == '.pdf':
            svg_path = save_path.with_suffix('.svg')
            chart.save(str(svg_path))
            import cairosvg
            cairosvg.svg2pdf(url=str(svg_path), write_to=str(save_path))
            svg_path.unlink()  # Remove temporary SVG
        else:
            chart.save(str(save_path))

    return chart


# ── Discover model result dirs ────────────────────────────────────────────────
dfs_to_plot = []
dfs_full = []
subtitles = []

for model_dir in sorted(RESULTS_DIR.iterdir()):
    results_path = model_dir / "all_results_with_runs.csv"
    if not model_dir.is_dir() or not results_path.exists():
        continue

    df = load_results(results_path)
    common_queries = (
        df.groupby('query_name')['system_name']
        .nunique()[lambda x: x == df['system_name'].nunique()]
        .index.tolist()
    )
    dfs_to_plot.append(df[df['query_name'].isin(common_queries)])
    dfs_full.append(df)
    subtitles.append(model_dir.name)  # use dir name as subtitle

if not dfs_to_plot:
    raise ValueError(f"No results found under {RESULTS_DIR}")

paired = sorted(zip(subtitles, dfs_to_plot, dfs_full), key=lambda x: int(re.search(r'(\d+)', x[0]).group(1)))
subtitles, dfs_to_plot, dfs_full = zip(*paired)
subtitles, dfs_to_plot, dfs_full = list(subtitles), list(dfs_to_plot), list(dfs_full)

all_result_queries = set(q for df in dfs_to_plot for q in df['query_name'].unique())
all_filtered_stats = stats[stats['query'].isin(all_result_queries)]

save_path = RESULTS_DIR / "performance_latency_scatter_all.pdf"
plot_performance_scatter_comparison(
    dfs_to_plot,
    subtitles,
    horizontal_line=all_filtered_stats['quality'].mean() if IS_COMPARABLE_TO_ORIGINAL_SEMBENCH else None,
    vertical_line=all_filtered_stats['latency'].mean() if IS_COMPARABLE_TO_ORIGINAL_SEMBENCH else None,
    save_path=save_path,
)

# ── Per-model generation calls + cost plots ───────────────────────────────────
for subtitle, df, df_full in zip(subtitles, dfs_to_plot, dfs_full):
    # Generation calls plot
    if 'num_generation_calls' not in df.columns:
        print(f"Skipping generation calls plot for {subtitle}: no 'num_generation_calls' column")
    else:
        gen_calls_save_path = RESULTS_DIR / subtitle / "generation_calls_by_query.pdf"
        plot_generation_calls_by_query(df, save_path=gen_calls_save_path)
        print(f"Saved generation calls plot to {gen_calls_save_path}")

    # Cost per query plot (systems only, no baseline)
    if 'latency' not in df_full.columns:
        print(f"Skipping cost plots for {subtitle}: no 'latency' column")
        continue
    cost_save_path = RESULTS_DIR / subtitle / "cost_by_query.pdf"
    plot_cost_by_query(
        df_full,
        hourly_rate=LOCAL_HOURLY_RATE,
        save_path=cost_save_path,
    )
    print(f"Saved cost-by-query plot to {cost_save_path}")

    # Two-bar overall average comparison (ours vs SemBench).
    # Filter stats to the [system, query] pairs that exist in MOVIE_STATS for the
    # queries actually run — ThalamusDB Q9/Q10 simply won't appear since they're
    # absent from MOVIE_STATS, while LOTUS/Palimpzest Q9/Q10 will be included.
    full_queries = df_full['query_name'].unique()
    df_filtered_stats = stats[stats['query'].isin(full_queries)]
    cost_comparison_save_path = RESULTS_DIR / subtitle / "cost_comparison.pdf"
    plot_cost_comparison(
        df_full,
        hourly_rate=LOCAL_HOURLY_RATE,
        baseline_stats=df_filtered_stats,
        aggregate_closed_on='sum' if sembench_split.startswith('movie') else 'mean',
        save_path=cost_comparison_save_path,
    )
    print(f"Saved cost comparison plot to {cost_comparison_save_path}")


    # ── LaTeX table: BlendSQL vs average baseline per query ───────────────────────
    # Add this code at the END of plot_results.py, after the final print statement.
    #
    # Requires in your LaTeX preamble:
    #   \usepackage{booktabs}
    #   \usepackage[table]{xcolor}
    #   \usepackage{tikz}
    #   \definecolor{bestgreen}{RGB}{198,239,206}
    #   \definecolor{tiecolor}{RGB}{255,255,191}
    #   \definecolor{rowgray}{RGB}{245,245,245}

    def generate_latex_table(
            df: pd.DataFrame,
            baseline_stats: pd.DataFrame,
            hourly_rate: float,
            subtitle: str,
            n_runs: int = 5,
            save_path: Optional[Path] = None,
    ):
        """Generate a LaTeX table comparing BlendSQL per-query metrics against the
        average of the baseline systems (LOTUS, Palimpzest, ThalamusDB) from the
        STATS variable.

        Features:
        - All values rounded to 2 decimal places
        - Best value per metric per row highlighted green + bold
        - Ties highlighted yellow + bold
        - Accuracy ties use a 0.02 margin of error
        - Cost values < $0.01 use scientific notation
        - Cost column shows cost * n_runs (i.e. cost across all runs)
        - Total Cost summary row at the bottom
        - Alternating row shading (light gray)
        - Column group spacing between BlendSQL and Baseline
        - Wins summary row
        - footnotesize for compact fit
        """

        df_bs = df[df['system_name'] == 'blendsql'].copy()
        if sembench_split == 'movie':
            df_bs.loc[df_bs['query_name'] == 'Q7', ['latency']] *= 2

        if df_bs.empty:
            print(f"  No BlendSQL data for {subtitle}, skipping LaTeX table.")
            return

        # BlendSQL averages per query (across runs)
        df_bs['cost'] = df_bs['latency'] * hourly_rate / 3600.0
        bs_agg = (
            df_bs.groupby('query_name')
            .agg(bs_latency=('latency', 'mean'),
                 bs_quality=('quality', 'mean'),
                 bs_cost=('cost', 'mean'))
            .reset_index()
        )

        # Baseline averages per query (across systems)
        bl_agg = (
            baseline_stats.groupby('query')
            .agg(bl_latency=('latency', 'mean'),
                 bl_quality=('quality', 'mean'),
                 bl_cost=('cost', 'mean'))
            .reset_index()
            .rename(columns={'query': 'query_name'})
        )

        merged = bs_agg.merge(bl_agg, on='query_name', how='outer').sort_values('query_name')

        # Scale costs by n_runs
        merged['bs_cost_scaled'] = merged['bs_cost'] * n_runs
        merged['bl_cost_scaled'] = merged['bl_cost'] * n_runs

        # Total costs (sum of scaled per-query costs)
        bs_total_cost = merged['bs_cost_scaled'].sum()
        bl_total_cost = merged['bl_cost_scaled'].sum()

        # ── Helpers ───────────────────────────────────────────────────────────

        def fmt(v):
            """Format a value to 2 decimal places, or '--' if missing."""
            if pd.isna(v):
                return '--'
            return f'{v:.2f}'

        def fmt_cost(v):
            """Format a cost value with a dollar sign, or '--' if missing.
            Uses scientific notation for values less than $0.01."""
            if pd.isna(v):
                return '--'
            if abs(v) < 0.01:
                s = f'{v:.0e}'  # e.g. '3e-03'
                mantissa, exp = s.split('e')
                exp_val = int(exp)  # e.g. -3
                return f'\\${mantissa}e{exp_val}'  # e.g. '$3e-3'
            return f'\\${v:.2f}'

        def highlight_green(val_str):
            """Bold + green rounded pill background via tikz."""
            return (r'\tikz[baseline=(X.base)]{'
                    r'\node[fill=bestgreen,rounded corners=3pt,'
                    r'inner xsep=3pt,inner ysep=1.5pt]'
                    r'(X){\bfseries ' + val_str + r'};}')

        def highlight_yellow(val_str):
            """Bold + yellow rounded pill background via tikz."""
            return (r'\tikz[baseline=(X.base)]{'
                    r'\node[fill=tiecolor,rounded corners=3pt,'
                    r'inner xsep=3pt,inner ysep=1.5pt]'
                    r'(X){\bfseries ' + val_str + r'};}')

        # Win counters: [bs_wins, bl_wins] per metric
        wins = {
            'latency': [0, 0],
            'quality': [0, 0],
            'cost': [0, 0],
        }

        def best_cell(bs_val, bl_val, lower_is_better=True, metric=None,
                      formatter=None, tie_margin=0.0):
            """Return (bs_str, bl_str) with the better one highlighted green+bold,
            or both highlighted yellow+bold on a tie.

            *tie_margin*: if the absolute difference between the two rounded values
            is <= this threshold, treat them as a tie.

            Tracks win counts when *metric* is provided.
            """
            _fmt = formatter or fmt
            bs_str = _fmt(bs_val)
            bl_str = _fmt(bl_val)
            bs_na = pd.isna(bs_val)
            bl_na = pd.isna(bl_val)

            if bs_na and bl_na:
                return bs_str, bl_str
            if bs_na:
                if metric:
                    wins[metric][1] += 1
                return bs_str, highlight_green(bl_str)
            if bl_na:
                if metric:
                    wins[metric][0] += 1
                return highlight_green(bs_str), bl_str

            # Compare after rounding to 2 decimals (match displayed values)
            bs_r = round(bs_val, 2)
            bl_r = round(bl_val, 2)

            if abs(bs_r - bl_r) <= tie_margin:
                # Tie — no win counted for either side
                return highlight_yellow(bs_str), highlight_yellow(bl_str)

            if lower_is_better:
                if bs_r < bl_r:
                    if metric:
                        wins[metric][0] += 1
                    return highlight_green(bs_str), bl_str
                else:
                    if metric:
                        wins[metric][1] += 1
                    return bs_str, highlight_green(bl_str)
            else:
                if bs_r > bl_r:
                    if metric:
                        wins[metric][0] += 1
                    return highlight_green(bs_str), bl_str
                else:
                    if metric:
                        wins[metric][1] += 1
                    return bs_str, highlight_green(bl_str)

        # ── Build LaTeX ───────────────────────────────────────────────────────
        lines = []
        lines.append(r'\begin{table}[htbp]')
        lines.append(r'\centering')
        lines.append(r'\footnotesize')
        lines.append(rf'\caption{{BlendSQL vs.\ closed models on {sembench_split} subset (' + subtitle.replace('_',
                                                                                                               '/_') + r')}')
        lines.append(r'\label{tab:blendsql_vs_baseline_' + subtitle.replace(' ', '_').lower() + r'}')
        lines.append(r'\begin{tabular}{l rrr | rrr}')
        lines.append(r'\toprule')
        lines.append(
            r' & \multicolumn{3}{c|}{\textbf{BlendSQL}}'
            r' & \multicolumn{3}{c}{\textbf{Baseline Avg.}} \\'
        )
        lines.append(r'\cmidrule(lr){2-4} \cmidrule(l){5-7}')
        lines.append(
            r'\textbf{Query}'
            rf' & \textbf{{Lat.\,(s)}}'
            rf' & \textbf{{Acc.}}'
            rf' & \textbf{{Cost\,({n_runs}\,runs)}}'
            rf' & \textbf{{Lat.\,(s)}}'
            rf' & \textbf{{Acc.}}'
            rf' & \textbf{{Cost\,({n_runs}\,runs)}} \\'
        )
        lines.append(r'\midrule')

        # Natural sort by query number, then suffix
        sorted_merged = merged.sort_values(
            by='query_name',
            key=lambda col: col.str.extract(r'(\d+)', expand=False).astype(float)
        )

        for row_idx, (_, row) in enumerate(sorted_merged.iterrows()):
            qname = row['query_name']
            # Alternating row shading
            if row_idx % 2 == 1:
                lines.append(r'\rowcolor{rowgray}')
            bs_lat, bl_lat = best_cell(row.get('bs_latency'), row.get('bl_latency'),
                                       lower_is_better=True, metric='latency')
            bs_qual, bl_qual = best_cell(row.get('bs_quality'), row.get('bl_quality'),
                                         lower_is_better=False, metric='quality',
                                         tie_margin=0.02)
            bs_cost, bl_cost = best_cell(row.get('bs_cost_scaled'), row.get('bl_cost_scaled'),
                                         lower_is_better=True, metric='cost',
                                         formatter=fmt_cost)
            lines.append(
                f'{qname} & {bs_lat} & {bs_qual} & {bs_cost}'
                f' & {bl_lat} & {bl_qual} & {bl_cost} \\\\'
            )

        # ── Averages row ──────────────────────────────────────────────────────
        def safe_mean(series):
            s = series.dropna()
            return s.mean() if len(s) > 0 else float('nan')

        avg_bs_lat_v = safe_mean(merged['bs_latency'])
        avg_bs_qual_v = safe_mean(merged['bs_quality'])
        avg_bs_cost_scaled_v = safe_mean(merged['bs_cost_scaled'])
        avg_bl_lat_v = safe_mean(merged['bl_latency'])
        avg_bl_qual_v = safe_mean(merged['bl_quality'])
        avg_bl_cost_scaled_v = safe_mean(merged['bl_cost_scaled'])

        # Don't count avg row in wins — pass metric=None
        a_bs_lat, a_bl_lat = best_cell(avg_bs_lat_v, avg_bl_lat_v, lower_is_better=True)
        a_bs_qual, a_bl_qual = best_cell(avg_bs_qual_v, avg_bl_qual_v, lower_is_better=False,
                                         tie_margin=0.02)
        a_bs_cost, a_bl_cost = best_cell(avg_bs_cost_scaled_v, avg_bl_cost_scaled_v,
                                         lower_is_better=True, formatter=fmt_cost)

        lines.append(r'\midrule')
        lines.append(
            f'\\textbf{{Avg.}} & {a_bs_lat} & {a_bs_qual} & {a_bs_cost}'
            f' & {a_bl_lat} & {a_bl_qual} & {a_bl_cost} \\\\'
        )

        # ── Wins summary row ──────────────────────────────────────────────────
        bs_lat_w, bl_lat_w = wins['latency']
        bs_qual_w, bl_qual_w = wins['quality']
        bs_cost_w, bl_cost_w = wins['cost']

        lines.append(
            f'\\textbf{{Wins}}'
            f' & {bs_lat_w} & {bs_qual_w} & {bs_cost_w}'
            f' & {bl_lat_w} & {bl_qual_w} & {bl_cost_w} \\\\'
        )

        # ── Total Cost summary row ────────────────────────────────────────────
        t_bs, t_bl = best_cell(bs_total_cost, bl_total_cost,
                               lower_is_better=True, formatter=fmt_cost)
        lines.append(
            f'\\textbf{{Total Cost}} & & & {t_bs}'
            f' & & & {t_bl} \\\\'
        )

        lines.append(r'\bottomrule')
        lines.append(r'\end{tabular}')
        lines.append(r'\end{table}')

        latex_str = '\n'.join(lines)
        print(f"\nLaTeX table for {subtitle}:\n")
        print(latex_str)

        if save_path:
            save_path = Path(save_path)
            save_path.write_text(latex_str)
            print(f"\nSaved LaTeX table to {save_path}")

        return latex_str


    for subtitle, df, df_full in zip(subtitles, dfs_to_plot, dfs_full):
        full_queries = df_full['query_name'].unique()
        df_filtered_stats = stats[stats['query'].isin(full_queries)]
        latex_save_path = RESULTS_DIR / subtitle / "blendsql_vs_baseline_table.tex"
        generate_latex_table(
            df_full,
            df_filtered_stats,
            hourly_rate=LOCAL_HOURLY_RATE,
            subtitle=subtitle,
            save_path=latex_save_path,
        )