#!/usr/bin/env python3
"""
Parse ETK Tursa timer output files and produce a profile summary.

Reads .out files from 3 runs of a given job size, extracts walltimes
for selected timers from the last timer table in each file, buckets
them, and writes an averaged summary.
"""
import argparse
import re
from pathlib import Path

# Bucket assignments: pattern -> bucket
# Each entry is (match_function, bucket_name)
BUCKET_PATTERNS = [
    # Sync and Comms
    (lambda name: name == "Sync", "Sync and Comms"),
    (lambda name: name == "Restrict", "Sync and Comms"),
    # RHS
    (lambda name: name == "ODESolvers::Solve::rhs", "RHS"),
    (lambda name: "Z4c::Z4c_Enforce" in name, "RHS"),
    # Analysis
    (lambda name: "PunctureTracker_Track" in name, "Analysis"),
    (lambda name: "Z4c::Z4c_ADM" in name, "Analysis"),
]

# Base directory for ETK Tursa submit outputs
BASE_DIR = Path(__file__).parents[1] / "codes" / "ETK" / "Tursa" / "submit"


def is_separator(line):
    """Check if a line is a table separator (long run of equals signs)."""
    stripped = line.strip()
    return len(stripped) >= 60 and all(c == "=" for c in stripped)


def parse_timer_file(output_path):
    """
    Parse the last timer table from an ETK Tursa output file.

    The timer table is delimited by lines of equals signs and has columns:
        1: percent
        2: time in seconds
        3: min time
        4: max time
        5+: timer name

    We want the last table with timer data (containing "Evolve").

    Returns a dict of timer_name -> walltime (seconds).
    """
    with open(output_path) as f:
        lines = f.readlines()

    # Find all separator line indices
    sep_indices = [i for i, line in enumerate(lines) if is_separator(line)]

    if len(sep_indices) < 2:
        print(f"Warning: no timer table found in {output_path}")
        return {}

    # Timer data pattern: starts with a percentage and has time columns
    timer_data_pattern = re.compile(r"^\s*[\d.]+\s+[\d.]+\s+[\d.]+\s+[\d.]+\s+")

    # Walk through all consecutive separator pairs and collect data blocks.
    # Find the last data block containing "Evolve".
    last_evolve_block = None

    for i in range(1, len(sep_indices)):
        start = sep_indices[i - 1]
        end = sep_indices[i]

        # Collect non-empty, non-separator lines between these separators
        block_lines = []
        for j in range(start + 1, end):
            line = lines[j]
            if line.strip() and not is_separator(line):
                block_lines.append(line.strip())

        if not block_lines:
            continue

        # Check if this block has timer data (skip header lines)
        has_timer_data = False
        for line in block_lines:
            if timer_data_pattern.match(line):
                has_timer_data = True
                break

        if not has_timer_data:
            continue

        # Check if this block contains "Evolve" timer
        has_evolve = any("Evolve" in line for line in block_lines)
        if has_evolve:
            last_evolve_block = block_lines

    if last_evolve_block is None:
        print(f"Warning: no timer table with 'Evolve' found in {output_path}")
        return {}

    timers = {}
    for line in last_evolve_block:
        # Parse: percent  time  min  max  timer_name...
        # e.g. " 88.1   627.559 627.556 627.559   Evolve"
        # e.g. "  7.8    55.229  53.568  57.092   ODESolvers::Solve::rhs"
        parts = line.split()
        if len(parts) >= 5:
            try:
                # First column is percentage, second is time
                time_val = float(parts[1])
                # Timer name is everything from column 5 onwards
                timer_name = " ".join(parts[4:])
                timers[timer_name] = time_val
            except (ValueError, IndexError):
                continue

    return timers


def main():
    parser = argparse.ArgumentParser(
        description="Parse ETK Tursa timer outputs and produce a profile summary."
    )
    parser.add_argument(
        "num_nodes",
        type=int,
        help="Number of nodes, e.g. 4 (for N4g4)",
    )
    args = parser.parse_args()

    num_nodes = args.num_nodes
    job = f"N{num_nodes}g4"

    # Collect timers from 3 runs
    all_timers = []
    for run in range(1, 4):
        output_path = BASE_DIR / f"{job}_{run}.out"
        if not output_path.exists():
            print(f"Warning: {output_path} not found, skipping.")
            continue
        timers = parse_timer_file(output_path)
        all_timers.append(timers)

    if not all_timers:
        print("Error: no output files found.")
        return

    # Total evolution time from "Evolve" timer (averaged)
    evolve_times = [t.get("Evolve", 0.0) for t in all_timers]
    evolve_total = sum(evolve_times) / len(evolve_times)

    if evolve_total == 0.0:
        print("Error: 'Evolve' timer not found in any run.")
        return

    # Compute bucket totals from exclusive table (sum per run, then average across runs)
    # For each run, sum all timers matching each bucket, then average those sums across runs
    bucket_sums_per_run = {}
    for _, bucket in BUCKET_PATTERNS:
        bucket_sums_per_run[bucket] = []

    for run in all_timers:
        # For this run, compute the sum for each bucket
        run_bucket_sums = {}
        for name, time_val in run.items():
            for match_fn, bucket in BUCKET_PATTERNS:
                if match_fn(name):
                    run_bucket_sums[bucket] = run_bucket_sums.get(bucket, 0.0) + time_val
                    break  # Only count each timer once (first matching pattern)
        # Collect per-run sums for each bucket
        for bucket in bucket_sums_per_run:
            bucket_sums_per_run[bucket].append(run_bucket_sums.get(bucket, 0.0))

    # Average across runs
    buckets = {}
    for bucket, sums in bucket_sums_per_run.items():
        avg_time = sum(sums) / len(sums)
        if avg_time > 0:
            buckets[bucket] = avg_time

    # Other = total evolution time minus accounted buckets
    accounted = sum(buckets.values())
    buckets["Other"] = evolve_total - accounted

    # Write output data file
    output_path = Path(__file__).parent / f"etk_tursa_{job}_profile_summary.dat"
    with open(output_path, "w") as f:
        f.write(f"# {'Bucket':<18s}  {'Walltime':>10s}\n")
        for bucket, walltime in buckets.items():
            f.write(f"{bucket:<18s}  {walltime:>10.4f}\n")

    print(f"Profile summary written to {output_path}")
    print(f"Total evolution time (avg): {evolve_total:.4f} s")
    for bucket, walltime in buckets.items():
        pct = 100.0 * walltime / evolve_total
        print(f"  {bucket:<18s} {walltime:>10.4f} s  ({pct:>5.1f}%)")


if __name__ == "__main__":
    main()
