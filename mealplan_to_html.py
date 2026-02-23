#!/usr/bin/env python3
"""Convert a weekly meal plan written in Markdown into a styled HTML page."""

from __future__ import annotations

import argparse
import html
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple


DAY_NAME_TO_ISO = {
    "monday": 1,
    "tuesday": 2,
    "wednesday": 3,
    "thursday": 4,
    "friday": 5,
    "saturday": 6,
    "sunday": 7,
}
DAY_NAME_PATTERN = re.compile(
    r"\b(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a weekly meal plan Markdown file into a styled HTML page."
    )
    parser.add_argument("markdown", type=Path, help="Path to the source Markdown file.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Path to the HTML file that should be created. Defaults to the Markdown file name with .html.",
    )
    parser.add_argument(
        "--iso-week",
        type=int,
        help="ISO week number (1-53). When used together with --year, meal dates are shown.",
    )
    parser.add_argument(
        "--year",
        type=int,
        help="Calendar year for ISO week calculations (e.g., 2026). Requires --iso-week.",
    )
    args = parser.parse_args()
    if (args.iso_week is None) ^ (args.year is None):
        parser.error("--year and --iso-week must be provided together.")
    return args


def render_inline(text: str) -> str:
    """Escape HTML entities and convert **bold** markers to <strong> tags."""

    def _replace(match: re.Match[str]) -> str:
        return f"<strong>{html.escape(match.group(1))}</strong>"

    result = []
    last_end = 0
    for match in re.finditer(r"\*\*(.+?)\*\*", text):
        result.append(html.escape(text[last_end : match.start()]))
        result.append(_replace(match))
        last_end = match.end()
    result.append(html.escape(text[last_end:]))
    return "".join(result)


def convert_lines_to_html(lines: List[str]) -> str:
    """Turn plain Markdown-like lines into simple HTML structures."""
    html_parts: List[str] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("- "):
            items = []
            while i < len(lines):
                candidate = lines[i].strip()
                if not candidate.startswith("- "):
                    break
                items.append(render_inline(candidate[2:].strip()))
                i += 1
            html_parts.append(
                "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
            )
            continue
        html_parts.append(f"<p>{render_inline(stripped)}</p>")
        i += 1
    return "\n".join(html_parts)


def split_day_and_title(raw_title: str) -> Tuple[str, str]:
    """Split headings like '🍕 Monday – Pizza Night' into day and meal title."""
    for delimiter in (" – ", " - ", " — ", " -- "):
        if delimiter in raw_title:
            day, meal = raw_title.split(delimiter, 1)
            return day.strip(), meal.strip()
    return "", raw_title.strip()


def parse_weekly_plan(markdown_text: str) -> Tuple[str, List[str], List[dict]]:
    """Extract the document title, intro lines, and sections from the Markdown."""
    title = ""
    intro_lines: List[str] = []
    sections: List[dict] = []
    current_section: Optional[dict] = None

    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()

        if stripped.startswith("# "):
            if not title:
                title = stripped[2:].strip()
            continue

        if stripped.startswith("## "):
            if current_section:
                sections.append(current_section)
            current_section = {"raw_title": stripped[3:].strip(), "lines": []}
            continue

        if stripped == "---":
            continue

        target = intro_lines if current_section is None else current_section["lines"]
        target.append(raw_line)

    if current_section:
        sections.append(current_section)

    return title, intro_lines, sections


def extract_weekday(day_label: str) -> Optional[int]:
    """Return ISO weekday number (1-7) from the provided day label."""
    match = DAY_NAME_PATTERN.search(day_label)
    if not match:
        return None
    return DAY_NAME_TO_ISO[match.group(1).lower()]


def format_display_date(value: date) -> str:
    """Return a human-friendly date like 'Feb 25, 2026'."""
    return f"{value.strftime('%b')} {value.day}, {value.year}"


def build_html_document(
    markdown_text: str, iso_dates: Optional[Dict[int, date]] = None
) -> str:
    """Generate the full HTML document string."""
    title, intro_lines, sections = parse_weekly_plan(markdown_text)
    page_title = title or "Weekly Meal Plan"

    intro_html = convert_lines_to_html(intro_lines) if intro_lines else ""
    intro_section = (
        f'<div class="intro">{intro_html}</div>' if intro_html else ""
    )

    cards_html = []
    for section in sections:
        day_label, meal_title = split_day_and_title(section["raw_title"])
        content_html = convert_lines_to_html(section["lines"])
        weekday_number = extract_weekday(day_label) if day_label else None
        meal_date = iso_dates.get(weekday_number) if iso_dates and weekday_number else None
        date_html = (
            f'<span class="meal-date">{html.escape(format_display_date(meal_date))}</span>'
            if meal_date
            else ""
        )
        day_name_html = (
            f'<span class="day-name">{html.escape(day_label)}</span>' if day_label else ""
        )
        day_html = (
            f'<p class="meal-day">{day_name_html}{date_html}</p>' if day_label else ""
        )
        cards_html.append(
            f"""
            <section class="meal-card">
                {day_html}
                <h2>{html.escape(meal_title)}</h2>
                <div class="meal-body">
                    {content_html}
                </div>
            </section>
            """
        )

    cards_markup = "\n".join(cards_html)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{html.escape(page_title)}</title>
    <style>
        :root {{
            color-scheme: light;
            --page-bg: #f8fafc;
            --page-gradient: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e2e8f0 100%);
            --card-bg: #ffffff;
            --card-border: #e2e8f0;
            --text-primary: #0f172a;
            --text-muted: #475569;
            --accent: #ec7c30;
            --accent-soft: #ffe6cf;
        }}

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family: "Inter", "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif;
            background: var(--page-gradient);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 2.5rem 1.5rem 4rem;
        }}

        .page {{
            max-width: 1100px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 2.5rem;
        }}

        header h1 {{
            margin: 0;
            font-size: clamp(2rem, 5vw, 3.5rem);
        }}

        header .intro {{
            margin-top: 0.75rem;
            font-size: 1rem;
            color: var(--text-muted);
            max-width: 640px;
            margin-left: auto;
            margin-right: auto;
        }}

        main {{
            display: grid;
            gap: 1.5rem;
            grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
        }}

        .meal-card {{
            background: var(--card-bg);
            border-radius: 1.25rem;
            padding: 1.5rem;
            border: 1px solid var(--card-border);
            box-shadow: 0 10px 20px rgba(15, 23, 42, 0.08);
        }}

        .meal-day {{
            display: inline-flex;
            align-items: baseline;
            gap: 0.4rem;
            flex-wrap: wrap;
            margin: 0 0 0.35rem;
        }}

        .meal-day .day-name {{
            text-transform: uppercase;
            font-size: 0.8rem;
            letter-spacing: 0.08em;
            font-weight: 600;
            color: var(--accent);
        }}

        .meal-day .meal-date {{
            font-size: 0.75rem;
            color: var(--text-muted);
            letter-spacing: normal;
            text-transform: none;
            font-weight: 500;
            display: inline-flex;
            align-items: baseline;
            gap: 0.15rem;
        }}

        .meal-day .meal-date::before {{
            content: "•";
            color: var(--card-border);
        }}

        .meal-card h2 {{
            margin: 0 0 1rem;
            font-size: 1.35rem;
            color: var(--text-primary);
        }}

        .meal-body p {{
            margin: 0.35rem 0;
            color: var(--text-muted);
            line-height: 1.5;
        }}

        .meal-body ul {{
            list-style: disc;
            padding-left: 1.2rem;
            margin: 0.35rem 0 0.8rem;
            color: var(--text-muted);
        }}

        .meal-body li {{
            margin: 0.2rem 0;
        }}

        .meal-body strong {{
            background: var(--accent-soft);
            color: var(--text-primary);
            padding: 0.1rem 0.35rem;
            border-radius: 0.35rem;
        }}

        @media print {{
            @page {{
                margin: 0.5in;
            }}
            body {{
                background: #ffffff;
                padding: 0;
                color: #000;
            }}
            main {{
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.5in;
            }}
            .meal-card {{
                box-shadow: none;
                page-break-inside: avoid;
                break-inside: avoid;
                margin: 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="page">
        <header>
            <h1>{html.escape(page_title)}</h1>
            {intro_section}
        </header>
        <main>
            {cards_markup}
        </main>
    </div>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    input_path: Path = args.markdown
    output_path: Path = args.output or input_path.with_suffix(".html")

    markdown_text = input_path.read_text(encoding="utf-8")
    iso_dates: Optional[Dict[int, date]] = None
    if args.iso_week is not None and args.year is not None:
        try:
            iso_dates = {
                weekday: date.fromisocalendar(args.year, args.iso_week, weekday)
                for weekday in range(1, 8)
            }
        except ValueError as exc:
            raise SystemExit(f"Invalid ISO week/year combination: {exc}")

    html_document = build_html_document(markdown_text, iso_dates=iso_dates)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_document, encoding="utf-8")
    print(f"Meal plan saved to {output_path}")


if __name__ == "__main__":
    main()
