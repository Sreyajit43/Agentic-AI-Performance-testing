#!/usr/bin/env python3
"""
convert_alt_to_json.py

Converts Azure Load Testing's data/testRunData.js (extracted from the
downloaded HTML report zip) into a statistics.json-style file compatible
with PerfResultsAnalysis_Instructions.md.

Azure wraps its stats as:  window.testRunData = { ...json... };
This strips the wrapper and remaps fields to JMeter's statistics.json
field names so both sources can be compared with the same instructions file.

Usage:
    python convert_alt_to_json.py <path/to/testRunData.js> <output.json>
"""

import json
import re
import sys


FIELD_MAP = {
    "meanResTime": ["meanResTime", "avgResTime", "mean"],
    "medianResTime": ["medianResTime", "median"],
    "minResTime": ["minResTime", "min"],
    "maxResTime": ["maxResTime", "max"],
    "pct1ResTime": ["pct1ResTime", "p90"],
    "pct2ResTime": ["pct2ResTime", "p95"],
    "pct3ResTime": ["pct3ResTime", "p99"],
    "sampleCount": ["sampleCount", "count", "totalRequests"],
    "errorCount": ["errorCount", "errors"],
    "errorPct": ["errorPct", "errorPercentage"],
    "throughput": ["throughput", "rps"],
}


def first_present(d, keys, default=0):
    for k in keys:
        if k in d:
            return d[k]
    return default


def normalize_entry(name, raw):
    entry = {"transaction": name}
    for out_key, candidates in FIELD_MAP.items():
        entry[out_key] = first_present(raw, candidates, 0)

    # Derive errorPct if only counts are present
    if not entry.get("errorPct") and entry.get("sampleCount"):
        entry["errorPct"] = round((entry.get("errorCount", 0) / entry["sampleCount"]) * 100, 2)

    return entry


def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_alt_to_json.py <testRunData.js> <output.json>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    # Strip "window.testRunData = " wrapper and trailing semicolon
    match = re.search(r"window\.testRunData\s*=\s*(\{.*\})\s*;?\s*$", raw_text, re.DOTALL)
    json_text = match.group(1) if match else raw_text.strip().rstrip(";")

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        print(f"❌ Could not parse testRunData.js as JSON: {e}")
        sys.exit(1)

    # testRunStatistics is usually a dict keyed by request/transaction name
    stats_block = data.get("testRunStatistics", data)

    result = {}
    all_names = []
    for name, raw in stats_block.items():
        if not isinstance(raw, dict):
            continue
        result[name] = normalize_entry(name, raw)
        all_names.append(name)

    if not result:
        print("❌ No transaction statistics found in testRunStatistics block.")
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    total_entry = result.get("Total") or result.get("total")
    print("✅ Conversion successful!")
    if total_entry:
        print(f"   Test run name   : {data.get('testName', 'N/A')}")
        print(f"   Transactions    : {len(result) - 1} (+ Total)")
        print(f"   Overall Avg RT  : {total_entry['meanResTime']} ms")
        print(f"   Overall Error % : {total_entry['errorPct']}%\n")
    print("   Transactions found:")
    for name in all_names:
        s = result[name]
        print(f"     - {name:<30} Avg RT: {s['meanResTime']:>8} ms  |  Error%: {s['errorPct']}%")


if __name__ == "__main__":
    main()
