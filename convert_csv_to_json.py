#!/usr/bin/env python3
"""
convert_csv_to_json.py

Converts a raw JMeter results CSV (or Azure Load Testing raw engine CSV,
which uses the same column schema) into a statistics.json-style file
compatible with PerfResultsAnalysis_Instructions.md.

Usage:
    python convert_csv_to_json.py <input.csv> <output.json>

Expected CSV columns (JMeter default / Azure raw engine CSV):
    timeStamp, elapsed, label, responseCode, responseMessage,
    threadName, dataType, success, failureMessage, bytes, sentBytes,
    grpThreads, allThreads, URL, Latency, IdleTime, Connect
Only timeStamp, elapsed, label, success are required — extra columns
are ignored, missing optional columns are tolerated.
"""

import csv
import json
import sys
import statistics as stats
from collections import defaultdict


def to_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def build_stats(label, elapsed_list, error_count):
    sorted_vals = sorted(elapsed_list)
    sample_count = len(elapsed_list)
    mean_res = round(stats.mean(elapsed_list), 2) if elapsed_list else 0.0
    median_res = round(stats.median(elapsed_list), 2) if elapsed_list else 0.0
    min_res = round(min(elapsed_list), 2) if elapsed_list else 0.0
    max_res = round(max(elapsed_list), 2) if elapsed_list else 0.0
    error_pct = round((error_count / sample_count) * 100, 2) if sample_count else 0.0
    return {
        "transaction": label,
        "sampleCount": sample_count,
        "errorCount": error_count,
        "errorPct": error_pct,
        "meanResTime": mean_res,
        "medianResTime": median_res,
        "minResTime": min_res,
        "maxResTime": max_res,
        "pct1ResTime": round(percentile(sorted_vals, 90), 2),
        "pct2ResTime": round(percentile(sorted_vals, 95), 2),
        "pct3ResTime": round(percentile(sorted_vals, 99), 2),
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_csv_to_json.py <input.csv> <output.json>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    per_label_elapsed = defaultdict(list)
    per_label_errors = defaultdict(int)
    all_elapsed = []
    all_errors = 0
    total_rows = 0

    try:
        with open(input_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                label = row.get("label", "").strip()
                if not label:
                    continue
                try:
                    elapsed = float(row.get("elapsed", 0))
                except ValueError:
                    continue
                success = to_bool(row.get("success", "true"))

                per_label_elapsed[label].append(elapsed)
                all_elapsed.append(elapsed)
                total_rows += 1
                if not success:
                    per_label_errors[label] += 1
                    all_errors += 1
    except FileNotFoundError:
        print(f"❌ File not found: {input_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to read CSV: {e}")
        sys.exit(1)

    if total_rows == 0:
        print("❌ No valid data rows found — check the CSV has 'label', 'elapsed', 'success' columns.")
        sys.exit(1)

    result = {}
    for label, elapsed_list in per_label_elapsed.items():
        result[label] = build_stats(label, elapsed_list, per_label_errors[label])

    result["Total"] = build_stats("Total", all_elapsed, all_errors)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print("✅ Conversion successful!")
    print(f"   Transactions  : {len(result) - 1} (+ Total)")
    print(f"   Overall Avg RT: {result['Total']['meanResTime']} ms")
    print(f"   Overall Error%: {result['Total']['errorPct']}%\n")
    for label, s in result.items():
        if label == "Total":
            continue
        print(f"   {label:<30} {s['sampleCount']:>4} samples   {s['meanResTime']:>8} ms   {s['errorPct']}%")


if __name__ == "__main__":
    main()
