"""Assemble the KPIs, summary, and charts into a single Markdown report."""


def build_markdown(kpis, summary, charts, top_region, top_category):
    period = f"{kpis['start']:%b %Y} - {kpis['end']:%b %Y}"
    lines = [
        "# 📈 Automated Sales Report",
        "",
        f"*Auto-generated from {kpis['rows']:,} records · period: {period}.*",
        "",
        "## Executive summary",
        "",
        summary,
        "",
        "## Key numbers",
        f"- **Total sales:** ${kpis['total_sales']:,.0f}",
        f"- **Total profit:** ${kpis['total_profit']:,.0f}",
        f"- **Profit margin:** {kpis['margin']:.1%}",
        f"- **Top region:** {top_region}",
        f"- **Top category (sales):** {top_category}",
        "",
        "## Charts",
        "",
    ]
    for title, filename in charts:
        lines += [f"### {title}", "", f"![{title}]({filename})", ""]
    return "\n".join(lines)
