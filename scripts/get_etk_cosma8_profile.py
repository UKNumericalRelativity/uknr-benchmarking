#!/usr/bin/env python3
"""
Parse ETK (Cactus) timer output files and produce a profile summary.

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
    (lambda name: "syncs" in name, "Sync and Comms"),
    (lambda name: "Restrict" in name, "Sync and Comms"),
    # Analysis
    (lambda name: name == "ML_ADMConstraints_evaluate", "Analysis"),
    (lambda name: name.startswith("ML_BSSN_ADMBase"), "Analysis"),
    (lambda name: name == "ML_BSSN_ConstraintsInterior", "Analysis"),
    (lambda name: name == "PunctureTracker_Track", "Analysis"),
    # RHS
    (lambda name: name == "ML_BSSN_EnforceEverywhere", "RHS"),
    (lambda name: name.startswith("ML_BSSN_Evolution"), "RHS"),
    (lambda name: name == "SBP_DissipationAdd", "RHS"),
]

# Base directory for ETK COSMA8 submit outputs
BASE_DIR = Path(__file__).parents[1] / "codes" / "ETK" / "COSMA8" / "submit"


def strip_timer_name(raw_name):
    """
    Strip the tree-structure prefix from a Cactus timer name.

    Timer names in the output are prefixed with combinations of '|', '_',
    and spaces to show the hierarchy, e.g. '| | | |_syncs'.
    We strip these to get the bare name, e.g. 'syncs'.

    The actual timer name starts with an alphanumeric character.
    """
    # Remove leading |, _, and spaces until we hit an alphanumeric char
    name = re.sub(r"^[|_\s]+", "", raw_name)
    # The timer name is the first word (may contain underscores within)
    # Trailing columns (cycle counts) are separated by multiple spaces
    name = re.split(r"\s{2,}", name)[0].strip()
    return name


def is_separator(line):
    """Check if a line is a table separator (long run of dashes)."""
    stripped = line.strip()
    return len(stripped) >= 60 and all(c == "-" for c in stripped)


def parse_timer_file(output_path):
    """
    Parse the last "Evolve" timer table from an ETK/Cactus output file.

    The timer table is delimited by lines of dashes and has columns:
        1: time percent
        2: time in seconds
        3: imbalance percent
        4+: timer name (may include tree prefix like '| | |_')

    There may be multiple timer tables in the file (e.g., "Evolve" and
    "meta mode").  We want the last table whose first data line is the
    "Evolve" timer (100% time).

    Returns a dict of stripped_timer_name -> walltime (seconds).
    """
    with open(output_path) as f:
        lines = f.readlines()

    # Find all separator line indices
    sep_indices = [i for i, line in enumerate(lines) if is_separator(line)]

    if len(sep_indices) < 2:
        print(f"Warning: no timer table found in {output_path}")
        return {}

    # Timer data pattern: starts with a percentage
    timer_data_pattern = re.compile(r"\d+\.?\d*%\s+[\d.]+")

    # Walk through all consecutive separator pairs and collect data blocks.
    # A data block is content between two separators where at least the
    # first non-empty line matches the timer data pattern.
    # We skip blocks that are header-only (e.g. column names).
    # Adjacent separators produce empty blocks — those are skipped.

    # Find the last data block starting with "Evolve"
    last_evolve_block = None

    for i in range(1, len(sep_indices)):
        start = sep_indices[i - 1]
        end = sep_indices[i]

        # Collect non-empty, non-separator lines between these separators
        block_lines = []
        for j in range(start + 1, end):
            stripped = lines[j].strip()
            if stripped and not is_separator(lines[j]):
                block_lines.append(stripped)

        if not block_lines:
            continue

        # Check if this block starts with timer data
        if not timer_data_pattern.match(block_lines[0]):
            continue

        # Check if the first timer is "Evolve"
        first_match = re.match(
            r"[\d.]+%\s+([\d.]+)\s+[\d.]+%?\s+(.+)", block_lines[0]
        )
        if first_match:
            first_timer = strip_timer_name(first_match.group(2).strip())
            if first_timer == "Evolve":
                last_evolve_block = block_lines

    if last_evolve_block is None:
        print(f"Warning: no 'Evolve' timer table found in {output_path}")
        return {}

    timers = {}
    for line in last_evolve_block:
        # Parse: percent  time  imbalance  timer_name...
        # e.g. " 100.0%    344.0    0.0%  Evolve"
        # e.g. "  84.7%    291.4    0.7%  |_CallEvol"
        match = re.match(
            r"[\d.]+%\s+([\d.]+)\s+[\d.]+%?\s+(.+)", line
        )
        if match:
            walltime = float(match.group(1))
            raw_name = match.group(2).strip()
            name = strip_timer_name(raw_name)
            # Sum times if same timer appears multiple times (e.g., syncs)
            timers[name] = timers.get(name, 0.0) + walltime

    return timers


def main():
    parser = argparse.ArgumentParser(
        description="Parse ETK/Cactus timer outputs and produce a profile summary."
    )
    parser.add_argument(
        "job_size",
        type=str,
        help="Job size, e.g. n128c4 (n<MPI ranks>c<OMP threads>)",
    )
    args = parser.parse_args()

    job = args.job_size
    # Ensure it starts with 'n' for consistency
    if not job.startswith("n"):
        job = f"n{job}"

    # Collect timers from 3 runs
    all_timers = []
    for run in range(1, 4):
        output_path = BASE_DIR / f"{job}_{run}.out"
        if not output_path.exists():
            print(f"Warning: {output_path} not found, skipping run {run}")
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

    # Compute bucket totals (averaged over runs)
    buckets = {}
    for match_fn, bucket in BUCKET_PATTERNS:
        bucket_times = []
        for run in all_timers:
            # Sum all timers in this run that match the pattern
            run_total = sum(
                wt for name, wt in run.items() if match_fn(name)
            )
            bucket_times.append(run_total)
        avg_time = sum(bucket_times) / len(bucket_times)
        buckets[bucket] = buckets.get(bucket, 0.0) + avg_time

    # Other = total evolution time minus accounted buckets
    accounted = sum(buckets.values())
    buckets["Other"] = evolve_total - accounted

    # Write output data file
    output_path = Path(__file__).parent / f"etk_cosma8_{job}_profile_summary.dat"
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
