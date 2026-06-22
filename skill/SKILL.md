---
name: keep-screenshot
description: Generate fake Keep app monthly running screenshot mockups for Chinese university semester sport requirements. Use this skill whenever a user wants to generate Keep running records, fake sport screenshots, 跑步截图, Keep月视图, 运动记录截图, semester running data, or needs to produce monthly running images that meet school requirements (距离>=80km, 次数>=40次 per semester). Trigger whenever the user mentions Keep screenshots, running record images, or university sport submission.
allowed-tools: [Bash, Read, Write, Edit, Glob]
---

# Keep Screenshot Generator

Generate realistic-looking Keep app monthly running record screenshots for university semester sport requirement submissions.

## What this skill does

Creates PNG images that look like Keep's "月" (monthly) view — complete with cumulative distance chart, run list, stats bar, and a real iPhone-style status bar extracted from actual Keep screenshots.

The generator lives at:
```
/Users/yangyuheng/Project/keep_screenshot/generate_keep.py   # single-month generator
/Users/yangyuheng/Project/keep_screenshot/batch_generate.py  # semester batch generator
```

Assets required (already present in the project):
```
/Users/yangyuheng/Project/keep_screenshot/statusbar_base.png  # real iPhone status bar strip
```

---

## Workflow

### Step 1 — Gather requirements

Ask the user these questions **all at once** in a single message (don't ask one by one):

1. **Date range** — Which year/month to start, which year/month to end?
2. **Semester structure** — How are the semesters divided? (default: autumn = Sep–Feb, spring = Mar–Aug)
3. **Requirements per semester** — Distance (default 80 km) and run count (default 40 times)?
4. **Current time** — What time should the status bar show? (default: use `date +"%H:%M"` to get current time)

If the user's school uses a different semester structure (e.g. the last semester is cut short and only 3–6 months count), note this carefully — the total must be met within those months only.

### Step 2 — Plan the data

Before generating, calculate and **show the user a summary table**:

| 学期 | 月份 | 目标距离 | 目标次数 |
|------|------|---------|---------|
| 2024-2025第一学期 | 2024-09 ~ 2025-02 | 82 km | 42次 |
| ... | ... | ... | ... |

Rules for distributing data across months:
- Each semester's total must **meet or slightly exceed** the requirement (add 1–3 km buffer)
- Distribute distance and run count unevenly across months — real runners don't run exactly the same amount every month
- Minimum per month: ~10 km, 6 runs (for 6-month semesters); scale up if fewer months
- For shortened semesters (e.g. only 4 months), raise the per-month floor accordingly

### Step 3 — Generate screenshots

Use `scripts/run_batch.py` (see below) or call `generate_keep.py` directly.

**Status bar time rules:**
- Start from the user's current time (or their specified time)
- Advance by +1 minute every **2–4 screenshots** (random, so it looks like manual scrolling)
- Do NOT increment by exactly 1 minute per screenshot — that looks scripted

**Total running minutes (`--total-minutes`):**
- Must be a single consistent value that increases monotonically across all months
- Start from a realistic "historical" baseline (~3000–4000 min, assuming ~1–2 years of prior Keep usage)
- Add each month's estimated run time + 20–40 min of other exercise
- Never let it decrease between months

### Step 4 — Verify and deliver

After generating, verify the semester totals meet requirements:

```python
for semester in semesters:
    assert sum(km) >= required_km
    assert sum(runs) >= required_runs
```

Tell the user:
- Where the files are saved (output directory)
- A summary table confirming each semester meets requirements
- Any caveats (e.g. battery % is fixed at 74% from the source screenshot)

---

## Calling the generator

### Single month
```bash
python3 /Users/yangyuheng/Project/keep_screenshot/generate_keep.py \
  --year 2025 \
  --month 9 \
  --distance 22.5 \      # total km this month
  --runs 12 \             # number of runs this month
  --time 17:43 \          # status bar time
  --total-minutes 4500 \  # cumulative Keep activity minutes
  --seed 42 \             # optional: fix randomness for reproducibility
  --output /path/to/out.png
```

### Batch (use the script in this skill)
See `scripts/run_batch.py` — it handles planning, time progression, and verification automatically. Run it from the project directory:

```bash
cd /Users/yangyuheng/Project/keep_screenshot
python3 ~/.claude/skills/keep-screenshot/scripts/run_batch.py \
  --start 2024-09 \
  --end 2026-06 \
  --semesters '{"2024-2025-1": {"months": ["2024-09","2024-10","2024-11","2024-12","2025-01","2025-02"], "km": 82, "runs": 42}, ...}' \
  --start-time 17:43 \
  --output-dir output/
```

Or just call `generate_keep.py` in a loop and handle the logic inline — both approaches work.

---

## Key constraints to preserve

- **`statusbar_base.png` must exist** — it contains the real iPhone status bar strip (signal/wifi/battery icons extracted from an actual Keep screenshot). If it's missing, the status bar will fall back to a hand-drawn version which looks noticeably fake.
- **Battery percentage is fixed at 74%** — this is baked into the extracted status bar image and cannot be changed without re-extracting from a different source screenshot.
- **Font path is macOS-specific** — `generate_keep.py` uses PingFang and San Francisco fonts from `/System/Library/`. On other platforms, it falls back to STHeiti.
- **Output size is 390×844 px** — matching a typical iPhone @1x logical resolution screenshot.
