#!/usr/bin/env python3
"""
Create a stacked bar chart from one or more profile_summary.dat files.

Each input file has the format:
    # Bucket                Walltime
    RHS                    42.6000
    Sync and Comms         28.8727
    Analysis               16.4770
    Other                  60.0273

The script normalizes each bar to 100% and stacks the categories.
"""

import argparse
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

# Consistent category order and colors
CATEGORY_ORDER = ["RHS", "Sync and Comms", "Analysis", "Other"]
CATEGORY_COLORS = {
    "RHS": "#2196F3",           # Blue
    "Sync and Comms": "#FF9800", # Orange
    "Analysis": "#4CAF50",      # Green
    "Other": "#9E9E9E",         # Grey
}


def parse_profile_file(filepath):
    """
    Parse a profile_summary.dat file.

    Returns a dict of {bucket_name: walltime}.
    """
    buckets = {}
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Format: "BucketName    walltime"
            match = re.match(r"^(.+?)\s+([\d.]+)$", line)
            if match:
                name = match.group(1).strip()
                walltime = float(match.group(2))
                buckets[name] = walltime
    return buckets


def fix_code_name(name):
    """Fix capitalization of known code names."""
    replacements = {
        "mhduet": "MHDuet",
        "grteclyn": "GRTeclyn",
        "etk": "ETK",
        "bam": "BAM",
    }
    return replacements.get(name.lower(), name.capitalize())


def fix_system_name(name):
    """Fix capitalization of known system names."""
    replacements = {
        "cosma8": "COSMA-8",
        "tursa": "Tursa",
    }
    return replacements.get(name.lower(), name.upper())


def label_from_filepath(filepath):
    """
    Extract a short label from the filename (code + system, no job size).

    E.g. "mhduet_cosma8_n128c4_profile_summary.dat" -> "MHDuet COSMA-8"
    E.g. "grteclyn_tursa_N4g4_profile_summary.dat" -> "GRTeclyn Tursa"
    """
    stem = Path(filepath).stem  # "mhduet_cosma8_n128c4_profile_summary"
    # Remove trailing "_profile_summary"
    name = stem.replace("_profile_summary", "")
    # Split on underscores: [code, system, job_size, ...]
    parts = name.split("_")
    # Only use code and system (first two parts), drop job size
    if len(parts) >= 2:
        code = fix_code_name(parts[0])
        system = fix_system_name(parts[1])
        return f"{code} {system}"
    return fix_code_name(parts[0]) if parts else "Unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Create a stacked bar chart from profile_summary.dat files."
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=str,
        help="One or more profile_summary.dat files",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="profile_comparison.png",
        help="Output image file (default: profile_comparison.png)",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Image DPI (default: 300)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="Profile Comparison",
        help="Chart title (default: 'Profile Comparison')",
    )
    args = parser.parse_args()

    # Parse all input files
    data = []  # list of (label, buckets_dict)
    for fpath in args.files:
        if not Path(fpath).exists():
            print(f"Warning: {fpath} not found, skipping.")
            continue
        buckets = parse_profile_file(fpath)
        if not buckets:
            print(f"Warning: {fpath} has no data, skipping.")
            continue
        label = label_from_filepath(fpath)
        data.append((label, buckets))

    if not data:
        print("Error: no valid input files.")
        sys.exit(1)

    # Handle duplicate labels (e.g., same code+system appearing twice)
    labels = []
    seen = {}
    for label, _ in data:
        if label in seen:
            seen[label] += 1
            labels.append(f"{label} ({seen[label]})")
        else:
            seen[label] = 0
            labels.append(label)

    # Collect all categories that appear in any file
    all_categories = set()
    for _, buckets in data:
        all_categories.update(buckets.keys())

    # Order categories: use CATEGORY_ORDER for known ones, append unknowns
    ordered_categories = [c for c in CATEGORY_ORDER if c in all_categories]
    for c in sorted(all_categories):
        if c not in ordered_categories:
            ordered_categories.append(c)

    # Normalize each bar to 100%
    category_data = {cat: [] for cat in ordered_categories}

    for label, buckets in data:
        total = sum(buckets.values())
        if total == 0:
            total = 1.0  # Avoid division by zero
        for cat in ordered_categories:
            pct = 100.0 * buckets.get(cat, 0.0) / total
            category_data[cat].append(pct)

    # Create stacked bar chart
    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 1.5), 6))

    bottom = [0.0] * len(labels)
    for cat in ordered_categories:
        color = CATEGORY_COLORS.get(cat, "#9E9E9E")
        ax.bar(
            labels,
            category_data[cat],
            bottom=bottom,
            label=cat,
            color=color,
            edgecolor="white",
            linewidth=0.5,
        )
        # Add percentage labels inside bars if they're large enough
        for i, pct in enumerate(category_data[cat]):
            if pct > 5.0:  # Only label if > 5% to avoid crowding
                ax.text(
                    i,
                    bottom[i] + pct / 2.0,
                    f"{pct:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=9,
                    color="white" if pct > 20 else "black",
                    fontweight="bold",
                )
        bottom = [b + p for b, p in zip(bottom, category_data[cat])]

    # Rotate x-axis labels vertically to prevent overlap
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=90, ha="right", fontsize=10)

    ax.set_ylabel("Walltime (%)", fontsize=12)
    ax.set_ylim(0, 105)
    ax.set_title(args.title, fontsize=14, fontweight="bold")
    ax.legend(
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        fontsize=10,
        framealpha=0.9,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
    print(f"Chart saved to {args.output}")


if __name__ == "__main__":
    main()
