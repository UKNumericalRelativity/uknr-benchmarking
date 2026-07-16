#!/usr/bin/env python3
"""Plot strong scaling for the benchmarking codes."""

from __future__ import annotations

import argparse
import glob
import re
from pathlib import Path
from typing import Callable, Dict, List, Sequence

import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator, PercentFormatter


REPO_ROOT = Path(__file__).resolve().parent.parent
TRIES = range(1, 4)


def extract_bam_time(timer_path: Path) -> float:
    """Extract the BAM evolve_grid_iteration time from the timer tail."""
    with timer_path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    tail = lines[-10:] if len(lines) >= 10 else lines
    for line in reversed(tail):
        if "evolve_grid_iteration" in line:
            parts = re.split(r"\s+", line.strip())
            if len(parts) < 3:
                raise ValueError(
                    f"Unexpected format in {timer_path}: '{line.strip()}'"
                )
            try:
                return float(parts[2])
            except ValueError as exc:
                raise ValueError(
                    f"Non-numeric time in {timer_path}: '{line.strip()}'"
                ) from exc

    raise ValueError(
        f"Missing evolve_grid_iteration line near end of {timer_path}"
    )


def extract_mhduet_time(stdout_path: Path) -> float:
    """Extract the MHDuet time from the second AmrCoreProblem::Evolve() line."""
    needle = "AmrCoreProblem::Evolve()"
    with stdout_path.open("r", encoding="utf-8") as handle:
        occurrence = 0
        for line in handle:
            if needle in line:
                occurrence += 1
                if occurrence == 2:
                    parts = re.split(r"\s+", line.strip())
                    if len(parts) < 4:
                        raise ValueError(
                            f"Unexpected format in {stdout_path}: '{line.strip()}'"
                        )
                    try:
                        return float(parts[3])
                    except ValueError as exc:
                        raise ValueError(
                            f"Non-numeric time in {stdout_path}: '{line.strip()}'"
                        ) from exc

    raise ValueError(f"Missing second {needle} line in {stdout_path}")


def extract_grteclyn_time(stdout_path: Path) -> float:
    """Extract the GRTeclyn time from the [STEP 1] Coarse TimeStep line."""
    pattern = re.compile(r"^\[STEP 1\] Coarse TimeStep time:\s+([0-9.eE+-]+)")
    with stdout_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            match = pattern.match(line.strip())
            if match:
                return float(match.group(1))

    raise ValueError(
        f"Missing [STEP 1] Coarse TimeStep time line in {stdout_path}"
    )


def extract_etk_time(stdout_path: Path) -> float:
    """Extract the ETK time from the trailing main/Evolve timer line."""
    with stdout_path.open("r", encoding="utf-8") as handle:
        lines = handle.readlines()

    tail = lines[-200:] if len(lines) >= 200 else lines
    for line in reversed(tail):
        if line.rstrip().endswith("Evolve"):
            parts = re.split(r"\s+", line.strip())
            if len(parts) < 2:
                raise ValueError(
                    f"Unexpected format in {stdout_path}: '{line.strip()}'"
                )
            try:
                return float(parts[1])
            except ValueError as exc:
                raise ValueError(
                    f"Non-numeric time in {stdout_path}: '{line.strip()}'"
                ) from exc

    raise ValueError(
        f"Missing trailing Evolve timer line in the last 200 lines of {stdout_path}"
    )


def collect_bam_times(base_dir: Path, runs: Sequence[int]) -> Dict[int, List[float]]:
    """Collect BAM times per core count across tries."""
    times: Dict[int, List[float]] = {}
    for cores in runs:
        per_run: List[float] = []
        for trial in TRIES:
            pattern = base_dir / f"n{cores}" / str(trial) / "timer.0*"
            matches = sorted(Path(path) for path in glob.glob(str(pattern)))
            if not matches:
                raise FileNotFoundError(
                    f"No timer files found for {cores} cores, try {trial}"
                )
            per_run.append(extract_bam_time(matches[0]))
        times[cores] = per_run
    return times


def collect_pattern_times(
    base_dir: Path,
    runs: Sequence[int],
    multiplier: int,
    pattern: str,
    extractor: Callable[[Path], float],
) -> Dict[int, List[float]]:
    """Collect times for stdout-backed codes across tries."""
    times: Dict[int, List[float]] = {}
    for run_value in runs:
        per_run: List[float] = []
        for trial in TRIES:
            stdout_path = base_dir / pattern.format(value=run_value, trial=trial)
            if not stdout_path.exists():
                raise FileNotFoundError(f"Missing stdout file: {stdout_path}")
            per_run.append(extractor(stdout_path))
        times[run_value * multiplier] = per_run
    return times


def mean(values: Sequence[float]) -> float:
    if not values:
        raise ValueError("Cannot compute mean of empty list")
    return sum(values) / len(values)


def compute_scaling_line(x_values: Sequence[int], base_time: float) -> List[float]:
    """Ideal strong scaling halves time when resources double."""
    baseline = x_values[0]
    return [base_time * (baseline / value) for value in x_values]


CODE_CONFIGS: Dict[str, Dict[str, object]] = {
    "BAM": {
        "systems": {
            "COSMA8": {
                "x_label": "Number of COSMA8 cores",
                "resources_per_node": 128,
                "evolution_time": 0.107421875,
                "collector": lambda: collect_bam_times(
                    REPO_ROOT / "codes" / "BAM" / "COSMA8" / "outputs",
                    [128, 256, 512, 1024, 2048],
                ),
            }
        },
    },
    "MHDuet": {
        "systems": {
            "COSMA8": {
                "x_label": "Number of COSMA8 cores",
                "resources_per_node": 128,
                "evolution_time": 1.6,
                "collector": lambda: collect_pattern_times(
                    REPO_ROOT / "codes" / "MHDuet" / "COSMA8" / "submit",
                    [32, 64, 128, 256, 512, 1024],
                    4,
                    "n{value}c4_{trial}.out",
                    extract_mhduet_time,
                ),
            },
            "Tursa": {
                "x_label": "Number of GPUs",
                "resources_per_node": 4,
                "evolution_time": 1.6,
                "collector": lambda: collect_pattern_times(
                    REPO_ROOT / "codes" / "MHDuet" / "Tursa" / "submit",
                    [1, 2, 4, 8, 16, 32],
                    4,
                    "N{value}g4_{trial}.out",
                    extract_mhduet_time,
                ),
            },
        },
    },
    "GRTeclyn": {
        "systems": {
            "COSMA8": {
                "x_label": "Number of COSMA8 cores",
                "resources_per_node": 128,
                "evolution_time": 0.8,
                "collector": lambda: collect_pattern_times(
                    REPO_ROOT / "codes" / "GRTeclyn" / "COSMA8" / "submit",
                    [32, 64, 128, 256, 512, 1024],
                    4,
                    "n{value}c4_{trial}.out",
                    extract_grteclyn_time,
                ),
            },
            "Tursa": {
                "x_label": "Number of GPUs",
                "resources_per_node": 4,
                "evolution_time": 0.8,
                "collector": lambda: collect_pattern_times(
                    REPO_ROOT / "codes" / "GRTeclyn" / "Tursa" / "submit",
                    [1, 2, 4, 8, 16, 32],
                    4,
                    "N{value}g4_{trial}.out",
                    extract_grteclyn_time,
                ),
            },
        },
    },
    "ETK": {
        "systems": {
            "COSMA8": {
                "x_label": "Number of COSMA8 cores",
                "resources_per_node": 128,
                "evolution_time": 0.4,
                "collector": lambda: collect_pattern_times(
                    REPO_ROOT / "codes" / "ETK" / "COSMA8" / "submit",
                    [32, 64, 128, 256, 512, 1024],
                    4,
                    "n{value}c4_{trial}.out",
                    extract_etk_time,
                ),
            },
            "Tursa": {
                "x_label": "Number of GPUs",
                "resources_per_node": 4,
                "evolution_time": 256 / 288,
                "collector": lambda: collect_pattern_times(
                    REPO_ROOT / "codes" / "ETK" / "Tursa" / "submit",
                    [1, 2, 4, 8, 16, 32],
                    4,
                    "N{value}g4_{trial}.out",
                    extract_etk_time,
                ),
            },
        },
    },
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot strong scaling for the benchmarking codes."
    )
    parser.add_argument(
        "--code",
        required=True,
        choices=sorted(CODE_CONFIGS.keys()),
        help="Code name: BAM, ETK, GRTeclyn, or MHDuet.",
    )
    parser.add_argument(
        "--system",
        required=True,
        help="System name, e.g. COSMA8 or Tursa, or combined for both systems.",
    )
    parser.add_argument(
        "--alignment-multiplier",
        type=float,
        default=1.0,
        help=(
            "Multiply COSMA8 node counts in combined plots to align the "
            "horizontal axis with Tursa (default: 1)."
        ),
    )
    parser.add_argument(
        "--scale",
        choices=["normalized", "actual"],
        default="normalized",
        help=(
            "Plot walltime per unit of evolution time or actual walltime "
            "in seconds."
        ),
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save the figure to the code directory.",
    )
    parser.add_argument(
        "--format",
        choices=["png", "pdf", "svg"],
        default="png",
        help="File format to use when saving figures.",
    )
    args = parser.parse_args(argv)

    valid_systems = sorted(CODE_CONFIGS[args.code]["systems"].keys())
    allowed_systems = valid_systems + (
        ["combined"] if len(valid_systems) > 1 else []
    )
    if args.system not in allowed_systems:
        parser.error(
            f"system must be one of {', '.join(allowed_systems)} "
            f"for code {args.code}"
        )
    if args.alignment_multiplier <= 0:
        parser.error("alignment-multiplier must be greater than zero")

    return args


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    systems = CODE_CONFIGS[args.code]["systems"]

    if args.system == "combined":
        selected_systems = list(systems.items())
        x_label = (
            "Number of nodes"
            if args.alignment_multiplier == 1
            else "Number of resources"
        )
    else:
        selected_systems = [(args.system, systems[args.system])]
        x_label = systems[args.system]["x_label"]

    fig, ax_left = plt.subplots(figsize=(7, 5))
    ax_right = ax_left.twinx()
    node_ticks: set[float] = set()

    colours = {
        "COSMA8": "tab:blue",
        "Tursa": "tab:red",
    }

    for system_name, system_config in selected_systems:
        times_by_resource = system_config["collector"]()
        resources = sorted(times_by_resource.keys())
        mean_times = [mean(times_by_resource[value]) for value in resources]
        baseline = mean_times[0]

        if args.system == "combined":
            x_values = [
                (
                    value / system_config["resources_per_node"]
                    * (args.alignment_multiplier if system_name == "COSMA8" else 1)
                )
                for value in resources
            ]
            node_ticks.update(x_values)
        else:
            x_values = resources

        if args.scale == "normalized":
            evolution_time = float(system_config["evolution_time"])
            plot_times = [time / evolution_time for time in mean_times]
            ideal_times = compute_scaling_line(x_values, plot_times[0])
            y_label = "Walltime per unit evolution time (s/M)"
        else:
            plot_times = mean_times
            ideal_times = compute_scaling_line(x_values, plot_times[0])
            y_label = "Walltime (s)"

        efficiencies = [
            ideal / actual for ideal, actual in zip(ideal_times, plot_times)
        ]
        colour = colours.get(system_name, "tab:blue")
        label_prefix = f"{system_name} " if args.system == "combined" else ""

        ax_left.loglog(
            x_values,
            plot_times,
            marker="o",
            label=f"{label_prefix}measured walltime",
            color=colour,
        )
        ax_left.loglog(
            x_values,
            ideal_times,
            linestyle="--",
            label=f"{label_prefix}ideal scaling walltime",
            color=colour,
        )
        ax_right.plot(
            x_values,
            efficiencies,
            color=colour,
            marker="s",
            linestyle=":",
            label=f"{label_prefix}scaling efficiency",
        )

    if args.system == "combined":
        x_ticks = sorted(node_ticks)
    else:
        x_ticks = sorted(times_by_resource.keys())

    ax_left.set_xticks(x_ticks)
    ax_left.set_xticklabels([f"{value:g}" for value in x_ticks])
    ax_left.set_xlabel(x_label)
    ax_left.set_ylabel(y_label)
    ax_left.set_title(f"{args.code} Strong Scaling ({args.system})")
    ax_left.xaxis.set_minor_locator(NullLocator())
    ax_left.grid(True, which="major", linestyle=":", linewidth=0.6)
    ax_left.grid(True, which="minor", axis="y", linestyle=":", linewidth=0.4)

    ax_right.set_ylabel("Strong scaling efficiency (%)")
    ax_right.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))

    left_handles, left_labels = ax_left.get_legend_handles_labels()
    right_handles, right_labels = ax_right.get_legend_handles_labels()
    ax_left.legend(
        left_handles + right_handles,
        left_labels + right_labels,
        loc="best",
    )

    fig.tight_layout()
    if args.save:
        output_parts = [
            args.code.lower(),
            "strong",
            "scaling",
            args.system.lower(),
            args.scale,
        ]
        output_path = (
            REPO_ROOT
            / "codes"
            / args.code
            / ("_".join(output_parts) + f".{args.format}")
        )
        fig.savefig(output_path, dpi=300)
    else:
        plt.show()


if __name__ == "__main__":
    main()
