#!/usr/bin/env python3
"""
Parse GRTeclyn timer output files and produce a profile summary.

Reads .out files from 3 runs of a given job size, extracts walltimes
for selected timers from the exclusive timer table, uses Amr::coarseTimeStep()
from the inclusive table for total time, buckets them, and writes an
averaged summary.

Works for both COSMA8 (n<MPI>c4) and Tursa (N<nodes>g4) outputs.
"""
import argparse
import re
from pathlib import Path

# Bucket assignments: pattern -> bucket
# Each entry is (match_function, bucket_name)
BUCKET_PATTERNS = [
    # RHS
    (lambda name: name == "BinaryBHLevel::specificEvalRHS()", "RHS"),
    # Sync and Comms
    (lambda name: name.startswith("FabArray::ParallelCopy"), "Sync and Comms"),
    (lambda name: name.startswith("FillBoundary"), "Sync and Comms"),
    (lambda name: name.startswith("FillPatch"), "Sync and Comms"),
    (lambda name: name == "CellQuartic::interp()", "Sync and Comms"),
    (lambda name: name == "StateData::FillBoundary(geom)", "Sync and Comms"),
    (lambda name: name == "AmrLevel::FillPatch()", "Sync and Comms"),
    (lambda name: name == "AmrLevel::storeRKCoarseData()", "Sync and Comms"),
    # Analysis
    (lambda name: name == "PunctureTracker::track", "Analysis"),
]

# Base directories for GRTeclyn submit outputs
COSMA8_DIR = Path(__file__).parents[1] / "codes" / "GRTeclyn" / "COSMA8" / "submit"
TURSA_DIR = Path(__file__).parents[1] / "codes" / "GRTeclyn" / "Tursa" / "submit"


def is_separator(line):
    """Check if a line is a table separator (long run of dashes)."""
    stripped = line.strip()
    return len(stripped) >= 60 and all(c == "-" for c in stripped)


def parse_timer_tables(output_path):
    """
    Parse the two timer tables from a GRTeclyn output file.

    There are two tables at the end of the file:
    1. Exclusive time table (columns: Name, NCalls, Excl. Min, Excl. Avg, Excl. Max, Max %)
    2. Inclusive time table (columns: Name, NCalls, Incl. Min, Incl. Avg, Incl. Max, Max %)

    Returns (exclusive_timers, inclusive_timers) dicts of timer_name -> avg_time.
    """
    with open(output_path) as f:
        lines = f.readlines()

    # Find all separator line indices
    sep_indices = [i for i, line in enumerate(lines) if is_separator(line)]

    if len(sep_indices) < 2:
        print(f"Warning: not enough tables found in {output_path}")
        return {}, {}

    # The timer tables have this structure:
    # separator
    # header line (e.g. "Name  NCalls  Excl. Min  Excl. Avg  ...")
    # separator
    # data lines...
    # separator
    #
    # We need to find header lines between separators, then get the next block.

    # Find header lines and their positions
    headers_found = {}
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

        # Check if this block is a header for a timer table
        header = block_lines[0]
        if "Excl. Avg" in header:
            headers_found["excl"] = i  # Next block (i+1) has the data
        elif "Incl. Avg" in header:
            headers_found["incl"] = i  # Next block (i+1) has the data

    # Extract data from the block following each header
    exclusive_block = []
    inclusive_block = []

    if "excl" in headers_found:
        idx = headers_found["excl"]
        if idx + 1 < len(sep_indices):
            start = sep_indices[idx]
            end = sep_indices[idx + 1]
            for j in range(start + 1, end):
                line = lines[j]
                if line.strip() and not is_separator(line):
                    exclusive_block.append(line.strip())

    if "incl" in headers_found:
        idx = headers_found["incl"]
        if idx + 1 < len(sep_indices):
            start = sep_indices[idx]
            end = sep_indices[idx + 1]
            for j in range(start + 1, end):
                line = lines[j]
                if line.strip() and not is_separator(line):
                    inclusive_block.append(line.strip())

    if not exclusive_block or not inclusive_block:
        print(f"Warning: timer tables not found in {output_path}")
        return {}, {}

    # Parse exclusive table
    exclusive_timers = {}
    for line in exclusive_block:
        # Format: "Name                    NCalls  Excl.Min  Excl.Avg  Excl.Max   Max %"
        # e.g. "BinaryBHLevel::specificEvalRHS()   4092       31.5      32.04      32.46  53.20%"
        # Split on whitespace
        parts = line.split()
        if len(parts) >= 6:
            try:
                timer_name = parts[0]
                ncalls = int(parts[1])
                excl_avg = float(parts[3])
                exclusive_timers[timer_name] = excl_avg
            except (ValueError, IndexError):
                continue

    # Parse inclusive table
    inclusive_timers = {}
    for line in inclusive_block:
        parts = line.split()
        if len(parts) >= 6:
            try:
                timer_name = parts[0]
                ncalls = int(parts[1])
                incl_avg = float(parts[3])
                inclusive_timers[timer_name] = incl_avg
            except (ValueError, IndexError):
                continue

    return exclusive_timers, inclusive_timers


def main():
    parser = argparse.ArgumentParser(
        description="Parse GRTeclyn timer outputs and produce a profile summary."
    )
    parser.add_argument(
        "job_size",
        type=str,
        help="Job size, e.g. n128c4 (COSMA8) or N4g4 (Tursa)",
    )
    args = parser.parse_args()

    job = args.job_size

    # Detect system from job name
    if job.upper().startswith("N") and "g" in job.lower():
        # Tursa format: N<num_nodes>g4
        base_dir = TURSA_DIR
        system = "tursa"
    else:
        # COSMA8 format: n<MPI>c4
        if not job.startswith("n"):
            job = f"n{job}"
        base_dir = COSMA8_DIR
        system = "cosma8"

    # Collect timers from 3 runs
    all_exclusive = []
    all_inclusive = []
    for run in range(1, 4):
        output_path = base_dir / f"{job}_{run}.out"
        if not output_path.exists():
            print(f"Warning: {output_path} not found, skipping.")
            continue
        exclusive, inclusive = parse_timer_tables(output_path)
        all_exclusive.append(exclusive)
        all_inclusive.append(inclusive)

    if not all_exclusive:
        print("Error: no output files found.")
        return

    # Total time from Amr::coarseTimeStep() in inclusive table (averaged)
    total_times = [t.get("Amr::coarseTimeStep()", 0.0) for t in all_inclusive]
    total_avg = sum(total_times) / len(total_times)

    if total_avg == 0.0:
        print("Error: 'Amr::coarseTimeStep()' timer not found in any run.")
        return

    # Compute bucket totals from exclusive table (sum per run, then average across runs)
    # For each run, sum all timers matching each bucket, then average those sums across runs
    bucket_sums_per_run = {}
    for _, bucket in BUCKET_PATTERNS:
        bucket_sums_per_run[bucket] = []

    for run in all_exclusive:
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

    # Other = total time minus accounted buckets
    accounted = sum(buckets.values())
    buckets["Other"] = total_avg - accounted

    # Write output data file
    output_path = Path(__file__).parent / f"grteclyn_{system}_{job}_profile_summary.dat"
    with open(output_path, "w") as f:
        f.write(f"# {'Bucket':<18s}  {'Walltime':>10s}\n")
        for bucket, walltime in buckets.items():
            f.write(f"{bucket:<18s}  {walltime:>10.4f}\n")

    print(f"Profile summary written to {output_path}")
    print(f"Total time (avg): {total_avg:.4f} s")
    for bucket, walltime in buckets.items():
        pct = 100.0 * walltime / total_avg
        print(f"  {bucket:<18s} {walltime:>10.4f} s  ({pct:>5.1f}%)")


if __name__ == "__main__":
    main()
