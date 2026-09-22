#!/usr/bin/env python3
"""批量修复 CJK 加粗渲染问题（Goldmark/CommonMark flanking 规则）。

规则（只在 `**` 与全角标点相邻、导致无法解析时才插入半角空格）：
- 开定界符：前一个字符是字母/数字（含 CJK）、后一个字符是标点 → 在开符前加空格
  例：说**（重要）** → 说 **（重要）**
- 闭定界符：前一个字符是标点、后一个字符是字母/数字 → 在闭符后加空格
  例：熵减（Entropy Reduction）**过程 → 熵减（Entropy Reduction）** 过程

保护区间（其中的 `**` 不处理）：frontmatter（--- / +++）、围栏代码块（``` / ~~~）、
行内代码（`...`）、行内数学 `\\(...\\)` 与 `$$...$$`、跨行 `$$` 与 `\\[ \\]` 数学块。
默认 dry-run，--apply 才真正写文件。
"""
import sys
import unicodedata
from pathlib import Path


def is_punct(ch):
    return unicodedata.category(ch).startswith("P")


def mask_spans(line):
    """行内代码与行内数学的 (start, end) 区间列表。"""
    spans = []
    i = 0
    while i < len(line):
        if line[i] == "`":
            j = i
            while j < len(line) and line[j] == "`":
                j += 1
            tick = line[i:j]
            k = line.find(tick, j)
            if k == -1:
                break
            spans.append((i, k + len(tick)))
            i = k + len(tick)
        elif line.startswith("\\(", i):
            k = line.find("\\)", i + 2)
            if k == -1:
                i += 2
                continue
            spans.append((i, k + 2))
            i = k + 2
        elif line.startswith("$$", i):
            k = line.find("$$", i + 2)
            if k == -1:
                i += 2
                continue
            spans.append((i, k + 2))
            i = k + 2
        else:
            i += 1
    return spans


def process_line(line):
    """返回 (新行, 修复数, 未配对标记)。无法安全配对时不改动。"""
    spans = mask_spans(line)

    def masked(pos):
        return any(s <= pos < e for s, e in spans)

    stars = []
    i = 0
    while i < len(line) - 1:
        if line[i] == "*" and line[i + 1] == "*" and not masked(i):
            if (i > 0 and line[i - 1] == "*") or (i + 2 < len(line) and line[i + 2] == "*"):
                i += 2
                continue
            stars.append(i)
            i += 2
        else:
            i += 1

    if not stars:
        return line, 0, 0
    if len(stars) % 2 == 1:
        return line, 0, 1

    inserts = []
    for idx, pos in enumerate(stars):
        before = line[pos - 1] if pos > 0 else " "
        after = line[pos + 2] if pos + 2 < len(line) else " "
        if idx % 2 == 0:  # 开定界符
            if before.isalnum() and is_punct(after):
                inserts.append(pos)
        else:  # 闭定界符
            if is_punct(before) and after.isalnum():
                inserts.append(pos + 2)

    if not inserts:
        return line, 0, 0
    out = []
    prev = 0
    for pos in sorted(inserts):
        out.append(line[prev:pos])
        out.append(" ")
        prev = pos
    out.append(line[prev:])
    return "".join(out), len(inserts), 0


def process_file(path, apply, warnings):
    lines = path.read_text(encoding="utf-8").split("\n")
    out = []
    state = "body"
    fence_marker = ""
    total = 0
    for ln, line in enumerate(lines, 1):
        stripped = line.strip()
        if ln == 1 and stripped in ("---", "+++"):
            state = "front"
            front_close = stripped
            out.append(line)
            continue
        if state == "front":
            out.append(line)
            if stripped == front_close:
                state = "body"
            continue
        if state == "fence":
            out.append(line)
            if stripped.startswith(fence_marker):
                state = "body"
            continue
        if state in ("math", "math2"):
            out.append(line)
            if (state == "math" and "$$" in stripped) or (state == "math2" and "\\]" in stripped):
                state = "body"
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            state = "fence"
            fence_marker = stripped[:3]
            out.append(line)
            continue
        if stripped == "$$":
            state = "math"
            out.append(line)
            continue
        if stripped == "\\[":
            state = "math2"
            out.append(line)
            continue
        new, n, unpaired = process_line(line)
        if unpaired:
            warnings.append(f"{path}:{ln}: 未配对的 **，已跳过")
        total += n
        out.append(new)
    if apply and total:
        path.write_text("\n".join(out), encoding="utf-8")
    return total


def main():
    apply = "--apply" in sys.argv
    warnings = []
    total = files = 0
    for p in sorted(Path("content/posts").rglob("*.md")):
        n = process_file(p, apply, warnings)
        if n:
            print(f"{p}: {n} 处")
            files += 1
            total += n
    print(f"\n{'已修复' if apply else 'DRY-RUN 待修复'}: {total} 处 / {files} 个文件")
    for w in warnings:
        print("WARN:", w)


if __name__ == "__main__":
    main()
