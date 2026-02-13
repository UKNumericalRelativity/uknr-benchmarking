#!/usr/bin/env python3
"""Plot strong scaling for BAM runs using timer outputs."""

from __future__ import annotations

import glob
import re
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator, PercentFormatter


BASE_DIR = Path(__file__).resolve().parent / "COSMA8" / "outputs"
CORES = [128, 256, 512, 1024, 2048]
TRIES = [1, 2, 3]


def extract_evolve_time(timer_path: Path) -> float:
	"""Extract the evolution time from the evolve_grid_iteration line."""
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


def collect_times() -> Dict[int, List[float]]:
	"""Collect times per core count across tries."""
	times: Dict[int, List[float]] = {}
	for cores in CORES:
		per_core: List[float] = []
		for trial in TRIES:
			pattern = BASE_DIR / f"n{cores}" / str(trial) / "timer.0*"
			matches = sorted(Path(p) for p in glob.glob(str(pattern)))
			if not matches:
				raise FileNotFoundError(
					f"No timer files found for {cores} cores, try {trial}"
				)
			per_core.append(extract_evolve_time(matches[0]))
		times[cores] = per_core
	return times


def mean(values: List[float]) -> float:
	if not values:
		raise ValueError("Cannot compute mean of empty list")
	return sum(values) / len(values)


def compute_scaling_line(cores: List[int], base_time: float) -> List[float]:
	"""Ideal strong scaling: half the time when doubling cores."""
	baseline = cores[0]
	return [base_time * (baseline / c) for c in cores]


def main() -> None:
	times_by_core = collect_times()
	mean_times = [mean(times_by_core[c]) for c in CORES]
	baseline = mean_times[0]
	mean_times = [t / baseline for t in mean_times]

	ideal_times = compute_scaling_line(CORES, 1.0)
	efficiencies = [ideal / actual for ideal, actual in zip(ideal_times, mean_times)]

	fig, ax_left = plt.subplots(figsize=(7, 5))
	ax_left.loglog(CORES, mean_times, marker="o", label="Measured")
	ax_left.loglog(CORES, ideal_times, linestyle="--", label="Ideal scaling")
	ax_left.set_xticks(CORES)
	ax_left.set_xticklabels([str(c) for c in CORES])
	ax_left.set_xlabel("Number of COSMA8 cores")
	ax_left.set_ylabel("Normalized evolution time")
	ax_left.set_title("BAM Strong Scaling")
	ax_left.xaxis.set_minor_locator(NullLocator())
	ax_left.grid(True, which="major", linestyle=":", linewidth=0.6)
	ax_left.grid(True, which="minor", axis="y", linestyle=":", linewidth=0.4)

	ax_right = ax_left.twinx()
	ax_right.plot(CORES, efficiencies, color="tab:green", marker="s", label="Efficiency")
	ax_right.set_ylabel("Strong scaling efficiency (%)")
	ax_right.yaxis.set_major_formatter(PercentFormatter(xmax=1.0))

	left_handles, left_labels = ax_left.get_legend_handles_labels()
	right_handles, right_labels = ax_right.get_legend_handles_labels()
	ax_left.legend(left_handles + right_handles, left_labels + right_labels, loc="best")

	fig.tight_layout()
	output_path = Path(__file__).resolve().parent / "bam_strong_scaling.png"
	fig.savefig(output_path, dpi=300)
	plt.show()


if __name__ == "__main__":
	main()
