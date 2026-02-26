#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pandas",
#   "numpy",
#   "seaborn",
#   "matplotlib",
# ]
# ///

import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional
import warnings
warnings.filterwarnings('ignore')

sns.set_palette("Spectral")
plt.rcParams['font.family'] = 'DeJavu Serif'
plt.rcParams['font.serif'] = ['Times New Roman']

# ── Config from environment ───────────────────────────────────────────────────
RESULTS_DIR = Path(os.environ["RESULTS_DIR"])


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
    if n_plots < 1 or n_plots > 4:
        raise ValueError("Must provide between 1 and 4 DataFrames")
    if len(subtitles) != n_plots:
        raise ValueError("Number of subtitles must match number of DataFrames")

    if n_plots <= 2:
        nrows, ncols = 1, n_plots
        figsize = (8 * n_plots, 5)
    else:
        nrows, ncols = 2, 2
        figsize = (16, 10)

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    plt.rc('font', size=14)

    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if hasattr(axes, 'flatten') else list(axes)

    for i in range(n_plots, len(axes)):
        axes[i].set_visible(False)

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

    for ax, df, subtitle in zip(axes[:n_plots], dfs, subtitles):
        plot_on_axis(ax, df, subtitle)

    all_handles, all_labels = [], []
    for ax in axes[:n_plots]:
        handles, labels = ax.get_legend_handles_labels()
        all_handles.extend(handles)
        all_labels.extend(labels)

    handles_labels = dict(zip(all_labels, all_handles))
    unique_labels = sorted(handles_labels.keys())
    unique_handles = [handles_labels[label] for label in unique_labels]

    for ax in axes[:n_plots]:
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

# ── Discover model result dirs ────────────────────────────────────────────────
dfs_to_plot = []
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
    subtitles.append(model_dir.name)  # use dir name as subtitle

if not dfs_to_plot:
    raise ValueError(f"No results found under {RESULTS_DIR}")

save_path = RESULTS_DIR / "performance_latency_scatter_all.pdf"
plot_performance_scatter_comparison(
    dfs_to_plot,
    subtitles,
    save_path=save_path,
)