# Meal Plan Builder

A small CLI tool for turning a weekly meal plan written in Markdown into a polished, print-friendly HTML overview. The converter understands your day headings, keeps your private recipe content out of Git, and can show actual calendar dates for each meal when you tell it which ISO week you are planning.

## Requirements

- Python 3.9+ (tested with the system `python3`)

## Directory Layout

- `mealplan_to_html.py` – CLI script that converts markdown plans to styled HTML
- `NN_month/input/` – drop weekly `*.md` files here (ignored by Git)
- `NN_month/output/` – generated HTML files end up here (ignored by Git)
- `.gitignore` – ensures the monthly folders and all markdown/HTML exports stay private

Each month directory is prefixed with its calendar number (`01_january`, `02_february`, …) so they stay in chronological order. When you add a new month, keep the same `input/` and `output/` structure so the ignore rules continue to work automatically.

## Usage

```bash
# Basic conversion (HTML goes next to the markdown file)
python3 mealplan_to_html.py 02_february/input/KW9.md

# Specify a custom output path
python3 mealplan_to_html.py 02_february/input/KW9.md -o 02_february/output/KW9.html

# Also show calendar dates for ISO week 9 in 2026
python3 mealplan_to_html.py \
  02_february/input/KW9.md \
  -o 02_february/output/KW9.html \
  --year 2026 \
  --iso-week 9
```

The script infers dates from the ISO calendar, so make sure your markdown headings include day names (e.g., `## 🍕 Wednesday – Pizza Night`). If a day name is missing or written differently, that entry simply renders without a date badge.

## Styling Notes

- Light theme by default with minimalist accents so it prints cleanly.
- Print stylesheet keeps the two-column grid and avoids breaking meal cards across pages.
- Update the CSS inside `mealplan_to_html.py` if you want different colors or fonts; no external assets are required.

## Tips

- Keep sensitive content in the numbered month folders so `.gitignore` can protect it and they stay ordered chronologically.
- Commit the script and README so collaborators have the tooling, but share actual meal plans over a private channel.
