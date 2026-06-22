#!/usr/bin/env python3
"""
Keep 月视图示例截图生成器
用法: python3 generate_keep.py --year 2025 --month 9 --distance 22.5 --runs 12
"""

import argparse
import calendar
import os
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

# PingFang 字体路径 (macOS)
PINGFANG_PATH = (
    "/System/Library/AssetsV2/com_apple_MobileAsset_Font8/"
    "86ba2c91f017a3749571a82f2c6d890ac7ffb2fb.asset/AssetData/PingFang.ttc"
)
SF_PATH = "/System/Library/Fonts/SFNS.ttf"          # San Francisco，iOS 状态栏字体
FALLBACK_FONT = "/System/Library/Fonts/STHeiti Medium.ttc"

# 从真实 Keep 截图里提取的状态栏右侧图标（信号+wifi+电池），放在脚本同目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STATUSBAR_ICONS_PATH = os.path.join(SCRIPT_DIR, "statusbar_icons_1x.png")
# 完整状态栏底板（右侧图标已保留，左侧时间区域已清空），用于直接贴图
STATUSBAR_BASE_PATH = os.path.join(SCRIPT_DIR, "statusbar_base.png")
# 原始 Keep 截图，用于提取状态栏图标（如 statusbar_icons_1x.png 不存在时自动生成）
STATUSBAR_SOURCE_PATH = (
    "/var/folders/ql/d9y1zl053pj53kbqrllgfn6h0000gn/T/aionui/f3989016/"
    "a4d0f0490a8c6957afbf15dec3435838.png"
)

# 配色
WHITE       = (255, 255, 255)
BLACK       = (20,  20,  20)
LIGHT_GRAY  = (248, 248, 248)
MID_GRAY    = (200, 200, 200)
GRAY        = (150, 150, 150)
DARK_GRAY   = (60,  60,  60)
GREEN       = (82,  196, 26)
GREEN_DARK  = (56,  158, 13)
GREEN_FILL  = (82,  196, 26, 45)
BORDER      = (235, 235, 235)


def font(size, bold=False):
    """加载字体，优先 PingFang"""
    index = 1 if bold else 0  # PingFang.ttc: index 0=Regular, 1=Medium
    for path in [PINGFANG_PATH, FALLBACK_FONT]:
        try:
            return ImageFont.truetype(path, size, index=index)
        except Exception:
            continue
    return ImageFont.load_default()


def sf_font(size):
    """加载 San Francisco 字体（用于状态栏时间，与 iOS 原生一致）"""
    try:
        return ImageFont.truetype(SF_PATH, size)
    except Exception:
        return font(size, bold=True)


def gen_runs(year, month, target_distance, target_runs):
    """随机生成跑步记录，使距离和次数接近目标"""
    days_in_month = calendar.monthrange(year, month)[1]
    run_count = min(target_runs, days_in_month)

    run_days = sorted(random.sample(range(1, days_in_month + 1), run_count))

    # 分配距离：每次保底 1.5km，剩余量按随机权重分配
    MIN_RUN = 1.5
    extra = max(0.0, target_distance - run_count * MIN_RUN)
    weights = [random.random() for _ in range(run_count)]
    w_sum = sum(weights)
    distances = [round(MIN_RUN + w / w_sum * extra, 2) for w in weights]
    # 修正四舍五入误差
    diff = round(target_distance - sum(distances), 2)
    distances[-1] = round(distances[-1] + diff, 2)

    runs = []
    for day, dist in zip(run_days, distances):
        pace_min = random.randint(4, 6)
        pace_sec = random.randint(0, 59)
        pace_total = pace_min * 60 + pace_sec
        total_sec = int(dist * pace_total)
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        duration = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
        runs.append({
            "day": day,
            "distance": dist,
            "pace_min": pace_min,
            "pace_sec": pace_sec,
            "pace": f"{pace_min}'{pace_sec:02d}\"",
            "duration": duration,
            "calories": int(dist * 58 + random.randint(-20, 20)),
        })
    return runs


def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)


def generate(year, month, target_distance, target_runs, time_str=None, output=None, total_minutes=None):
    W, H = 390, 844
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    runs = gen_runs(year, month, target_distance, target_runs)
    total_dist = round(sum(r["distance"] for r in runs), 2)
    total_cals = sum(r["calories"] for r in runs)
    total_count = len(runs)

    all_pace_sec = [r["pace_min"] * 60 + r["pace_sec"] for r in runs]
    avg_pace_sec = sum(all_pace_sec) // len(all_pace_sec)
    ap_m, ap_s = avg_pace_sec // 60, avg_pace_sec % 60
    avg_pace = f"{ap_m}'{ap_s:02d}\""

    total_sec = sum(int(r["distance"] * (r["pace_min"] * 60 + r["pace_sec"])) for r in runs)
    th = total_sec // 3600
    tm = (total_sec % 3600) // 60
    ts = total_sec % 60
    total_dur = f"{th:02d}:{tm:02d}:{ts:02d}"

    # 总运动（分钟）= Keep 历史累计，必须远大于本月跑步时长
    # 默认推算：假设用户从大约1~2年前开始使用，平均每月运动约180~300分钟
    this_month_min = total_sec // 60
    if total_minutes is None:
        months_active = random.randint(14, 24)
        avg_monthly = random.randint(170, 290)
        total_minutes = months_active * avg_monthly + this_month_min + random.randint(0, 50)

    if time_str is None:
        now = datetime.now()
        time_str = f"{now.hour:02d}:{now.minute:02d}"

    y = 0

    # ── 状态栏 ──────────────────────────────────────────────────
    # 贴真实底板（含右侧图标），再在左侧写时间，风格完全一致
    if os.path.exists(STATUSBAR_BASE_PATH):
        bar_img = Image.open(STATUSBAR_BASE_PATH).convert("RGB")
        img.paste(bar_img, (0, 0))
        draw = ImageDraw.Draw(img)
        draw.text((22, 23), time_str, fill=BLACK, font=sf_font(16), anchor="lm")
    elif os.path.exists(STATUSBAR_ICONS_PATH):
        draw.rectangle([0, 0, W, 46], fill=WHITE)
        draw.text((22, 23), time_str, fill=BLACK, font=font(15, bold=True), anchor="lm")
        icons_img = Image.open(STATUSBAR_ICONS_PATH).convert("RGBA")
        iw, ih = icons_img.size
        img.paste(icons_img, (W - iw, (46 - ih) // 2), icons_img)
        draw = ImageDraw.Draw(img)
    else:
        draw.rectangle([0, 0, W, 46], fill=WHITE)
        draw.text((22, 23), time_str, fill=BLACK, font=font(15, bold=True), anchor="lm")

    y = 46

    # ── 标题栏 ──────────────────────────────────────────────────
    draw.rectangle([0, y, W, y + 48], fill=WHITE)
    # 返回箭头
    draw.text((18, y + 24), "‹", fill=BLACK, font=font(26), anchor="lm")
    # 标题
    draw.text((W // 2, y + 24), "运动记录", fill=BLACK, font=font(17, bold=True), anchor="mm")
    # 右侧图标（分享 + 更多）
    draw.text((W - 44, y + 24), "⬆", fill=DARK_GRAY, font=font(15), anchor="mm")
    draw.text((W - 18, y + 24), "…", fill=DARK_GRAY, font=font(15), anchor="mm")

    y += 48

    # ── 顶部统计 Tab（滚动区域） ──────────────────────────────
    draw.rectangle([0, y, W, y + 52], fill=WHITE)
    draw.line([0, y + 51, W, y + 51], fill=BORDER, width=1)

    top_tabs = [
        ("总运动(分钟)", str(total_minutes)),
        (f"总跑步(公里)", f"{total_dist:.2f}"),
        (f"户外跑步(公里)", f"{total_dist:.2f}"),
    ]
    tw = W // 3
    for i, (lbl, val) in enumerate(top_tabs):
        tx = i * tw
        cx = tx + tw // 2
        # 选中第2个tab（总跑步）
        if i == 1:
            draw.rectangle([tx + 4, y + 4, tx + tw - 4, y + 48], outline=BLACK, width=1)
        draw.text((cx, y + 16), lbl if len(lbl) <= 8 else lbl[:6] + "…", fill=DARK_GRAY if i == 1 else GRAY,
                  font=font(10), anchor="mt")
        draw.text((cx, y + 30), val, fill=BLACK if i == 1 else GRAY,
                  font=font(13, bold=True), anchor="mt")

    y += 52

    # ── 时间维度 Tab（日/周/月/年/总）──────────────────────────
    draw.rectangle([0, y, W, y + 44], fill=WHITE)
    tabs = ["日", "周", "月", "年", "总"]
    tw2 = W // len(tabs)
    for i, t in enumerate(tabs):
        tx = i * tw2
        cx = tx + tw2 // 2
        if t == "月":
            draw_rounded_rect(draw, [tx + 5, y + 7, tx + tw2 - 5, y + 37], radius=8, fill=(240, 240, 240))
        draw.text((cx, y + 22), t, fill=BLACK if t == "月" else GRAY,
                  font=font(14, bold=(t == "月")), anchor="mm")

    y += 44
    draw.line([0, y, W, y], fill=BORDER, width=1)
    y += 1

    # ── 月份导航 ─────────────────────────────────────────────
    draw.rectangle([0, y, W, y + 46], fill=WHITE)
    draw.text((22, y + 23), "‹", fill=GRAY, font=font(20), anchor="lm")
    draw.text((W // 2, y + 23), f"{year}年{month}月 ▾", fill=BLACK, font=font(15, bold=True), anchor="mm")
    draw.text((W - 22, y + 23), "›", fill=GRAY, font=font(20), anchor="rm")

    y += 46

    # ── 距离标题 ─────────────────────────────────────────────
    draw.text((22, y + 16), "里程(公里)", fill=GRAY, font=font(12), anchor="lm")
    y += 32

    # ── 大数字 ───────────────────────────────────────────────
    draw.text((22, y + 8), f"{total_dist:.2f}", fill=BLACK, font=font(50, bold=True), anchor="lt")
    y += 66

    # ── 统计行 ───────────────────────────────────────────────
    draw.rectangle([0, y, W, y + 52], fill=WHITE)
    stats = [
        ("消耗(千卡)", str(total_cals)),
        ("平均配速", avg_pace),
        ("时长", total_dur),
        ("完成(次)", str(total_count)),
    ]
    sw = W // 4
    for i, (lbl, val) in enumerate(stats):
        cx = i * sw + sw // 2
        draw.text((cx, y + 12), lbl, fill=GRAY, font=font(10), anchor="mt")
        draw.text((cx, y + 28), val, fill=DARK_GRAY, font=font(13, bold=True), anchor="mt")

    y += 52

    # ── 折线图 ───────────────────────────────────────────────
    ch_top = y + 40          # 顶部留出足够空间给气泡提示
    ch_bottom = y + 180
    ch_left = 20
    ch_right = W - 20
    ch_w = ch_right - ch_left
    ch_h = ch_bottom - ch_top

    days_in_month = calendar.monthrange(year, month)[1]
    day_dist = {r["day"]: r["distance"] for r in runs}

    cum = []
    acc = 0.0
    for d in range(1, days_in_month + 1):
        acc += day_dist.get(d, 0)
        cum.append(acc)

    max_c = max(cum) if cum else 1

    # 网格线
    for gi in range(5):
        gy = ch_bottom - int(gi * ch_h / 4)
        draw.line([ch_left, gy, ch_right, gy], fill=(238, 238, 238), width=1)

    # 计算折线点
    pts = []
    for i, c in enumerate(cum):
        px = ch_left + int(i * ch_w / (days_in_month - 1))
        py = ch_bottom - int(c / max_c * ch_h)
        pts.append((px, py))

    # 半透明填充
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    fill_poly = list(pts) + [(pts[-1][0], ch_bottom), (pts[0][0], ch_bottom)]
    od.polygon(fill_poly, fill=GREEN_FILL)
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 折线
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=GREEN, width=2)

    # 终点气泡
    ex, ey = pts[-1]
    draw.ellipse([ex - 5, ey - 5, ex + 5, ey + 5], fill=GREEN)
    tip_text = f"{total_dist:.2f}公里"
    tip_w, tip_h = 84, 24
    tip_x = min(max(ex - tip_w // 2, ch_left), ch_right - tip_w)
    tip_y = ey - tip_h - 10
    draw_rounded_rect(draw, [tip_x, tip_y, tip_x + tip_w, tip_y + tip_h], radius=5, fill=GREEN)
    # 小三角
    draw.polygon([(ex - 4, tip_y + tip_h), (ex + 4, tip_y + tip_h), (ex, tip_y + tip_h + 6)], fill=GREEN)
    draw.text((tip_x + tip_w // 2, tip_y + tip_h // 2), tip_text, fill=WHITE,
              font=font(10, bold=True), anchor="mm")

    # X 轴标签
    label_days = [1, 5, 10, 15, 20, 25]
    for ld in label_days:
        if ld <= days_in_month:
            lx = ch_left + int((ld - 1) * ch_w / (days_in_month - 1))
            draw.text((lx, ch_bottom + 7), f"{ld}日", fill=GRAY, font=font(9), anchor="mt")
    # 本月标签
    draw.text((ch_right, ch_bottom + 7), "本月", fill=GRAY, font=font(9), anchor="mt")

    y = ch_bottom + 28
    draw.line([0, y, W, y], fill=BORDER, width=1)
    y += 1

    # ── 跑步记录列表 ─────────────────────────────────────────
    row_h = 76
    for run in reversed(runs):
        if y + row_h > H:
            break
        draw.rectangle([0, y, W, y + row_h], fill=WHITE)

        # 左侧小图标（简单圆形跑步图标）
        draw.ellipse([14, y + 10, 36, y + 32], fill=(240, 250, 235))
        draw.ellipse([14, y + 10, 36, y + 32], outline=GREEN, width=2)

        # 标题
        draw.text((40, y + 16), "户外跑步", fill=DARK_GRAY, font=font(14, bold=True))
        # 距离
        draw.text((40, y + 38), f"{run['distance']:.2f} 公里", fill=DARK_GRAY, font=font(13))
        # 时间和配速
        draw.text((40, y + 58), f"用时 {run['duration']}  配速 {run['pace']}",
                  fill=GRAY, font=font(10))

        # 右侧日期
        date_str = f"{year}年{month}月{run['day']}日"
        draw.text((W - 16, y + 16), date_str, fill=GRAY, font=font(11), anchor="rt")

        draw.line([16, y + row_h - 1, W - 16, y + row_h - 1], fill=BORDER, width=1)
        y += row_h

    if output is None:
        output = f"keep_monthly_{year}_{month:02d}.png"

    img.save(output)
    print(f"✓ 已生成: {output}")
    print(f"  {year}年{month}月 | 距离 {total_dist:.2f}km | {total_count}次 | 消耗 {total_cals}千卡")
    return output


def main():
    ap = argparse.ArgumentParser(description="生成 Keep 月视图示例截图")
    ap.add_argument("--year",          type=int,   default=2025, help="年份 (默认 2025)")
    ap.add_argument("--month",         type=int,   default=9,    help="月份 (默认 9)")
    ap.add_argument("--distance",      type=float, default=22.0, help="当月跑步总距离 km (默认 22.0)")
    ap.add_argument("--runs",          type=int,   default=12,   help="当月跑步次数 (默认 12)")
    ap.add_argument("--time",          type=str,   default=None, help="截图时间显示，如 09:30")
    ap.add_argument("--output",        type=str,   default=None, help="输出文件路径")
    ap.add_argument("--seed",          type=int,   default=None, help="随机种子，固定可复现")
    ap.add_argument("--total-minutes", type=int,   default=None, help="Keep 历史总运动分钟数（默认自动推算一个合理大值）")
    args = ap.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    generate(
        year=args.year,
        month=args.month,
        target_distance=args.distance,
        target_runs=args.runs,
        time_str=args.time,
        output=args.output,
        total_minutes=args.total_minutes,
    )


if __name__ == "__main__":
    main()
