"""Web search tool backed by DuckDuckGo (no API key required)."""
from __future__ import annotations

MAX_RESULTS = 5
MAX_OUTPUT = 4000


def run(args: dict) -> str:
    query = (args.get("query") or args.get("q") or "").strip()
    if not query:
        return "❌ search tool: missing 'query' parameter."

    try:
        from ddgs import DDGS  # type: ignore
    except ImportError:
        return (
            "❌ search tool: the 'ddgs' package is not installed. "
            "Install it with `pip install ddgs`."
        )

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=MAX_RESULTS))
    except Exception as exc:
        return f"❌ search tool error: {exc}"

    if not results:
        return f"(no results for {query!r})"

    lines = [f"Top {len(results)} results for: {query}"]
    for i, r in enumerate(results, 1):
        title = r.get("title", "(no title)")
        href = r.get("href") or r.get("url") or ""
        body = (r.get("body") or "").strip()
        lines.append(f"\n[{i}] {title}\n    {href}\n    {body}")

    out = "\n".join(lines)
    if len(out) > MAX_OUTPUT:
        out = out[:MAX_OUTPUT] + f"\n…[truncated, {len(out) - MAX_OUTPUT} bytes more]"
    return out
