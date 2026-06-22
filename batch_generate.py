#!/usr/bin/env python3
"""批量生成 Keep 月视图示例截图，覆盖 2024-09 到 2026-06 共 22 个月"""

import os
import random
import subprocess

random.seed(2024)

# ── 学期规划 ─────────────────────────────────────────────────────
# 每学期 80km / 40次，按月随机分配，月份间有自然波动
# 学期4只有4个月（3~6月），同样要达标

def alloc_semester(months, total_km, total_runs):
    """把学期目标分配到各月，返回 {(year,month): (km, runs)}"""
    n = len(months)
    # 距离：保底每月 10km，剩余随机权重分配
    min_km = 10.0
    extra_km = total_km - min_km * n
    w_km = [random.uniform(0.6, 1.4) for _ in range(n)]
    s = sum(w_km)
    kms = [round(min_km + w / s * extra_km, 2) for w in w_km]
    diff = round(total_km - sum(kms), 2)
    kms[-1] = round(kms[-1] + diff, 2)

    # 次数：保底每月 6次，剩余随机整数分配
    min_runs = 6
    extra_runs = total_runs - min_runs * n
    weights = [random.random() for _ in range(n)]
    ws = sum(weights)
    runs_list = [min_runs + int(w / ws * extra_runs) for w in weights]
    # 补足因取整丢失的次数
    while sum(runs_list) < total_runs:
        runs_list[random.randint(0, n-1)] += 1
    while sum(runs_list) > total_runs:
        i = random.randint(0, n-1)
        if runs_list[i] > min_runs:
            runs_list[i] -= 1

    return {months[i]: (kms[i], runs_list[i]) for i in range(n)}


semesters = [
    # (学期名, [(year, month), ...], km目标, 次数目标)
    ("2024-2025第一学期",
     [(2024,9),(2024,10),(2024,11),(2024,12),(2025,1),(2025,2)],
     82.0, 42),
    ("2024-2025第二学期",
     [(2025,3),(2025,4),(2025,5),(2025,6),(2025,7),(2025,8)],
     83.0, 41),
    ("2025-2026第一学期",
     [(2025,9),(2025,10),(2025,11),(2025,12),(2026,1),(2026,2)],
     81.5, 43),
    ("2025-2026第二学期(只计3-6月)",
     [(2026,3),(2026,4),(2026,5),(2026,6)],
     80.5, 40),
]

plan = {}
for name, months, km, runs in semesters:
    plan.update(alloc_semester(months, km, runs))

# ── 时间 & 总运动分钟累计 ────────────────────────────────────────
# 截图时间：从当前时刻 17:43 开始，每隔 2~4 张随机+1分钟
# 总运动分钟：历史累计，从一个合理初值开始每月累加当月跑步时长

start_h, start_m = 17, 43
cumulative_minutes = 3480

all_months = sorted(plan.keys())

# 预先生成每张截图的时间，每隔 2~4 张+1分钟
rng_time = random.Random(999)  # 独立种子，不影响距离分配
time_list = []
cur_h, cur_m = start_h, start_m
skip_counter = 0
next_skip = rng_time.randint(2, 4)
for i in range(len(all_months)):
    time_list.append(f"{cur_h:02d}:{cur_m:02d}")
    skip_counter += 1
    if skip_counter >= next_skip:
        cur_m += 1
        if cur_m >= 60:
            cur_m = 0
            cur_h += 1
        skip_counter = 0
        next_skip = rng_time.randint(2, 4)

print("=== 生成计划 ===")
for i, ym in enumerate(all_months):
    km, runs = plan[ym]
    run_min = int(km * 5.5)
    print(f"  {ym[0]}-{ym[1]:02d}  {km:.2f}km  {runs}次  ~{run_min}min  时间{time_list[i]}")

print()

out_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out_dir, exist_ok=True)

for i, ym in enumerate(all_months):
    year, month = ym
    km, runs = plan[ym]

    time_str = time_list[i]

    # 累计总运动分钟
    run_min = int(km * 5.5)
    other_min = random.randint(20, 45)
    cumulative_minutes += run_min + other_min

    out_file = os.path.join(out_dir, f"{year}-{month:02d}.png")
    seed = 2024 * 100 + i

    cmd = [
        "python3", "generate_keep.py",
        "--year", str(year),
        "--month", str(month),
        "--distance", str(km),
        "--runs", str(runs),
        "--time", time_str,
        "--total-minutes", str(cumulative_minutes),
        "--seed", str(seed),
        "--output", out_file,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✓ {year}-{month:02d}  {km:.2f}km  {runs}次  时间{time_str}  累计{cumulative_minutes}min")
    else:
        print(f"✗ {year}-{month:02d} 失败:", result.stderr.strip())

print("\n全部完成，文件在 output/ 目录")
