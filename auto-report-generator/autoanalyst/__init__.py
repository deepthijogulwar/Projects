"""Auto-Analyst: turn a sales CSV into a full written report, automatically.

Pipeline modules:
    metrics    -> compute KPIs, trends, top segments, loss-makers, anomalies
    charts     -> render the report's charts as PNGs
    narrative  -> write the plain-English executive summary (LLM or template)
    report     -> assemble everything into a Markdown report
"""
