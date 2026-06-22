#!/usr/bin/env python3
"""
Keep screenshot batch generator — called by the keep-screenshot skill.

Usage:
  python3 run_batch.py --config config.json

config.json format:
{
  "start_time": "17:43",
  "initial_total_minutes": 3480,
  "output_dir": "/path/to/output",
  "seed": 2024,
  "semesters": [
    {
      "name": "2024-2025第一学期",
      "months": ["2024-09", "2024-10", "2024-11", "2024-12", "2025-01", "2025-02"],
      "target_km": 82.0,
      "target_runs": 42
    }
  ]
}
"""

import argparse
import json
import os
import random
import subprocess
import sys

GENERATOR = os.path.join(
    os.path.dirname(__file__), "../../generate_keep.py"
)
# Resolve to absolute path
GENERATOR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../../generate_keep.py"
))
# Fallback to project location
if not os.path.exists(GENERATOR):
    GENERATOR = os.path.expanduser(
        "~/Project/keep_screenshot/generate_keep.py"
    )


def alloc_semester(months, total_km, total_runs, rng):
    n = len(months)
    min_km = max(8.0, total_km / n * 0.6)
    extra_km = max(0, total_km - min_km * n)
    w_km = [rng.uniform(0.6, 1.4) for _ in range(n)]
    s = sum(w_km)
    kms = [round(min_km + w / s * extra_km, 2) for w in w_km]
    diff = round(total_km - sum(kms), 2)
    kms[-1] = round(kms[-1] + diff, 2)

    min_runs = max(4, total_runs // n - 2)
    extra_runs = max(0, total_runs - min_runs * n)
    weights = [rng.random() for _ in range(n)]
    ws = sum(weights)
    runs_list = [min_runs + int(w / ws * extra_runs) for w in weights]
    while sum(runs_list) < total_runs:
        runs_list[rng.randint(0, n - 1)] += 1
    while sum(runs_list) > total_runs:
        i = rng.randint(0, n - 1)
        if runs_list[i] > min_runs:
            runs_list[i] -= 1

    return list(zip(months, kms, runs_list))


def build_time_sequence(start_time, count, rng):
    h, m = map(int, start_time.split(":"))
    times = []
    skip_counter = 0
    next_skip = rng.randint(2, 4)
    for _ in range(count):
        times.append(f"{h:02d}:{m:02d}")
        skip_counter += 1
        if skip_counter >= next_skip:
            m += 1
            if m >= 60:
                m = 0
                h += 1
            skip_counter = 0
            next_skip = rng.randint(2, 4)
    return times


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Path to config JSON")
    args = ap.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    seed = cfg.get("seed", 2024)
    rng = random.Random(seed)
    rng_time = random.Random(seed + 999)

    start_time = cfg.get("start_time", "09:00")
    cum_min = cfg.get("initial_total_minutes", 3480)
    out_dir = cfg.get("output_dir", "output")
    os.makedirs(out_dir, exist_ok=True)

    # Build full month plan
    all_entries = []  # (year, month_str, km, runs)
    for sem in cfg["semesters"]:
        entries = alloc_semester(
            sem["months"], sem["target_km"], sem["target_runs"], rng
        )
        all_entries.extend(entries)

    # Build time sequence
    times = build_time_sequence(start_time, len(all_entries), rng_time)

    # Print plan
    print("=== 生成计划 ===")
    sem_idx = 0
    month_idx = 0
    for sem in cfg["semesters"]:
        print(f"\n【{sem['name']}】目标: {sem['target_km']}km / {sem['target_runs']}次")
        for m in sem["months"]:
            _, km, runs = all_entries[month_idx]
            print(f"  {m}  {km:.2f}km  {runs}次  时间{times[month_idx]}")
            month_idx += 1

    # Verify
    print("\n=== 学期验证 ===")
    month_idx = 0
    all_ok = True
    for sem in cfg["semesters"]:
        n = len(sem["months"])
        sem_entries = all_entries[month_idx: month_idx + n]
        total_km = round(sum(e[1] for e in sem_entries), 2)
        total_runs = sum(e[2] for e in sem_entries)
        ok_km = total_km >= sem["target_km"]
        ok_runs = total_runs >= sem["target_runs"]
        status = "✓" if (ok_km and ok_runs) else "✗"
        print(f"  {status} {sem['name']}: {total_km:.2f}km {'✓' if ok_km else '✗'}  {total_runs}次 {'✓' if ok_runs else '✗'}")
        if not (ok_km and ok_runs):
            all_ok = False
        month_idx += n

    if not all_ok:
        print("\n警告: 部分学期未达标，请调整 target_km / target_runs")
        sys.exit(1)

    print("\n=== 开始生成 ===")
    for i, (month_str, km, runs) in enumerate(all_entries):
        year, month = map(int, month_str.split("-"))
        time_str = times[i]

        run_min = int(km * 5.5)
        other_min = rng.randint(20, 45)
        cum_min += run_min + other_min

        out_file = os.path.join(out_dir, f"{month_str}.png")
        img_seed = seed * 100 + i

        cmd = [
            sys.executable, GENERATOR,
            "--year", str(year),
            "--month", str(month),
            "--distance", str(km),
            "--runs", str(runs),
            "--time", time_str,
            "--total-minutes", str(cum_min),
            "--seed", str(img_seed),
            "--output", out_file,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ {month_str}  {km:.2f}km  {runs}次  {time_str}  累计{cum_min}min")
        else:
            print(f"✗ {month_str} 失败:\n{result.stderr.strip()}")

    print(f"\n全部完成，{len(all_entries)} 张截图保存在: {os.path.abspath(out_dir)}")


if __name__ == "__main__":
    main()
