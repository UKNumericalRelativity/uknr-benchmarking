#!/usr/bin/env python3
"""
Parse BAM timer output files and produce a profile summary.

Reads timer.000 files from 3 runs of a given job size, extracts walltimes
for selected timers, buckets them, and writes an averaged summary.
"""

import argparse
import os
from pathlib import Path

# Bucket assignments: timer_name -> bucket
BUCKET_MAP = {
    "bssn_rhs": "RHS",
    "synchronize": "Sync and Comms",
    "restrict_prolong": "Sync and Comms",
    "syncparent": "Sync and Comms",
    "analyze_level": "Analysis",
}

# Base directory for BAM outputs
BASE_DIR = Path(__file__).parents[1] / "codes" / "BAM" / "COSMA8" / "outputs"


def parse_timer_file(timer_path):
    """
    Parse the bottom section of a BAM timer file.

    The bottom section contains summary timers with lines starting with a
    timer name (not a number).  Columns are:
        1: timer name
        2: inclusive percentage
        3: total walltime
        4: number of calls

    Returns a dict of timer_name -> walltime (taking the last occurrence
    of each timer, which has the most inclusive time).
    """
    timers = {}
    with open(timer_path) as f:
        lines = f.readlines()

    # Find the start of the bottom section — lines that start with a
    # timer name (not a digit) and have a numeric second column
    # (the inclusive percentage).  This distinguishes summary lines
    # from "Timers after top level iteration ..." headers.
    in_bottom = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped[0].isalpha():
            parts = stripped.split()
            # Bottom-section lines have: name  percentage  walltime  calls
            # The percentage (parts[1]) should be a float.
            if len(parts) >= 4:
                try:
                    float(parts[1])
                    in_bottom = True
                except ValueError:
                    continue
        if in_bottom:
            parts = stripped.split()
            if len(parts) >= 4:
                name = parts[0]
                walltime = float(parts[2])
                timers[name] = walltime  # last occurrence wins

    return timers


def main():
    parser = argparse.ArgumentParser(
        description="Parse BAM timer outputs and produce a profile summary."
    )
    parser.add_argument(
        "job_size",
        type=int,
        help="Job size (grid resolution), e.g. 512",
    )
    args = parser.parse_args()

    n = args.job_size
    run_dirs = BASE_DIR / f"n{n}"

    # Collect timers from 3 runs
    all_timers = []
    for run in range(1, 4):
        timer_path = run_dirs / str(run) / "timer.000"
        if not timer_path.exists():
            print(f"Warning: {timer_path} not found, skipping run {run}")
            continue
        timers = parse_timer_file(timer_path)
        all_timers.append(timers)

    if not all_timers:
        print("Error: no timer files found.")
        return

    # Total evolution time from evolve_grid_iteration (averaged)
    evolve_times = [t["evolve_grid_iteration"] for t in all_timers]
    evolve_total = sum(evolve_times) / len(evolve_times)

    # Compute bucket totals (averaged over runs)
    buckets = {}
    for timer_name, bucket in BUCKET_MAP.items():
        bucket_times = [run.get(timer_name, 0.0) for run in all_timers]
        avg_time = sum(bucket_times) / len(bucket_times)
        buckets[bucket] = buckets.get(bucket, 0.0) + avg_time

    # Other = total evolution time minus accounted buckets
    accounted = sum(buckets.values())
    buckets["Other"] = evolve_total - accounted

    # Write output data file
    output_path = Path(__file__).parent / f"bam_cosma8_n{n}_profile_summary.dat"
    with open(output_path, "w") as f:
        f.write(f"# {'Bucket':<18s}  {'Walltime':>10s}\n")
        for bucket, walltime in buckets.items():
            f.write(f"{bucket:<18s}  {walltime:10.4f}\n")

    print(f"Profile summary written to {output_path}")
    print(f"Total evolution time (avg): {evolve_total:.4f} s")
    for bucket, walltime in buckets.items():
        pct = 100.0 * walltime / evolve_total
        print(f"  {bucket}: {walltime:.4f} s ({pct:.1f}%)")


if __name__ == "__main__":
    main()
