"""Fetch daily EUR exchange rates from frankfurter.app and output a forward-filled CSV.

Supports EUR/GBP, EUR/SEK, EUR/PLN.  Weekend and holiday gaps are forward-filled
so that every calendar day in the requested range has a rate row.
"""

from __future__ import annotations

import csv
import sys
from datetime import date, timedelta
from pathlib import Path

import click
import requests

TARGETS: list[str] = ["GBP", "SEK", "PLN"]
BASE: str = "EUR"
API_BASE: str = "https://api.frankfurter.app"
# The API tends to cap responses at roughly 365 days.  We chunk conservatively.
MAX_DAYS_PER_REQUEST: int = 360


def _date_range(start: date, end: date) -> list[date]:
    """Return a list of dates from *start* to *end* inclusive."""
    days: list[date] = []
    current = start
    while current <= end:
        days.append(current)
        current += timedelta(days=1)
    return days


def _chunk_date_range(start: date, end: date, chunk_days: int = MAX_DAYS_PER_REQUEST) -> list[tuple[date, date]]:
    """Split a date range into chunks of at most *chunk_days* days."""
    chunks: list[tuple[date, date]] = []
    current_start = start
    while current_start <= end:
        current_end = min(current_start + timedelta(days=chunk_days - 1), end)
        chunks.append((current_start, current_end))
        current_start = current_end + timedelta(days=1)
    return chunks


def fetch_rates_from_api(start: date, end: date, targets: list[str]) -> dict[str, dict[str, float]]:
    """Fetch rates from frankfurter.app, returning {date_str: {target: rate}}.

    Handles chunking so that ranges longer than ~365 days are split into
    multiple requests.
    """
    all_rates: dict[str, dict[str, float]] = {}
    targets_param = ",".join(targets)

    for chunk_start, chunk_end in _chunk_date_range(start, end):
        url = f"{API_BASE}/{chunk_start.isoformat()}..{chunk_end.isoformat()}?from={BASE}&to={targets_param}"
        click.echo(f"  Fetching {url}")
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        rates_block: dict[str, dict[str, float]] = data.get("rates", {})
        all_rates.update(rates_block)

    return all_rates


def forward_fill(
    raw_rates: dict[str, dict[str, float]],
    start: date,
    end: date,
    targets: list[str],
) -> list[dict[str, object]]:
    """Forward-fill missing dates so every calendar day has a rate for each target.

    Returns a list of row dicts ready for CSV writing.
    """
    rows: list[dict[str, object]] = []
    last_known: dict[str, float] = {}

    for day in _date_range(start, end):
        day_str = day.isoformat()
        day_rates = raw_rates.get(day_str, {})

        for target in targets:
            if target in day_rates:
                last_known[target] = day_rates[target]

            rate = last_known.get(target)
            if rate is None:
                # No data seen yet for this target; skip until we have one
                continue

            rows.append(
                {
                    "rate_date": day_str,
                    "base_currency": BASE,
                    "target_currency": target,
                    "rate": round(rate, 6),
                    "rate_inverse": round(1.0 / rate, 6),
                }
            )

    return rows


def write_csv(rows: list[dict[str, object]], path: Path) -> None:
    """Write rate rows to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["rate_date", "base_currency", "target_currency", "rate", "rate_inverse"]
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    click.echo(f"  Wrote {len(rows)} rows to {path}")


def load_existing_csv(path: Path) -> list[dict[str, object]] | None:
    """Load an existing CSV as a list of dicts, or return None if missing."""
    if not path.exists():
        return None
    with open(path, newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader)


@click.command()
@click.option(
    "--start-date",
    default="2025-01-01",
    show_default=True,
    help="Start date (YYYY-MM-DD).",
)
@click.option(
    "--end-date",
    default=lambda: date.today().isoformat(),
    show_default=True,
    help="End date (YYYY-MM-DD). Defaults to today.",
)
@click.option(
    "--output",
    default="dbt_project/seeds/fx_rates_daily.csv",
    show_default=True,
    type=click.Path(),
    help="Output CSV path.",
)
@click.option(
    "--offline",
    is_flag=True,
    default=False,
    help="Skip API call; reuse existing CSV.",
)
def main(start_date: str, end_date: str, output: str, offline: bool) -> None:
    """Fetch daily EUR exchange rates and write a forward-filled CSV."""
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    out_path = Path(output)

    if offline:
        existing = load_existing_csv(out_path)
        if existing is None:
            click.echo("ERROR: --offline specified but no existing CSV found.", err=True)
            sys.exit(1)
        click.echo(f"Offline mode: keeping existing {out_path} ({len(existing)} rows).")
        return

    click.echo(f"Fetching EUR rates for {TARGETS} from {start} to {end} ...")
    try:
        raw = fetch_rates_from_api(start, end, TARGETS)
    except Exception as exc:
        click.echo(f"WARNING: API request failed ({exc}). Falling back to existing CSV.", err=True)
        if out_path.exists():
            click.echo(f"  Existing CSV preserved at {out_path}")
        else:
            click.echo("  No existing CSV to fall back to.", err=True)
            sys.exit(1)
        return

    rows = forward_fill(raw, start, end, TARGETS)
    if not rows:
        click.echo("WARNING: No rate data returned. Keeping existing CSV if present.", err=True)
        return

    write_csv(rows, out_path)
    click.echo("Done.")


if __name__ == "__main__":
    main()
