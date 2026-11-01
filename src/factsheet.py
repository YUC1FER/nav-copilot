"""
Fill the factsheet HTML template from reconciled figures.

Formatting only: every number arrives already computed (see factsheet_figures.py).
Template placeholders use string.Template syntax ($name); a placeholder with no
value raises KeyError instead of silently printing blank.
"""

import html
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = ROOT / "templates" / "factsheet.html"


def format_figures(figures: dict, details: dict[str, str]) -> dict[str, str]:
    """Turn figures and fund details into HTML-escaped display strings for the template."""
    values = {
        "fund_name": details["fund_name"],
        "share_class": details["share_class"],
        "isin": details["isin"],
        "currency": details["currency"],
        "as_of": f"{figures['as_of']:%Y-%m-%d}",
        "nav_end": f"{figures['nav_end']:.4f}",
        "mtd_return": f"{figures['mtd_return_pct']:+.2f}%",
        "volatility": f"{figures['annualised_vol_pct']:.2f}%",
        "aum_end": f"{figures['aum_end']:,.2f}",
    }
    return {key: html.escape(value) for key, value in values.items()}


def render_factsheet(figures: dict, details: dict[str, str],
                     template_path: Path, out_path: Path) -> Path:
    """Write the filled factsheet as UTF-8 HTML and return its path."""
    template = Template(Path(template_path).read_text(encoding="utf-8"))
    page = template.substitute(format_figures(figures, details))
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(page, encoding="utf-8")
    return out_path
