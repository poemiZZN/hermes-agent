#!/usr/bin/env python3
"""
Basics-pro 分镜脚本自动验证脚本 v1.0
用法: python verify_storyboard.py <分镜文件路径> [--min-duration 60] [--max-segment 30]
检查项: 11 项全部自动化，任一不通过则返回非零退出码
"""

import re
import sys
import argparse
from pathlib import Path


def find_episode_boundaries(lines):
    """Find start/end line indices for each episode."""
    episodes = []
    for i, line in enumerate(lines):
        m = re.match(r'# 第(\d+)集', line)
        if m:
            episodes.append((i, m.group(1)))
    return episodes


def detect_shot_id_format(ep_content, ep_num):
    """Detect shot ID format: 'A' = S-{ep}.{seg}-{shot}, 'B' = S-{ep:02d}-{shot}."""
    # Check for format B (two-segment) first: S-01-03
    ep_padded = ep_num.zfill(2)
    if re.search(r'【镜头 S-' + ep_padded + r'-\d+', ep_content):
        return 'B', ep_padded
    # Default to format A (three-segment): S-1.1-03
    return 'A', ep_num


def build_shot_split_regex(ep_num, fmt='A', ep_padded=None):
    """Build regex for splitting shots. Returns the pattern string."""
    if fmt == 'B' and ep_padded:
        return r'【镜头 S-' + ep_padded + r'-\d+'
    return r'【镜头 S-' + ep_num + r'\.\d-\d+'


def parse_header_durations(ep_content):
    """Parse header line like '段落：第1段（24.5s）→ 第2段（20.0s）→ 第3段（16.5s）→ 总计 61.0s'"""
    for line in ep_content.split('\n'):
        if '段落：' in line:
            nums = re.findall(r'([\d.]+)s', line)
            return [float(n) for n in nums]
    return None


def parse_shot_durations(ep_content, ep_num):
    """Parse actual shot durations from S-X.Y-ZZ or S-XX-YY lines."""
    fmt, ep_key = detect_shot_id_format(ep_content, ep_num)
    if fmt == 'B':
        durations = re.findall(
            r'S-' + ep_key + r'-(\d+) \| 时长：([\d.]+)s',
            ep_content
        )
        seg_dur = {}
        for shot_num, dur in durations:
            # Format B: all shots in one pseudo-segment for duration tracking
            seg_dur['1'] = seg_dur.get('1', 0) + float(dur)
        return seg_dur
    else:
        durations = re.findall(
            r'S-' + ep_num + r'\.(\d)-\d+ \| 时长：([\d.]+)s',
            ep_content
        )
        seg_dur = {}
        for seg, dur in durations:
            seg_dur[seg] = seg_dur.get(seg, 0) + float(dur)
        return seg_dur


def parse_shot_props(ep_content, ep_num):
    """Collect all props from shot '道具' fields."""
    props = set()
    split_regex = build_shot_split_regex(ep_num, *detect_shot_id_format(ep_content, ep_num))
    shots = re.split(split_regex, ep_content)
    for shot in shots[1:]:  # skip content before first shot
        m = re.search(r'^道具：(.+?)$', shot, re.MULTILINE)
        if m:
            for p in re.split(r'[、,，]', m.group(1)):
                p = p.strip()
                if p and p != '无':
                    props.add(p)
    return props


def parse_shot_characters(ep_content, ep_num):
    """Collect all characters from shot '人物' fields."""
    chars = set()
    split_regex = build_shot_split_regex(ep_num, *detect_shot_id_format(ep_content, ep_num))
    shots = re.split(split_regex, ep_content)
    for shot in shots[1:]:
        m = re.search(r'^人物：(.+?)$', shot, re.MULTILINE)
        if m:
            for c in re.split(r'[、,，]', m.group(1)):
                c = c.strip()
                if c and c != '无':
                    chars.add(c)
    return chars


def parse_header_props(ep_content):
    """Parse '> 道具：' from header (may be on combined line or separate line)."""
    # Try combined line: '> 场景：... | 人物：... | 道具：...'
    for line in ep_content.split('\n'):
        if line.startswith('> 场景：') and '道具：' in line:
            m = re.search(r'道具：(.+?)$', line)
            if m:
                props = set()
                for p in re.split(r'[、,，]', m.group(1)):
                    p = p.strip()
                    if p:
                        props.add(p)
                return props
    # Try separate line: '> 道具：...'
    m = re.search(r'^> 道具：(.+?)$', ep_content, re.MULTILINE)
    if m:
        props = set()
        for p in re.split(r'[、,，]', m.group(1)):
            p = p.strip()
            if p:
                props.add(p)
        return props
    return set()


def parse_header_characters(ep_content):
    """Parse '> 人物：' from header (may be on combined line or separate line)."""
    # Try combined line: '> 场景：... | 人物：...'
    for line in ep_content.split('\n'):
        if line.startswith('> 场景：') and '人物：' in line:
            m = re.search(r'人物：(.+?)(?:\||$)', line)
            if m:
                chars = set()
                for c in re.split(r'[、,，]', m.group(1)):
                    c = c.strip()
                    if c:
                        chars.add(c)
                return chars
    # Try separate line: '> 人物：...'
    m = re.search(r'^> 人物：(.+?)$', ep_content, re.MULTILINE)
    if m:
        chars = set()
        for c in re.split(r'[、,，]', m.group(1)):
            c = c.strip()
            if c:
                chars.add(c)
        return chars
    return set()


def count_shot_types(ep_content, ep_num):
    """Count close-up ratio from shot '景别' fields."""
    split_regex = build_shot_split_regex(ep_num, *detect_shot_id_format(ep_content, ep_num))
    shots = re.split(split_regex, ep_content)
    total = 0
    closeup = 0
    for shot in shots[1:]:
        m = re.search(r'^景别：(.+?)[ \n]', shot, re.MULTILINE)
        if m:
            total += 1
            stype = m.group(1)
            if '特写' in stype or '近景' in stype:
                closeup += 1
    return total, closeup


def check_multi_camera(ep_content, ep_num):
    """Check for multiple camera movements per shot."""
    split_regex = build_shot_split_regex(ep_num, *detect_shot_id_format(ep_content, ep_num))
    shots = re.split(split_regex, ep_content)
    multi = []
    for shot in shots[1:]:
        m = re.search(r'^运镜：(.+?)[（(]', shot, re.MULTILINE)
        if m:
            cam = m.group(1)
            if '+' in cam or '＋' in cam:
                multi.append(cam.strip())
    return multi


STATIC_KEYWORDS = ['固定机位', '定格', '静止镜头', '静止', '定格凝视', '特写定格', '俯拍定格']


def count_static_shots(ep_content, ep_num):
    """Count static shot ratio from shot '运镜' fields. Static ≤5% required."""
    split_regex = build_shot_split_regex(ep_num, *detect_shot_id_format(ep_content, ep_num))
    shots = re.split(split_regex, ep_content)
    total = 0
    static = 0
    static_details = []
    for shot in shots[1:]:
        m = re.search(r'^运镜：(.+?)[（(]', shot, re.MULTILINE)
        if m:
            total += 1
            cam = m.group(1)
            if any(kw in cam for kw in STATIC_KEYWORDS):
                static += 1
                # extract shot ID for reporting
                sid = re.search(r'【镜头 (S-[^\|]+)', shot)
                static_details.append(sid.group(1) if sid else 'unknown')
    return total, static, static_details


def verify_episode(ep_content, ep_num, min_duration=None, max_segment=30):
    """Run all 11 checks on a single episode. Returns (passed, issues)."""
    issues = []

    # Parse header
    hdr_nums = parse_header_durations(ep_content)
    if not hdr_nums:
        return False, ['无法解析标头']

    # Determine header segment count (generalized for N segments)
    # Last element is total, preceding elements are segment durations
    hdr_segs = len(hdr_nums) - 1
    hdr_seg_durs = hdr_nums[:hdr_segs]  # segment durations
    th = hdr_nums[-1]  # total

    # Parse actual durations
    seg_dur = parse_shot_durations(ep_content, ep_num)
    at = sum(seg_dur.values())
    actual_segs = len(seg_dur)

    # Check 1: segment durations within model limit
    for seg_key, dur in seg_dur.items():
        if dur > max_segment:
            issues.append(f'段{seg_key}超时: {dur:.1f}s > {max_segment}s')

    # Check 11(a): segment count match
    if hdr_segs != actual_segs:
        issues.append(f'段落数: 标头={hdr_segs}段, 实际={actual_segs}段')

    # Check 11(b): segment duration match (generalized for N segments)
    for i in range(max(hdr_segs, actual_segs)):
        seg_key = str(i + 1)
        hdr_dur = hdr_seg_durs[i] if i < len(hdr_seg_durs) else 0
        actual_dur = seg_dur.get(seg_key, 0)
        if abs(hdr_dur - actual_dur) > 0.5:
            issues.append(f'段{seg_key}时长: 标头={hdr_dur}s, 实际={actual_dur:.1f}s')

    # Check 11(c): total duration match
    if abs(th - at) > 1.0:
        issues.append(f'总时长: 标头={th}s, 实际={at:.1f}s')

    # Check 11(d): minimum duration
    if min_duration is not None and at < min_duration:
        issues.append(f'总时长不足: {at:.1f}s < {min_duration}s')

    # Check 11(e): props consistency
    h_props = parse_header_props(ep_content)
    s_props = parse_shot_props(ep_content, ep_num)
    if h_props != s_props:
        extra = h_props - s_props
        missing = s_props - h_props
        if extra:
            issues.append(f'标头虚标道具（未出现在任何镜头中）: {extra}')
        if missing:
            issues.append(f'镜头中道具未在标头列出: {missing}')

    # Check 11(f): character consistency
    h_chars = parse_header_characters(ep_content)
    s_chars = parse_shot_characters(ep_content, ep_num)
    if h_chars != s_chars:
        extra = h_chars - s_chars
        missing = s_chars - h_chars
        if extra:
            issues.append(f'标头虚标人物（未出现在任何镜头中）: {extra}')
        if missing:
            issues.append(f'镜头中人物未在标头列出: {missing}')

    # Check: close-up ratio
    total, closeup = count_shot_types(ep_content, ep_num)
    ratio = closeup / total * 100 if total > 0 else 0
    if ratio < 60:
        issues.append(f'特写占比不足: {ratio:.0f}% (需≥60%)')

    # Check: multi-camera
    multi = check_multi_camera(ep_content, ep_num)
    if multi:
        issues.append(f'多运镜堆砌: {len(multi)}个镜头使用了多运镜')

    # Check: static shot ratio (v5.7 新增)
    static_total, static_count, static_details = count_static_shots(ep_content, ep_num)
    static_ratio = static_count / static_total * 100 if static_total > 0 else 0
    if static_ratio > 5:
        issues.append(f'静态镜头占比超标: {static_ratio:.0f}% ({static_count}/{static_total}) (需≤5%). 建议将以下镜头替换为极慢运动：')
        for sd in static_details:
            issues.append(f'  └─ {sd}: 建议替换为 微推（1mm/s）或 手持微晃 0.3Hz')

    shot_count = total
    passed = len(issues) == 0

    return passed, issues, {
        'segments': actual_segs,
        'shots': shot_count,
        'duration': at,
        'closeup_ratio': ratio,
        'static_ratio': static_ratio,
        'props': len(s_props),
        'chars': len(s_chars),
        'seg_dur': seg_dur,
    }


def main():
    parser = argparse.ArgumentParser(description='Basics-pro 分镜验证')
    parser.add_argument('file', help='分镜脚本 markdown 文件路径')
    parser.add_argument('--min-duration', type=float, default=None, help='可选的每集最低时长(s)，未填不检查下限')
    parser.add_argument('--max-segment', type=float, default=30, help='单段最高时长(s)')
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f'❌ 文件不存在: {filepath}')
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    episodes = find_episode_boundaries(lines)
    if not episodes:
        print('❌ 未找到任何分集')
        sys.exit(1)

    all_passed = True
    total_shots = 0
    total_duration = 0

    for idx, (start, ep_num) in enumerate(episodes):
        end = episodes[idx + 1][0] if idx + 1 < len(episodes) else len(lines)
        ep_content = ''.join(lines[start:end])

        result = verify_episode(
            ep_content, ep_num,
            args.min_duration,
            args.max_segment
        )
        if len(result) == 2:
            passed, issues = result
            info = {'segments': 0, 'shots': 0, 'duration': 0, 'closeup_ratio': 0, 'static_ratio': 0, 'props': 0, 'chars': 0, 'seg_dur': {}}
        else:
            passed, issues, info = result

        total_shots += info['shots']
        total_duration += info['duration']

        seg_str = ' + '.join(
            f"{info['seg_dur'].get(k, 0):.1f}s"
            for k in sorted(info['seg_dur'].keys())
        )

        status = '✅' if passed else '❌'
        print(f"{status} Ep{ep_num}: {seg_str} = {info['duration']:.1f}s | "
              f"{info['shots']}镜 | 特写{info['closeup_ratio']:.0f}% | 静态{info['static_ratio']:.0f}% | "
              f"道具{info['props']} | 人物{info['chars']}")

        if not passed:
            all_passed = False
            for issue in issues:
                print(f'   └─ {issue}')

    print(f"\n{'='*50}")
    print(f"总计: {len(episodes)}集 | {total_shots}镜 | {total_duration:.1f}s")
    if all_passed:
        print("✅ 全部通过")
    else:
        print("❌ 存在未通过项，请修复后重新运行")
        sys.exit(1)


if __name__ == '__main__':
    main()