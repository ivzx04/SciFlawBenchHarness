from core.events import AgentEvent

import json
import re

from typing import Dict, List


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

            u = p.get("usage") or res.get("usage") or {}
            tokens["input_tokens"] += u.get("input_tokens", u.get("prompt_tokens", 0)) or 0
            tokens["output_tokens"] += u.get("output_tokens", u.get("completion_tokens", 0)) or 0

    if pending_tool:
        trace.append(pending_tool)

    return trace, tokens, duration


def mermaid_schema(trace, status):
    # Mapping of tool names to unique visual icons
    tool_icons = {
        "web_search": "🔍 Search",
        "wiki_search": "📚 Wiki",
        "calculator": "🧮 Calc",
        "visit_webpage": "🌐 Visit",
        "json_answer": "📦 JsonOutput",
    }

    steps = []
    for x in trace:
        if x.get("content"):  # omit empty thoughts
            steps.append(("💭", None))
        elif "tool_name" in x:
            label = tool_icons.get(x["tool_name"], x["tool_name"])
            inp_key = json.dumps(x.get("inputs"), sort_keys=True)
            steps.append((label, inp_key))

    # Collapse identical consecutive calls
    merged = []
    for label, inp in steps:
        if inp is not None and merged and merged[-1][:2] == [label, inp]:
            merged[-1][2] += 1
        else:
            merged.append([label, inp, 1])

    # Build diagram
    nodes = ["Start"]
    for label, _, count in merged:
        suffix = f" ×{count}" if count > 1 else ""
        nodes.append(f"{label}{suffix}")
    nodes.append(f"Finish {status}")

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

    md_lines = [
        f"# Task Report #{data.get('task_id', 'N/A')}\n",
        f"**Task:** {data.get('task', '')}\n",
        f"**Final Output:** `{data.get('output', '')}`\n",
        f"**Status:** {status}\n",
        f"**Duration:** {duration:.2f}\n",
        f"**Tokens:** {token_str}\n",
        f"**Validation:** {validation_str}\n",
        "\n---\n",
        "## Execution Trace\n",
        diagram_block,
        "\n---\n",
    ]

    for i, step in enumerate(trace):
        if i > 0:
            md_lines.append("\n---")

        if "content" in step:
            thought = step['content']
            if thought:
                thought = f"\n> **Model Thought:**\n> {thought.strip().lstrip('Thought:')}\n"
            else:
                thought = "\n> **Model Thought:**\n> (No content)\n"
            md_lines.append(thought)

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
