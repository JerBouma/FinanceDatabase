"""Stats Page Model"""

__docformat__ = "google"

from datetime import datetime
from html import escape
from typing import Any

ACCENT = "#38bdf8"
MUTED = "#94a3b8"
WEEK = 7


def convert_number(value: float) -> str:
    """
    Format a count with thousands separators.

    Args:
        value (float): The count.

    Returns:
        str: The formatted count.
    """
    return f"{value:,.0f}"


def convert_day(day: str) -> str:
    """
    Format an ISO date as "11 Oct".

    Args:
        day (str): The date as YYYY-MM-DD.

    Returns:
        str: The short date.
    """
    return datetime.strptime(day, "%Y-%m-%d").strftime("%-d %b")


def select_history(summary: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Select the daily series from the first day with calls onwards.

    Args:
        summary (dict[str, Any]): The totals of ``UsageAnalytics.get_summary``.

    Returns:
        list[dict[str, Any]]: One entry per day with its calls and users.
    """
    history = summary.get("daily_calls") or []
    first = next((i for i, entry in enumerate(history) if entry["calls"]), len(history))
    return history[first:]


def create_axis_labels(history: list[dict[str, Any]]) -> str:
    """
    Create about six evenly spread date labels under a chart, in HTML so they stay
    readable at any width.

    Args:
        history (list[dict[str, Any]]): The daily series.

    Returns:
        str: The labels.
    """
    count = len(history)
    step = max(1, -(-count // 6))
    labels = "".join(
        f"<span>{convert_day(entry['date']) if i % step == 0 else ''}</span>"
        for i, entry in enumerate(history)
    )
    return f'<div class="axis" style="--days:{count}">{labels}</div>'


def create_bar_chart(
    history: list[dict[str, Any]], key: str, colour: str, label: str
) -> str:
    """
    Create a bar chart of one daily figure.

    Args:
        history (list[dict[str, Any]]): The daily series.
        key (str): The figure, "calls" or "users".
        colour (str): The bar colour.
        label (str): The unit shown on hover.

    Returns:
        str: The SVG chart.
    """
    width, height = 900, 200
    values = [entry[key] for entry in history]
    top = max(values) * 1.08 if values and max(values) else 1
    slot = width / len(values)
    bars = "".join(
        f'<rect x="{i * slot + slot * 0.15:.1f}" y="{height - value / top * height:.1f}" '
        f'width="{slot * 0.7:.1f}" height="{value / top * height:.1f}" rx="2" fill="{colour}">'
        f'<title>{convert_day(entry["date"])}: {convert_number(value)} {label}</title></rect>'
        for i, (entry, value) in enumerate(zip(history, values, strict=True))
    )
    return (
        f'<svg viewBox="0 -10 {width} {height + 10}" role="img" aria-label="Daily {label}">'
        f"{bars}</svg>{create_axis_labels(history)}"
    )


def create_tools_table(tools: list[dict[str, Any]], total: int) -> str:
    """
    Create the table of the most used tools with their share and response time.

    Args:
        tools (list[dict[str, Any]]): The tools, most used first.
        total (int): All calls.

    Returns:
        str: The HTML table.
    """
    if not tools:
        return '<p class="muted">No calls yet.</p>'
    top = tools[0]["calls"]
    head = (
        '<div class="tool head"><span>Tool</span><span></span><span class="num">Calls</span>'
        '<span class="num">Share</span><span class="num">Avg. time</span></div>'
    )
    return head + "".join(
        f'<div class="tool"><span class="name">{escape(str(tool["tool"]))}</span>'
        f'<span class="bar"><i style="width:{tool["calls"] / top * 100:.1f}%"></i></span>'
        f'<span class="num">{convert_number(tool["calls"])}</span>'
        f'<span class="num muted">{tool["calls"] / total * 100:.1f}%</span>'
        f'<span class="num muted">{tool["average_seconds"]:.2f}s</span></div>'
        for tool in tools
    )


def get_observations(
    summary: dict[str, Any], history: list[dict[str, Any]]
) -> list[str]:
    """
    Get a few plain-language observations from the totals.

    Args:
        summary (dict[str, Any]): The totals.
        history (list[dict[str, Any]]): The daily series from the first call onwards.

    Returns:
        list[str]: The observations as HTML.
    """
    notes = []
    if len(history) >= 2 * WEEK:
        last = sum(entry["calls"] for entry in history[-WEEK:])
        before = sum(entry["calls"] for entry in history[-2 * WEEK : -WEEK])
        if before:
            change = (last - before) / before * 100
            notes.append(
                f"Calls over the last 7 days are {'up' if change >= 0 else 'down'} "
                f"{abs(change):.0f}% on the 7 days before."
            )
    if history:
        busiest = max(history, key=lambda entry: entry["calls"])
        notes.append(
            f"The busiest day was {convert_day(busiest['date'])}, with "
            f"{convert_number(busiest['calls'])} calls by {busiest['users']} users."
        )
    tools = summary.get("top_tools") or []
    total = summary.get("total_calls") or 0
    if tools and total:
        notes.append(
            f"<code>{escape(str(tools[0]['tool']))}</code> answers "
            f"{tools[0]['calls'] / total * 100:.0f}% of all calls."
        )
    if summary.get("average_calls_per_user"):
        notes.append(
            f"A user makes {summary['average_calls_per_user']:.0f} calls on average."
        )
    if summary.get("new_users_last_7_days"):
        notes.append(
            f"{summary['new_users_last_7_days']} new users in the last 7 days."
        )
    return notes


def render_stats_page(summary: dict[str, Any], json_url: str, website: str) -> str:
    """
    Render the usage totals as an HTML dashboard.

    Args:
        summary (dict[str, Any]): The totals of ``UsageAnalytics.get_summary``.
        json_url (str): Where the same totals are served as JSON.
        website (str): The documentation page.

    Returns:
        str: The page.
    """
    history = select_history(summary)
    total = summary.get("total_calls") or 0
    success = summary.get("success_rate")
    cards = [
        ("Total calls", convert_number(total)),
        ("Users", convert_number(summary.get("unique_users") or 0)),
        ("Users today", convert_number(summary.get("users_today") or 0)),
        ("Users, last 7 days", convert_number(summary.get("users_last_7_days") or 0)),
        ("Calls, last 7 days", convert_number(summary.get("calls_last_7_days") or 0)),
        ("Success rate", f"{success * 100:.1f}%" if success is not None else "–"),
    ]
    card_html = "".join(
        f'<div class="card"><div class="label">{label}</div><div class="value">{value}</div></div>'
        for label, value in cards
    )
    notes = "".join(f"<li>{note}</li>" for note in get_observations(summary, history))
    since = f" since {convert_day(history[0]['date'])}" if history else ""
    charts = (
        f"<section><h2>Calls per day{since}</h2>"
        f"{create_bar_chart(history, 'calls', 'rgba(56,189,248,0.55)', 'calls')}</section>"
        f"<section><h2>Users per day{since}</h2>"
        f"{create_bar_chart(history, 'users', 'rgba(251,191,36,0.6)', 'users')}</section>"
        if history
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="300">
<title>Finance Database MCP · Usage</title>
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<style>
  html {{ background: #020617; }}
  body {{ margin: 0; min-height: 100vh; background: linear-gradient(135deg, #0f172a 0%, #020617 100%); color: #f8fafc;
          font-family: Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }}
  main {{ max-width: 64rem; margin: 0 auto; padding: 2.5rem 1rem 3rem; }}
  .head {{ display: flex; align-items: center; gap: 0.9rem; }}
  .head img {{ width: 3rem; height: 3rem; border-radius: 0.8rem; }}
  h1 {{ margin: 0; font-size: 1.8rem; }} h1 span {{ color: {ACCENT}; }}
  h2 {{ font-size: 1.05rem; margin: 0 0 0.8rem; color: #e2e8f0; }}
  .sub {{ color: {MUTED}; margin: 0.6rem 0 1.6rem; line-height: 1.5; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr)); gap: 0.8rem; }}
  .card, section, .notes {{ background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1);
                            border-radius: 1rem; }}
  .card {{ padding: 1rem 1.1rem; }}
  .label {{ color: {MUTED}; font-size: 0.85rem; }}
  .value {{ font-size: 1.7rem; font-weight: 700; margin-top: 0.3rem; font-variant-numeric: tabular-nums; }}
  .notes {{ margin: 1rem 0; padding: 1rem 1.4rem; }}
  .notes ul {{ margin: 0; padding-left: 1.1rem; color: #cbd5e1; line-height: 1.8; }}
  section {{ margin-top: 1rem; padding: 1.2rem 1.4rem; }}
  svg {{ width: 100%; height: auto; display: block; }}
  .tool {{ display: grid; grid-template-columns: 10rem 1fr 4.5rem 4rem 4.5rem; gap: 0.8rem; align-items: center;
           padding: 0.35rem 0; }}
  .tool.head {{ color: {MUTED}; font-size: 0.8rem; }}
  .tool .name {{ font-family: ui-monospace, "JetBrains Mono", monospace; font-size: 0.9rem; overflow: hidden;
                 text-overflow: ellipsis; }}
  .axis {{ display: grid; grid-template-columns: repeat(var(--days), 1fr); margin-top: 0.5rem; color: {MUTED};
           font-size: 0.8rem; }}
  .axis span {{ white-space: nowrap; overflow: visible; text-align: center; }}
  .bar {{ height: 0.6rem; background: rgba(148, 163, 184, 0.12); border-radius: 0.3rem; overflow: hidden; }}
  .bar i {{ display: block; height: 100%; background: linear-gradient(90deg, #0284c7, {ACCENT});
            border-radius: 0.3rem; }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .muted {{ color: {MUTED}; }}
  code {{ font-family: ui-monospace, "JetBrains Mono", monospace; color: {ACCENT}; overflow-wrap: anywhere; }}
  footer {{ margin-top: 1.5rem; color: {MUTED}; font-size: 0.85rem; line-height: 1.6; }}
  footer a {{ color: {ACCENT}; }}
  @media (max-width: 40rem) {{
    .tool {{ grid-template-columns: 9.5rem 1fr 2.6rem 3rem; gap: 0.5rem; }}
    .tool .name {{ font-size: 0.8rem; }}
    .tool > :last-child {{ display: none; }}
    section, .notes {{ padding: 1rem; }}
  }}
</style>
</head>
<body>
<main>
  <div class="head"><img src="/icon.png" alt=""><h1>Finance Database <span>MCP</span> usage</h1></div>
  <p class="sub">Live totals of the hosted server. Users are counted by a keyed one-way hash of their
  address and user agent; nothing per user is published.</p>
  <div class="cards">{card_html}</div>
  {f'<div class="notes"><ul>{notes}</ul></div>' if notes else ""}
  {charts}
  <section><h2>Most used tools</h2>{create_tools_table(summary.get("top_tools") or [], total or 1)}</section>
  <footer>Updates every 5 minutes. The same figures as JSON: <code>curl {escape(json_url)}</code>.<br>
  Set it up yourself: <a href="{escape(website)}">Finance Database MCP</a>.</footer>
</main>
</body>
</html>
"""
