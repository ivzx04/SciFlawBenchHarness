from core.events import AgentEvent

import json
import re

from typing import Dict, List


TOOL_ICONS = {
    "web_search": "🔍",
    "wiki_search": "📚",
    "calculator": "🧮",
    "visit_webpage": "🌐",
    "json_answer": "📦",
}


def extract_concise_trace(events: List[Dict]) -> tuple:
    # TODO: This has to be improved or the CodingAgent, and also checked for other than search and claculator tool
    """
    Extracts a concise trace from the list of AgentEvent objects, summarizing tool and model calls, duraion, and tokens.
    :param events: List[Dict]
    :return: A tuple containing the concise trace, token counts, and duration of the events.
    """

    trace = []
    tokens = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    pending_tool = None

    start_ts = events[0].get("timestamp", 0.0) if events else 0.0
    end_ts = events[-1].get("timestamp", 0.0) if events else 0.0
    duration = round(end_ts - start_ts, 3) if end_ts and start_ts else 0.0

    for e in events:
        t, p = e.get("event_type", ""), e.get("payload") or {}

        if t == "tool_call_start":
            inputs = p.get("kwargs") or (p.get("args")[0] if p.get("args") else {})
            pending_tool = {"tool_name": p.get("name"), "inputs": inputs}
        elif t == "tool_call_end" and pending_tool:
            pending_tool["result"] = p.get("result")
            trace.append(pending_tool)
            pending_tool = None
        elif t == "model_call_end":
            res = p.get("result") or {}
            content = res.get("content", "") if isinstance(res, dict) else str(res)
            trace.append({"event_type": t, "content": content})

            u = res.get("token_usage") or res.get("raw", {}).get("usage") or {}
            tokens["input_tokens"] += u.get("input_tokens", u.get("prompt_tokens", 0)) or 0
            tokens["output_tokens"] += u.get("output_tokens", u.get("completion_tokens", 0)) or 0

    if pending_tool:
        trace.append(pending_tool)

    return trace, tokens, duration


def mermaid_schema(trace, status):
    steps = []
    for x in trace:
        has_error = False
        if x.get("content"):  # omit empty thoughts
            steps.append(("💭", None, has_error))
        elif "tool_name" in x:
            label = TOOL_ICONS.get(x["tool_name"], x["tool_name"])
            inp_key = json.dumps(x.get("inputs"), sort_keys=True)
            res = str(x.get("result") or "").lower()
            has_error = "error" in res
            steps.append((label, inp_key, has_error))

    # Collapse identical consecutive calls
    merged = []
    for label, inp, has_error in steps:
        if inp is not None and merged and merged[-1][:3] == [label, inp, has_error]:
            merged[-1][3] += 1
        else:
            merged.append([label, inp, has_error, 1])

    # Build diagram
    nodes = ["Start"]
    for label, _, has_error, count in merged:
        suffix = f" ×{count}" if count > 1 else ""
        error = "❌ " if has_error else ""
        nodes.append(f"{label}{suffix}{error}")
    nodes.append(f"{status}")

    flow = " -> ".join(nodes)
    return f"```mermaid\n    {flow}\n```"


def get_preview(tool, text):
    preview = ""
    if "search" in tool:
        pattern = r"\[.*?\]\(https?://(?:www\.)?([^\)]+)\)"
        urls = [f"{u.rstrip('/')}" for u in re.findall(pattern, str(text or ""))]
        preview = "**URLs Found:**\n" + ", ".join(urls) + "\n\n" if urls else ""
    if "visit" in tool and text:
        first_lines = "\n> ".join(
            [l.strip() for l in text.split("\n") if l.strip()][:5]
        )
        preview = f"**Snippet**\n> {first_lines}...\n\n"

    details = (
        f"<details>\n"
        f"<summary>Click to expand output ({tool})</summary>\n\n"
        f"```text\n{preview}\n```\n\n"
        f"</details>\n"
    )

    return f"{preview}{details}"


def save_markdown_report(json_path, output_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Top summary section
    trace, tokens, duration = extract_concise_trace(data.get("full_trace", []))
    status = "Passed" if data.get("success") else "Failed"
    token_str = f"in {tokens['input_tokens']:,} | out {tokens['output_tokens']:,}"
    checks = data.get("check_results") or []
    validation_str = checks[0].get("details", "None") if checks else "None"
    diagram_block = mermaid_schema(trace, status)
    legend = " | ".join(f"{icon} {name}" for name, icon in TOOL_ICONS.items())

    md_lines = [
        f"# Task Report #{data.get('task_id', 'N/A')}\n",
        f"**Task:** {data.get('task', '')}\n",
        f"**Final Output:** `{data.get('output', '')}`\n",
        f"**Status:** {status}&emsp;&emsp;&emsp;",
        f"**Duration:** {duration:.2f}&emsp;&emsp;&emsp;",
        f"**Tokens:** {token_str}\n",
        f"**Validation:** {validation_str}\n",
        "\n---\n",
        "## Execution Trace\n",
        f"**Legend:** 💭 Thought | {legend}\n",
        diagram_block,
        "\n---\n",
    ]

    for i, step in enumerate(trace):
        if i > 0:
            md_lines.append("\n---")

        if "content" in step:
            content = str(step.get("content") or "").removeprefix("Thought:").strip()
            if not content:
                md_lines.append("\n> **Model Thought**\n> (No content)\n")
            else:
                body = re.sub(
                    r"<code>\s*([\s\S]*?)\s*</code>",
                    r"\n<details>\n<summary>Click to expand code</summary>\n\n```python\n\1\n```\n</details>\n",
                    content,
                )
                md_lines.append(f"\n> **Model Thought**\n{body}\n")

        elif "tool_name" in step:
            tool = step.get("tool_name", "Tool")
            inputs = json.dumps(step.get("inputs", {}), indent=2)
            result = step.get("result", "")
            if tool == "calculator":
                output_section = f"**Output:** `{result}`\n"
            else:
                output_section = get_preview(tool, result)

            block = (
                f"\n> **Tool Call:** `{tool}`\n\n"
                f">`{inputs}`\n\n"
                f"{output_section}"
            )
            md_lines.append(block)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
