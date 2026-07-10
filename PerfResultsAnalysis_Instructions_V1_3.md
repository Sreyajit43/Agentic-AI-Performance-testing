# Performance Test Analysis Instructions for GHCP
**Version:** 3.0 | **Author:** Sreyajit Mondal
**Generic — Applicable to any project | Supports multiple test types per session**
**New in v3.0:** Agent auto-converts whatever raw file you upload (JMeter `statistics.json`, Azure `testRunData.js`, or a raw results CSV) — no manual conversion step or python command needed from the user.

---

## OVERVIEW OF TEST TYPES SUPPORTED

| # | Test Type | Purpose |
|---|-----------|---------|
| 1 | **Baseline test** | Evaluates system performance under normal conditions to establish a performance baseline |
| 2 | **Peakload test** | Determines the system's ability to handle peak or maximum expected load levels |
| 3 | **Capacity/overload test** | Tests the system's limits by exceeding its expected capacity to identify failure points and measure performance degradation |
| 4 | **Endurance test** | Assesses system stability and performance over an extended period under sustained load to detect issues like memory leaks or resource exhaustion |

> **Note:** Not all test types are mandatory for every project.
> - The combination of test types used (for both UI and API) is determined entirely by project requirements.
> - Any of the 4 test types above can be applied to UI, API, or both — there are no restrictions.
> - GHCP must never assume which test types are in scope. The user will specify (or the uploaded files will indicate) which test types are included in the current session.

---

## REQUIRED COMPANION SCRIPTS

Place these two files in the **same VS Code workspace folder** as this
instructions file — GHCP's agent mode calls them directly in Step 0, you
never run them by hand:

- `convert_csv_to_json.py`
- `convert_alt_to_json.py`

> Requires GHCP agent mode with terminal/file-write permission enabled. Without it, GHCP can only show you the command to run rather than execute it itself.

---

## ACCEPTED INPUT FILES

GHCP now accepts **any** of the following per test run — conversion to the
target JSON format happens automatically in Step 0, before any comparison
logic runs:

| Source | What You Upload | Auto-Converted With |
|---|---|---|
| Local JMeter run | `statistics.json` (from `dashboard/` folder of JMeter HTML report) | Already in target format — used as-is |
| Local JMeter run (no HTML report generated) | raw `results.csv` | `convert_csv_to_json.py` |
| Azure Load Testing HTML report (downloaded zip) | `data/testRunData.js` | `convert_alt_to_json.py` |
| Azure Load Testing raw engine CSV | `engine1_results.csv` (or similarly named) | `convert_csv_to_json.py` |

You never need to run these scripts yourself or convert anything by hand —
just upload the raw file(s) you have, in whatever mix. The agent detects
the type and converts each one in Step 0.

## FILE NAMING CONVENTION

Once converted (or if already in JSON form), files are named/paired using
this pattern so GHCP can automatically match them by test type:

**Legacy (Baseline environment) files:**
```
Legacy_Baseline.json
Legacy_PeakLoad.json
Legacy_Capacity.json
Legacy_Endurance.json
```

**Current (Target environment) files:**
```
Current_Baseline.json
Current_PeakLoad.json
Current_Capacity.json
Current_Endurance.json
```

> GHCP must pair files that share the same test type suffix: `Legacy_Baseline.json` ↔ `Current_Baseline.json`, and so on.
> If a raw file's name doesn't indicate Legacy/Current or test type, the agent infers it from the parent folder path where possible, and only asks you directly as a last resort (see Step 0).

---

## STEP 0 — FILE INTAKE & AUTO-CONVERSION *(Agent-run — no user action required)*

Before any comparison logic runs, for every file the user attaches:

1. **Detect the file type:**
   - `.json` with transaction entries containing `meanResTime` / `errorPct` / `sampleCount` → already in target format, use as-is.
   - `.js` file (typically `testRunData.js`, or starting with `window.testRunData = `) → Azure Load Testing export.
     Run: `python convert_alt_to_json.py <file> <output.json>`
   - `.csv` with columns including `timeStamp`, `elapsed`, `label`, `success` → JMeter raw results CSV or Azure raw engine CSV (same schema).
     Run: `python convert_csv_to_json.py <file> <output.json>`
   - Anything else → tell the user the file type isn't recognized and ask for a `statistics.json`, `testRunData.js`, or raw results CSV instead.

2. **Infer Legacy/Current and test type** from the filename or parent folder
   (e.g. a folder named `Current\Peakload\...`, or a file called
   `Legacy_Baseline.csv`). Only ask directly when it truly can't be inferred:
   ```
   Is "<filename>" the Legacy/Baseline run or the Current/UAT-B run, and
   which test type (Baseline / Peakload / Capacity / Endurance) is it?
   ```

3. **Name the converted output** using the File Naming Convention above so
   Step 1 can auto-pair it.

4. **Confirm what was found**, once, before moving on:
   ```
   ✅ Converted and paired:
     - Baseline  : Legacy_Baseline.json  ↔ Current_Baseline.json
     - Peakload  : Legacy_PeakLoad.json  ↔ Current_PeakLoad.json (converted from CSV)
     - Capacity  : Current-side file missing — skipping this test type

   Proceeding to comparison scope selection...
   ```

If every file attached is already valid target-format JSON named per
convention, this step completes silently with just the confirmation
message — no conversion needed.

---

## STEP 0.5 — CHOOSE COMPARISON SCOPE

Before processing any files, always ask the user which scope applies to this session:

```
How would you like to compare these results?

1. Full comparison — analyze ALL transactions found in the uploaded files
2. Specific transaction(s) only — compare just the transaction(s) you name,
   even if Legacy and Current use different names for the same step
```

> If the user already stated their intent in the same message that attached the files (e.g., "I just want to compare PSOSInq- Event log page vs Open PSOreder&ShipInq"), skip this question and go directly into the matching mode below.

---

### MODE A — Full Comparison

Proceed to **Step 1 (File Validation)** as normal. Every transaction in the uploaded JSON pairs is validated and included in the comparison tables. If label mismatches are found, **Step 1.5** applies.

---

### MODE B — Specific Transaction(s) Only

Use this mode when the user wants to compare one or a few named transactions directly — including cases where the transaction was renamed between Legacy and Current and the user already knows the mapping.

**1. Skip full-file validation.** There is no need to check that every label in the file matches — only the specifically requested transaction(s) need to exist.

**2. Collect the transaction(s) to compare**, in this format:

```
Which transaction(s) would you like to compare?

For each one, provide:
  - Legacy transaction name (exact, as it appears in Legacy_*.json)
  - Current transaction name (same as Legacy if unchanged; different if renamed)
  - Test type(s) it applies to → Baseline / Peakload / Capacity / Endurance / All
```

Example of how the user may phrase this directly:
```
PSOSInq- Event log page (Legacy) = Open PSOreder&ShipInq (Current) — Baseline and Peakload
```

**3. Locate and validate only the named transaction(s):**
- Search for the Legacy name in the relevant `Legacy_*.json` file(s) and the Current name in the matching `Current_*.json` file(s), for each requested test type.
- If a named transaction is **not found** in either file, report it clearly:
  ```
  ⚠️ Could not find "[name]" in [filename]. Please verify the exact transaction
  name as it appears in the JSON (case-sensitive).
  ```
  Do not guess or fuzzy-match — ask the user to confirm the exact name.
- If found in both files for the requested test type(s), proceed to build the comparison table using **only** that transaction (or transactions, if multiple were requested) — all other transactions in the files are ignored for this session.

**4. Multiple specific transactions in one session:** the user may request several individually named transactions (each with its own Legacy↔Current mapping) — repeat steps 1–3 for each, and include all of them together in the same output table(s).

**5. Skip Step 1.5** in this mode — since the user has already explicitly confirmed the name mapping for the transaction(s) they care about, there is no need for a separate mapping confirmation step.

**6. Proceed directly to Step 2 (metadata collection)**, then Step 3 (table generation) — using only the requested transaction(s) instead of the full transaction set.

---

## STEP 1 — FILE VALIDATION  *(Mode A — Full comparison only)*

- Identify all uploaded JSON files.
- Auto-detect which test types are present by reading the filenames.
- For each detected pair (Legacy_X.json + Current_X.json), confirm:
  - Both files are valid JMeter `statistics.json` format.
  - Each transaction entry contains: `meanResTime`, `errorPct`, `sampleCount`, `throughput`.
  - Both files in a pair cover the same set of transaction labels.
- If any file fails validation, report the specific issue and pause before proceeding.
- On success, report:

```
✅ Validation Complete

Detected test type pairs:
  - Baseline    : Legacy_Baseline.json    ↔ Current_Baseline.json    ✅
  - Peakload    : Legacy_PeakLoad.json    ↔ Current_PeakLoad.json    ✅
  - Capacity    : Legacy_Capacity.json    ↔ Current_Capacity.json    ✅
  - Endurance   : Legacy_Endurance.json   ↔ Current_Endurance.json   ✅

Total pairs to analyze: [N]
Proceeding to metadata collection...
```

---

## STEP 1.5 — TRANSACTION LABEL MAPPING  *(Mode A — Full comparison only; skipped entirely in Mode B)*

It is common for Legacy and Current environment scripts to use **different transaction names** for the same logical step, especially after migration or script rewrites (e.g., renamed pages, restructured flows, different recording tools).

**If the transaction label sets in a pair do not match exactly:**

1. Do **not** halt the entire session. Report the mismatch clearly per pair:

```
⚠️ Label mismatch detected — [Test Type] pair

Legacy labels:
  - [label 1]
  - [label 2]
  ...

Current labels:
  - [label 1]
  - [label 2]
  ...

These labels do not match 1:1. I cannot assume which Legacy label corresponds
to which Current label — please confirm the mapping below.
```

2. **Never auto-guess the mapping**, even if labels look similar (e.g., "Redirect to applications page" vs. "Navigate to applications page" may or may not be the same step). Always ask the user to confirm.

3. Ask the user to provide the mapping in this format:

```
Please confirm the transaction mapping for [Test Type]:

Legacy Label                          ↔  Current Label
-----------------------------------------------------
[Legacy label]                        ↔  [Current label]
[Legacy label]                        ↔  [Current label]
[Legacy label]                        ↔  [No match — exclude from comparison]
```

4. Once the user confirms the mapping, apply it consistently:
   - Use the **Legacy label** as the canonical `Label` name in all comparison tables (this keeps naming consistent across cycles even if Current-side scripts get renamed again later).
   - Any Legacy or Current label explicitly marked **"no match — exclude"** is left out of the comparison table entirely and listed separately under a "Excluded transactions (no match found)" note below the table.
   - If a mapping was already confirmed earlier in this same session, reuse it automatically for any later test type pair with the same labels — don't re-ask for an already-confirmed mapping.

5. Once mapping is resolved for all pairs (or confirmed not needed), proceed to Step 2.

> **Tip for the user:** If your Legacy and Current scripts consistently use different naming conventions across projects, you can pre-confirm the mapping at the start of the session (before GHCP even asks) by pasting it directly after attaching files. GHCP will use it instead of stopping to ask.

---

## STEP 2 — COLLECT SESSION METADATA

Ask the user for the following details **once per session** (not per test type). These apply to all test types in the current session:

```
1. Project / Application Name        → e.g., PDC Dealer Daily - PSMasterInq
2. Testing Category                  → UI or API (or both, if mixed)
3. Testing Environment               → e.g., UAT
4. Baseline Environment Label        → e.g., Legacy, UAT-L, On-Prem
5. Target Environment Label          → e.g., UAT-B, Azure UAT
6. UI SLA Threshold (ms)             → e.g., 10000 (for 10 seconds)
7. Application URL                   → e.g., https://app-uat.company.com
8. Cycle Number                      → e.g., Cycle 1, Cycle 2 [Optional]
```

Then ask for **per test type details** (load profile + execution date) for each detected test type:

```
For each test type detected, collect:
  a. Load Profile  → e.g., 10 concurrent users, 100s ramp-up, 5 req/min, 1-hour hold
  b. Execution Date → DD/MM/YYYY
```

**Example prompt to user:**
```
I found [N] test type pairs. Please provide the load profile and execution date for each:

1. Baseline test     → Load profile: _____  | Execution date: _____
2. Peakload test     → Load profile: _____  | Execution date: _____
3. Capacity test     → Load profile: _____  | Execution date: _____
4. Endurance test    → Load profile: _____  | Execution date: _____
```

> If the user provides only partial metadata, ask for the missing fields before proceeding.

---

## STEP 3 — GENERATE COMPARISON TABLES (PER TEST TYPE)

Process each test type pair **sequentially** in this order: Baseline → Peakload → Capacity → Endurance.

For **each test type**, generate a section with the following structure:

---

### Section Header

```
═══════════════════════════════════════════════════════════
[N]. [TEST TYPE NAME] TEST — [Project / App Name]
Load profile: [Load Profile]
Execution date: [DD/MM/YYYY]
═══════════════════════════════════════════════════════════
```

### Comparison Table

Build the table in **exactly** this column order:

| Label | Average Response Time (ms) | | Error % | | Performance Change (ms) | % Performance Change |
|-------|:--------------------------:|:---:|:-------:|:---:|:----------------------:|:--------------------:|
| | **[Baseline Label]** | **[Target Label]** | **[Baseline Label]** | **[Target Label]** | | |
| [Transaction Name] | [Legacy meanResTime] | [Current meanResTime] | [Legacy errorPct] | [Current errorPct] | [Change ms] | [% Change] |

### Column Calculation Rules

| Column | Formula | Notes |
|--------|---------|-------|
| **Label** | Transaction name from JSON (or confirmed Legacy-side label from Step 1.5 mapping, if applicable) | Exclude `TOTAL` from main table; show separately as "Overall". Exclude any transaction marked "no match" in Step 1.5 |
| **Avg RT — Baseline** | `meanResTime` from Legacy JSON | In milliseconds |
| **Avg RT — Target** | `meanResTime` from Current JSON | In milliseconds |
| **Error % — Baseline** | `errorPct` from Legacy JSON | Format: `X.XX%` |
| **Error % — Target** | `errorPct` from Current JSON | Format: `X.XX%` |
| **Performance Change (ms)** | `Legacy meanResTime − Current meanResTime` | Positive = Improved; Negative = Degraded |
| **% Performance Change** | `(Legacy meanResTime / Current meanResTime) − 1` | Format: `X.XX%`; Positive = Improved; Negative = Degraded |

### Per-Test-Type Summary Block

After each table, show:

```
Summary — [Test Type]:
  ✅ Improved  : [N] transactions
  ❌ Degraded  : [N] transactions
  ➖ No Change : [N] transactions
  ⚠️  Errors   : [N] transactions (Error % > 0 in target)
  📊 Total     : [N] transactions (excluding TOTAL aggregate)
  🏆 Best improvement  : [Transaction] — improved by [X] ms ([Y]%)
  ⚠️  Worst degradation: [Transaction] — degraded by [X] ms ([Y]%)
```

---

## STEP 4 — CONSOLIDATED SUMMARY (ACROSS ALL TEST TYPES)

After all per-test-type sections are complete, generate a consolidated summary:

```
╔══════════════════════════════════════════════════════════╗
  CONSOLIDATED PERFORMANCE SUMMARY — [Project / App Name]
  Environment: [Baseline Label] → [Target Label]
╚══════════════════════════════════════════════════════════╝

| Test Type   | Improved | Degraded | No Change | Errors | Overall Verdict |
|-------------|----------|----------|-----------|--------|-----------------|
| Baseline    | [N]      | [N]      | [N]       | [N]    | ✅ / ❌ / ⚠️     |
| Peakload    | [N]      | [N]      | [N]       | [N]    | ✅ / ❌ / ⚠️     |
| Capacity    | [N]      | [N]      | [N]       | [N]    | ✅ / ❌ / ⚠️     |
| Endurance   | [N]      | [N]      | [N]       | [N]    | ✅ / ❌ / ⚠️     |

Overall Verdict Rules:
  ✅ Improved  → Majority (>60%) of transactions improved, no new errors
  ❌ Degraded  → Any transaction degraded >30%, or new errors introduced
  ⚠️ Mixed     → Mix of improvements and degradations
```

---

## STEP 5 — SLA ANALYSIS (PER TEST TYPE + COMBINED)

For each test type, compare **Target (Current) Average Response Time** against the SLA threshold:

```
SLA Threshold: [X] ms

[Test Type] — SLA Status:
  ❌ Breaches ([N]):
     - [Transaction]: [Current ms] ms  (+[Overage] ms over SLA)
  ✅ Passed ([N]):
     - [Transaction]: [Current ms] ms
  🔴 Worst performer: [Transaction] at [ms] ms ([X]% over threshold)
```

After all test types, generate a **Combined SLA Summary**:

```
SLA COMPLIANCE ACROSS ALL TEST TYPES:
  | Transaction | Baseline | Peakload | Capacity | Endurance | Status |
  |-------------|----------|----------|----------|-----------|--------|
  | [Name]      | ✅/❌     | ✅/❌    | ✅/❌    | ✅/❌     | Pass/Fail |
```

Flag: If a transaction **fails SLA in all test types**, mark it as **Critical — requires immediate investigation**.

---

## STEP 6 — AI-DRIVEN INSIGHTS (PER TEST TYPE + CONSOLIDATED)

### Per Test Type Insights
For each test type, generate:

**🟢 Top Improvements**
- Transaction name | Baseline → Target | ms change | % improvement
- What the improvement indicates (infrastructure, code efficiency, etc.)

**🔴 Degradations — Action Required**
- Transaction name | Baseline → Target | ms change | % degradation
- Severity: Critical (>30% degradation) | Moderate (10–30%) | Minor (<10%)
- Suggested investigation area

**⚠️ Error Rate Changes**
- Highlight new errors (0% → X%) or error rate increases

**📌 Pattern Observations**
- Are degradations isolated to one transaction or systemic?
- Do degradations appear only in high-load test types (Capacity, Endurance) vs. Baseline?

### Consolidated Recommendations
After all test types, provide **top 5 prioritized recommendations** across the entire session:

```
PRIORITIZED RECOMMENDATIONS:
1. [Critical — e.g., fix degraded transaction that fails across all test types]
2. [High — e.g., investigate new errors introduced in Peakload]
3. [Medium — e.g., SLA breach in Capacity test for specific transaction]
4. [Low — e.g., minor degradations to monitor in next cycle]
5. [Observation — e.g., overall migration shows X% average improvement]
```

---

## STEP 7 — EMAIL REPORT GENERATION

**Only generate when the user explicitly says:**
`"write the mail"` / `"draft the email"` / `"generate email report"`

Use **exactly** the following structure. Each test type gets its own numbered section with load profile, date, and comparison table.

---

**Subject:** [Project Name] - [App Name] - Performance test execution [cycle number]

---

Hi Team,

We have completed the execution of performance scripts for **[Project Name] - [App Name]** in the **[Testing Environment]** environment, details of which are as follows:

**Summary of Performance Test:**

Testing Environment: [Testing Environment]
Objective: To establish performance measurement by conducting performance tests on the application post-migration from [Baseline Label] environment to [Target Label] environment.
UI SLA: Average Response time should be less than [SLA Threshold in seconds].
[App Name] UI – [App URL]

**Performance Metrics:**

> Note to GHCP: Include only the test type sections that match the uploaded files. Number them sequentially (1, 2, 3…) based on what is present. Do not include sections for test types not uploaded. Do not assume any test type is mandatory or optional.

**1. Baseline test:**
Load profile – [Baseline load profile]
Execution date: [DD/MM/YYYY]

[INSERT BASELINE COMPARISON TABLE]

**2. Peakload test:**
Load profile – [Peakload load profile]
Execution date: [DD/MM/YYYY]

[INSERT PEAKLOAD COMPARISON TABLE]

**3. Capacity/overload test:**
Load profile – [Capacity load profile]
Execution date: [DD/MM/YYYY]

[INSERT CAPACITY COMPARISON TABLE]

**4. Endurance test:**
Load profile – [Endurance load profile]
Execution date: [DD/MM/YYYY]

[INSERT ENDURANCE COMPARISON TABLE]

**Resource Utilization for [Target Environment] –**

[📸 Placeholder: Insert CPU / Memory / DTU screenshot here]

DTU / CPU / Memory –

**Observations –**
[2–4 sentence AI-generated summary covering: overall migration result, which test types showed most improvement, any degraded endpoints, SLA compliance status, and any @mentions if stakeholder names were provided by user.]

Best regards,
Sreyajit

---

### Email Rules

- Include **only the test types that were analyzed** in the current session — skip sections for test types not uploaded
- Number sections sequentially based on test types present (don't leave gaps in numbering)
- Leave `[📸 Placeholder]` for all monitoring screenshots — never fabricate resource data
- Use `@[Name]` if the user provides stakeholder names for observations
- Keep tone professional and concise — match the writing style above exactly
- If cycle number is unknown, use `"latest cycle"` as fallback

---

## STEP 8 — FOLLOW-UP QUERY HANDLING

After the full analysis, respond to natural language follow-up prompts:

| User Prompt | Action |
|-------------|--------|
| `"Show degraded APIs across all test types"` | Cross-reference all tables, list transactions degraded in 1 or more test types |
| `"Which transactions fail SLA in all test types?"` | Cross-check SLA analysis across all test type sections |
| `"Compare Baseline vs Peakload degradation patterns"` | Side-by-side insight on how load increase affected results |
| `"Write the mail now"` | Execute Step 7 |
| `"Export all results to CSV"` | Output all 4 tables as CSV sections, labelled by test type |
| `"Show only Endurance results"` | Return only the Endurance section |
| `"Which test type performed best overall?"` | Compare consolidated summary rows, return verdict |
| `"Summarize in 5 lines"` | Return a 5-sentence executive summary across all test types |
| `"Get me [Transaction] across all test types"` | Return that transaction's row from every test type table |
| `"Are there any transactions that degraded in every test type?"` | Cross-reference all tables and flag consistent degradations |
| `"Now just compare [Legacy name] vs [Current name]"` | Switch to Mode B for this follow-up — locate and compare only the named transaction(s), even mid-session |
| `"Add [transaction] to the comparison too"` | Locate the named transaction (ask for Current-side name if renamed) and append it to the existing output |

---

## FIELD REFERENCE — JMeter statistics.json

| JSON Field | Meaning | Used In |
|------------|---------|---------|
| `transaction` | API / transaction label | Label column |
| `meanResTime` | Average response time (ms) | Avg Response Time columns |
| `errorPct` | Error percentage | Error % columns |
| `sampleCount` | Total requests | Validation / context |
| `throughput` | Requests per second | Optional — include if asked |
| `pct1ResTime` | 90th percentile (ms) | Optional follow-up metric |
| `pct2ResTime` | 95th percentile (ms) | Optional follow-up metric |
| `pct3ResTime` | 99th percentile (ms) | Optional follow-up metric |
| `minResTime` | Minimum response time | Optional |
| `maxResTime` | Maximum response time | Optional |

---

## GENERAL RULES

1. **Always run file intake/auto-conversion first (Step 0), then determine comparison scope (Step 0.5)** — Mode A (full) validates all pairs before proceeding; Mode B (specific transaction) skips full-file validation and works only with the named transaction(s)
2. **Collect all metadata before analyzing** — never proceed with placeholder names
3. **Never fabricate data** — if a JSON field is missing, state it explicitly
4. **Process test types in order**: Baseline → Peakload → Capacity → Endurance
5. **Table column order is fixed**: Label → Avg RT [Legacy | Current] → Error % [Legacy | Current] → Change (ms) → % Change
6. **Performance Change formula**: `Legacy meanResTime − Current meanResTime`
   - Positive = Target is **faster** = ✅ Improvement
   - Negative = Target is **slower** = ❌ Degradation
7. **% Performance Change formula**: `(Legacy meanResTime / Current meanResTime) − 1`
   - This is the exact equivalent of the Excel formula `=B3/C3-1`
8. **Do not generate email unless explicitly asked**
9. **Show Consolidated Summary (Step 4) after all test types** — Mode A only; not applicable in Mode B unless multiple test types were explicitly requested for the same transaction
10. **In Mode B, never auto-match renamed transactions** — only use the exact Legacy↔Current name pairing the user provides
11. **This file is generic** — works for any project, any environment labels, any combination of test types, and any comparison scope (full or specific)
