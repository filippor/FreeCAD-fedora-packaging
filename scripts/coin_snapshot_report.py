#!/usr/bin/env python3
"""Generate an HTML diff report for TestCoinNodeSnapshots output.

Usage:
    coin_snapshot_report.py <out_dir>

<out_dir> is the FC_VISUAL_OUT_DIR, expected to contain:
    actual/    – rendered PNGs
    expected/  – baseline copies
    diff/      – diff PNGs (red pixels = mismatched)
"""

import sys
from pathlib import Path


def _img_tag(src: str | None, label: str) -> str:
    if src:
        return (
            f'<figure style="margin:0">'
            f'<img src="{src}" style="max-width:100%;border:1px solid #ccc">'
            f'<figcaption style="text-align:center;font-size:.75em;color:#555">{label}</figcaption>'
            f"</figure>"
        )
    return f'<figure style="margin:0"><div style="width:100%;height:80px;background:#eee;display:flex;align-items:center;justify-content:center;color:#aaa;font-size:.75em">missing</div><figcaption style="text-align:center;font-size:.75em;color:#555">{label}</figcaption></figure>'


def _compare_slider_tag(expected_src: str | None, actual_src: str | None, slider_id: str) -> str:
    if not expected_src or not actual_src:
        return (
            '<div class="slider-missing">'
            "missing expected or actual image"
            "</div>"
        )

    return (
        f'<div class="compare-wrap" data-slider-id="{slider_id}">'
        f'  <div class="compare-stage">'
        f'    <img class="compare-img expected" src="{expected_src}" alt="expected">'
        f'    <img class="compare-img actual" src="{actual_src}" alt="actual">'
        f'    <div class="divider" style="left:50%"></div>'
        f'  </div>'
        f'  <input class="slider" type="range" min="0" max="100" value="50" aria-label="Compare expected and actual">'
        f'  <div class="slider-labels"><span>expected (left)</span><span>actual (right)</span></div>'
        f'</div>'
    )


def main(out_dir: Path) -> None:
    actual_dir = out_dir / "actual"
    expected_dir = out_dir / "expected"
    diff_dir = out_dir / "diff"

    names = sorted(
        {p.stem for p in actual_dir.glob("*.png")}
        | {p.stem for p in expected_dir.glob("*.png")}
    )

    rows = []
    for idx, name in enumerate(names):
        actual_path = actual_dir / f"{name}.png"
        expected_path = expected_dir / f"{name}.png"
        diff_path = diff_dir / f"{name}.png"

        has_diff = diff_path.is_file()
        row_bg = "#fff8f8" if has_diff else "#f8fff8"
        status = "&#x26A0; diff" if has_diff else "&#x2713; ok"
        status_color = "#c00" if has_diff else "#080"

        actual_src = f"actual/{name}.png" if actual_path.is_file() else None
        expected_src = f"expected/{name}.png" if expected_path.is_file() else None
        diff_src = f"diff/{name}.png" if has_diff else None
        c = _compare_slider_tag(expected_src, actual_src, f"cmp-{idx}")
        d = _img_tag(diff_src, "diff") if has_diff else ""

        detail_row_id = f"detail-{idx}"
        is_open = has_diff
        expanded_attr = "true" if is_open else "false"
        toggle_text = "Hide" if is_open else "Show"
        detail_style = "" if is_open else "display:none"

        rows.append(
            f'<tr class="row-header" style="background:{row_bg}">'
            f'<td style="white-space:nowrap;font-family:monospace;padding:4px 8px">{name}</td>'
            f'<td style="text-align:center;font-weight:bold;color:{status_color};white-space:nowrap">{status}</td>'
            f'<td colspan="2" style="text-align:right">'
            f'<button type="button" class="row-toggle" data-target="{detail_row_id}" aria-expanded="{expanded_attr}">{toggle_text}</button>'
            f"</td>"
            f"</tr>"
            f'<tr id="{detail_row_id}" class="row-detail" style="{detail_style}">'
            f'<td colspan="2"></td><td>{c}</td><td>{d}</td>'
            f"</tr>"
        )

    total = len(names)
    diffs = sum(1 for name in names if (diff_dir / f"{name}.png").is_file())
    summary = f"{total} nodes &mdash; {diffs} with pixel differences"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>TestCoinNodeSnapshots report</title>
<style>
body {{ font-family: sans-serif; margin: 1em 2em; }}
h1 {{ font-size: 1.2em; }}
table {{ border-collapse: collapse; width: 100%; }}
th {{ background:#f0f0f0; padding:4px 8px; text-align:left; font-size:.85em; }}
td {{ padding:4px 8px; vertical-align:top; }}
tr:hover {{ outline:1px solid #aaa; }}
.row-header:hover {{ outline:none; }}
.row-toggle {{
    border:1px solid #bbb;
    background:#f7f7f7;
    color:#222;
    font-size:.78em;
    padding:2px 8px;
    border-radius:4px;
    cursor:pointer;
}}
.row-toggle[aria-expanded="true"] {{
    border-color:#1a73e8;
    background:#e8f0fe;
    color:#174ea6;
}}
.compare-wrap {{ min-width: 340px; max-width: 560px; }}
.compare-stage {{ position:relative; border:1px solid #ccc; background:#fff; line-height:0; }}
.compare-img {{ display:block; width:100%; height:auto; }}
.compare-img.actual {{
    position:absolute;
    inset:0;
    clip-path: inset(0 0 0 50%);
}}
.divider {{
    position:absolute;
    top:0;
    bottom:0;
    width:2px;
    background:#1a73e8;
    transform:translateX(-1px);
    pointer-events:none;
}}
.slider {{ width:100%; margin-top:8px; }}
.slider-labels {{ display:flex; justify-content:space-between; font-size:.75em; color:#555; }}
.slider-missing {{
    width:100%;
    min-height:80px;
    background:#eee;
    color:#888;
    display:flex;
    align-items:center;
    justify-content:center;
    border:1px solid #ccc;
    font-size:.85em;
}}
</style>
</head>
<body>
<h1>TestCoinNodeSnapshots diff report</h1>
<p>{summary}</p>
<table>
<thead><tr>
    <th>Node</th><th>Status</th><th>Compare expected/actual</th><th>Diff</th>
</tr></thead>
<tbody>
{"".join(rows)}
</tbody>
</table>
<script>
document.querySelectorAll('.compare-wrap').forEach(function(wrap) {{
    var slider = wrap.querySelector('.slider');
    var actual = wrap.querySelector('.compare-img.actual');
    var divider = wrap.querySelector('.divider');

    var update = function() {{
        var v = Number(slider.value);
        var split = Math.max(0, Math.min(100, v));
        actual.style.clipPath = 'inset(0 0 0 ' + split + '%)';
        divider.style.left = split + '%';
    }};

    slider.addEventListener('input', update);
    update();
}});

document.querySelectorAll('.row-toggle').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
        var rowId = btn.dataset.target;
        var row = document.getElementById(rowId);
        if (!row) {{
            return;
        }}

        var isOpen = btn.getAttribute('aria-expanded') === 'true';
        var nextOpen = !isOpen;
        row.style.display = nextOpen ? '' : 'none';
        btn.setAttribute('aria-expanded', nextOpen ? 'true' : 'false');
        btn.textContent = nextOpen ? 'Hide' : 'Show';
    }});
}});
</script>
</body>
</html>
"""

    report_path = out_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <out_dir>", file=sys.stderr)
        sys.exit(1)
    main(Path(sys.argv[1]))
