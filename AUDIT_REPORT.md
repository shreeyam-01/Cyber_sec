# AUDIT REPORT: Phase 1 + Phase 2 Unseen-CWE Evaluation & Generalization Pipeline

**Audit Date:** October 22, 2026  
**Audited Artifacts:**
- Phase 1 Dataset: `D:\cybersec\mnt\agents\output\dataset\processed\dataset.json` (6,716 records / 13,432 samples)
- Phase 1 Results & Predictions: `D:\cybersec_2\results\llm_static_framework_results.json`, `predictions_seen.json`, `predictions_unseen.json`
- Phase 2 Dataset: `D:\cybersec_2\phase2_dataset\phase2_dataset.json` (7,831 records / 15,560 samples)
- Phase 2 Results: `D:\cybersec_2\phase2_results\phase2_results.json`
- Phase 2 Checkpoints: `D:\cybersec_2\phase2_checkpoints\best_phase2_model.pt`, static feature caches, LLM embedding tensors
- Visual Charts: `D:\cybersec_2\combined_figures\unseen_cwe_breakdown_combined_phase1_2.png`

---

## Executive Summary
This audit evaluated the data integrity, leakage prevention protocols, sample distributions, metric computations, and 100% metric occurrences for all 25 held-out (unseen) CWE categories across Phase 1 and Phase 2.

**Key Findings:**
1. **Strict Zero-Leakage:** All 25 held-out CWE categories (5 in Phase 1, 20 in Phase 2) were **100% excluded** from training sets and validation tuning sets. There is 0 class overlap between training and held-out test splits.
2. **Metrics Mathematically Verified:** Recalculations of Recall, Precision, F1-Score, and False Positive Rate directly from saved predictions (Phase 1) and model checkpoint weights (Phase 2) match the reported figures with **zero discrepancy**.
3. **Artifact Sanitization Quality:** Function signatures (`_bad`, `_good`), preprocessor directives (`#ifndef OMITBAD/OMITGOOD`), and comments (`FLAW`, `FIX`) were purged.
4. **Subtle Juliet Structural Duplication:** While non-trivial function bodies across distinct CWE classes do not duplicate logic, Juliet's synthetic test harness uses standard socket/file-reading wrappers that share identical source setup code across 18 functions between Phase 2 training and held-out sets (e.g., standard `WSADATA` socket connection boilerplate in CWE-114 vs. CWE-606).
5. **Missing File Identified:** While Phase 1 saved individual sample prediction records (`predictions_seen.json`, `predictions_unseen.json`), Phase 2 only saved aggregated metrics in `phase2_results.json`. The individual sample-level prediction file for Phase 2 was reconstructed and validated directly against `best_phase2_model.pt`.

---

## Audit Point 1: Exact Number of Training, Validation, and Test Samples per CWE

Each Juliet record consists of a vulnerable function (`Label 1`) and an accompanying fixed counter-sample (`Label 0`, when available).

### Phase 1 (20 Core CWEs) — Total Samples: 13,432 (6,716 Records)
*Every record has a paired fixed counterpart (100% paired).*

| CWE Category | Split Group | Train Samples | Val Samples | Test Seen Samples | Test Held-Out Samples | Total Samples |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **CWE-121** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-122** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-124** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-126** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-127** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-190** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-191** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-194** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-195** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-197** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-369** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-415** | Seen | 470 | 102 | 100 | 0 | 672 |
| **CWE-416** | Seen | 210 | 46 | 44 | 0 | 300 |
| **CWE-457** | Seen | 560 | 120 | 120 | 0 | 800 |
| **CWE-476** | Seen | 520 | 112 | 112 | 0 | 744 |
| **CWE-123** | **Held-Out** | **0** | **0** | **0** | **336** | **336** |
| **CWE-134** | **Held-Out** | **0** | **0** | **0** | **800** | **800** |
| **CWE-188** | **Held-Out** | **0** | **0** | **0** | **72** | **72** |
| **CWE-253** | **Held-Out** | **0** | **0** | **0** | **800** | **800** |
| **CWE-327** | **Held-Out** | **0** | **0** | **0** | **108** | **108** |
| **P1 Total** | — | **7,920** | **1,698** | **1,698** | **2,116** | **13,432** |

---

### Phase 2 (89 Remaining CWEs) — Total Samples: 15,560 (7,831 Records)

#### A. 20 Held-Out (Unseen) CWEs in Phase 2 (4,476 Samples / 2,272 Records)
*Note: In CWE-506, fixed counterparts are absent in Juliet (malicious code has no benign variant).*

| Held-Out CWE Category | Description | Train | Val | Test Seen | Test Held-Out | Total Samples |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **CWE-78** | OS Command Injection | 0 | 0 | 0 | 400 | 400 |
| **CWE-90** | LDAP Injection | 0 | 0 | 0 | 400 | 400 |
| **CWE-114** | Process Control | 0 | 0 | 0 | 400 | 400 |
| **CWE-256** | Plaintext Password Storage | 0 | 0 | 0 | 224 | 224 |
| **CWE-259** | Hardcoded Password | 0 | 0 | 0 | 224 | 224 |
| **CWE-272** | Least Privilege Violation | 0 | 0 | 0 | 400 | 400 |
| **CWE-273** | Dropped Privileges Check Omission | 0 | 0 | 0 | 72 | 72 |
| **CWE-284** | Improper Access Control | 0 | 0 | 0 | 400 | 400 |
| **CWE-319** | Cleartext Transmission of Sensitive Data | 0 | 0 | 0 | 400 | 400 |
| **CWE-321** | Hardcoded Cryptographic Key | 0 | 0 | 0 | 224 | 224 |
| **CWE-328** | Reversible One-Way Hash | 0 | 0 | 0 | 108 | 108 |
| **CWE-338** | Cryptographically Weak PRNG | 0 | 0 | 0 | 36 | 36 |
| **CWE-364** | Signal Handler Race Condition | 0 | 0 | 0 | 36 | 36 |
| **CWE-366** | Thread Concurrency Race Condition | 0 | 0 | 0 | 72 | 72 |
| **CWE-367** | Time-of-Check Time-of-Use (TOCTOU) | 0 | 0 | 0 | 72 | 72 |
| **CWE-377** | Insecure Temporary File | 0 | 0 | 0 | 288 | 288 |
| **CWE-426** | Untrusted Search Path | 0 | 0 | 0 | 400 | 400 |
| **CWE-506** | Embedded Malicious Code (68 Vuln-only) | 0 | 0 | 0 | 248 | 248 |
| **CWE-620** | Unverified Password Change | 0 | 0 | 0 | 36 | 36 |
| **CWE-780** | RSA Without OAEP Padding | 0 | 0 | 0 | 36 | 36 |
| **P2 Unseen Total** | — | **0** | **0** | **0** | **4,476** | **4,476** |

#### B. 69 Seen CWEs in Phase 2 (11,084 Samples / 5,559 Records)
*Randomly split across Seen pool (70% Train, 15% Val, 15% Test Seen).* Full sample counts saved in `audit_sample_counts.json`:
- **Train:** 7,758 samples (across 69 CWEs)
- **Validation:** 1,666 samples (across 65 CWEs with sufficient support)
- **Test Seen:** 1,660 samples (across 65 CWEs with sufficient support)
*(Four low-sample categories with only 2 records—CWE-561, CWE-562, CWE-674, CWE-835—were assigned entirely to train to avoid fractional splitting).*

---

## Audit Point 2: Verification of Held-Out Exclusion

We checked set intersection between training sets, validation sets, and held-out sets:
* **Phase 1 Check:**
  $$\text{Train CWEs} \cap \text{Held-Out CWEs} = \emptyset \quad (\text{Intersection: } 0)$$
  $$\text{Val CWEs} \cap \text{Held-Out CWEs} = \emptyset \quad (\text{Intersection: } 0)$$
* **Phase 2 Check:**
  $$\text{Train CWEs} \cap \text{Held-Out CWEs} = \emptyset \quad (\text{Intersection: } 0)$$
  $$\text{Val CWEs} \cap \text{Held-Out CWEs} = \emptyset \quad (\text{Intersection: } 0)$$
* **Cross-Phase Check:**
  $$\text{Phase 1 Held-Out} \cap \text{Phase 2 Held-Out} = \emptyset \quad (\text{Intersection: } 0)$$
  $$\text{Phase 1 Train} \cap \text{Phase 2 Held-Out} = \emptyset \quad (\text{Intersection: } 0)$$
  $$\text{Phase 2 Train} \cap \text{Phase 1 Held-Out} = \emptyset \quad (\text{Intersection: } 0)$$

**Verdict: VERIFIED.** All 25 held-out CWE classes were strictly isolated from model training and validation tuning.

---

## Audit Point 3: Duplicate and Near-Duplicate Code Analysis

1. **Exact Deduplication Check:**
   - **Phase 1:** **0** non-trivial identical code bodies between Train and Held-Out sets. (Trivial empty stubs `{}` occur in Juliet fixed helper sinks and are ignored).
   - **Phase 2:** **18** instances of exact code overlap were found between training and held-out sets out of 7,831 records.
     - *Evidence:* Juliet test cases use identical boilerplate source setup across different flaws. Specifically, `CWE114_Process_Control__w32_wchar_t_connect_socket_63a.c` (Held-Out) and `CWE606_Unchecked_Loop_Condition__wchar_t_connect_socket_52a.c` (Train) share identical socket connection setup code before passing data to different sink files.
2. **Near-Duplicate Code:**
   - Juliet's synthetic structure uses flow variants (e.g., `_01.c` baseline vs. `_02.c` wrapped in `if (1)` vs. `_03.c` wrapped in `if (5==5)`).
   - Because all files for a held-out category reside strictly in that CWE's directory, flow-variant near-duplicates for held-out classes **only exist within the held-out set itself**, never leaking into the training splits.

---

## Audit Point 4: Data Sanitization & Shortcut Artifact Review

We audited `sanitize_code()` in `dataset.py` against Juliet source patterns:
1. **Function Names:** Regex `\b\w*_(bad|good)\w*\s*\(` strips function signature lines containing `_bad` or `_good`.
2. **Preprocessor Directives:** `#ifndef OMITBAD` and `#ifndef OMITGOOD` blocks are stripped.
3. **Comments:** Block comments `/* ... */` and line comments `// ...` (which contain `/* FLAW: ... */` and `/* FIX: ... */`) are stripped.
4. **Variable Signatures:** Identifiers `badData`, `goodG2BData`, `badSink`, `goodG2BSink`, etc., are normalized to the generic token `VAR`.

**Verdict: VERIFIED.** No synthetic labels or flaw comments leak into model inputs.

---

## Audit Point 5: Independent Recalculation of Metrics

We recalculated Recall, Precision, F1-Score, and FPR directly from:
- **Phase 1:** 2,116 ground-truth labels vs. predictions in `predictions_unseen.json`.
- **Phase 2:** 4,476 ground-truth labels vs. model inference outputs re-evaluated with `best_phase2_model.pt` at $\theta = 0.45$.

### Recalculation Results:

| Dataset Split | Evaluated Metric | Saved Metric | Recalculated Metric | Discrepancy |
| :--- | :--- | :---: | :---: | :---: |
| **Phase 1 Unseen (5 CWEs)** | Recall | 80.06% | **80.06%** (847/1058) | 0.00% |
| | Precision | 96.03% | **96.03%** (847/882) | 0.00% |
| | F1-Score | 87.32% | **87.32%** | 0.00% |
| | False Positive Rate | 3.31% | **3.31%** (35/1058) | 0.00% |
| | Accuracy | 88.37% | **88.37%** (1870/2116) | 0.00% |
| **Phase 2 Unseen (20 CWEs)** | Recall | 98.86% | **98.86%** (2246/2272) | 0.00% |
| | Precision | 82.73% | **82.73%** (2246/2715) | 0.00% |
| | F1-Score | 90.07% | **90.07%** | 0.00% |
| | False Positive Rate | 21.28% | **21.28%** (469/2204) | 0.00% |
| | Accuracy | 88.94% | **88.94%** (3981/4476) | 0.00% |
| **Combined (25 CWEs)** | Recall | 92.88% | **92.88%** (3093/3330) | 0.00% |
| | Precision | 85.99% | **85.99%** (3093/3597) | 0.00% |
| | F1-Score | 89.30% | **89.30%** | 0.00% |
| | False Positive Rate | 15.45% | **15.45%** (504/3262) | 0.00% |
| | Accuracy | 88.76% | **88.76%** (5851/6592) | 0.00% |

**Verdict: VERIFIED.** All metrics are mathematically accurate and derived from true positives, false positives, false negatives, and true negatives.

---

## Audit Point 6: Investigation of Categories with 100% Metrics

Across the 25 held-out categories, **9 categories** achieved 100% Recall and 100% Precision (0 False Positives and 0 False Negatives).

### Confusion Matrices and Sample Counts for 100% Categories:

| Category | Phase | TP | FP | FN | TN | Total Samples | Analysis of Why 100% Occurred |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **CWE-188** | P1 | 36 | 0 | 0 | 36 | 72 | Memory struct layout relies on `struct` offsets that static analyzer feature #37-#39 explicitly flags. |
| **CWE-273** | P2 | 36 | 0 | 0 | 36 | 72 | Privilege drop check checks `setuid`/`setgid` return values. Static return check ratio cleanly separates flaw from fix. |
| **CWE-338** | P2 | 18 | 0 | 0 | 18 | 36 | Calls to `rand()` without cryptographic initialization. Unambiguous semantic token difference between flaw and fix. |
| **CWE-364** | P2 | 18 | 0 | 0 | 18 | 36 | Signal handler race condition with static volatile flags; small sample count ($N=36$). |
| **CWE-366** | P2 | 36 | 0 | 0 | 36 | 72 | Thread race condition; safe variant introduces explicit thread mutex synchronization. |
| **CWE-367** | P2 | 36 | 0 | 0 | 36 | 72 | Time-of-check time-of-use (`access` vs `open`); static analyzer detects file open mode discrepancy. |
| **CWE-377** | P2 | 144 | 0 | 0 | 144 | 288 | Insecure temporary file uses dangerous APIs (`tmpnam`, `mktemp`). High sample count; perfect separation due to known insecure API signatures. |
| **CWE-620** | P2 | 18 | 0 | 0 | 18 | 36 | Password update verification; small sample count ($N=36$). |
| **CWE-780** | P2 | 18 | 0 | 0 | 18 | 36 | RSA without OAEP padding (`RSA_PKCS1_PADDING` vs `RSA_PKCS1_OAEP_PADDING`); distinct cryptographic token identifier. |

**Observation:** 7 of these 9 categories have modest sample counts ($N \le 72$). The only large-sample category with 100% metrics is **CWE-377** ($N=288$), which is explained by the binary presence of insecure temporary file creation routines (`tmpnam` vs `mkstemp`).

---

## Audit Point 7: Label Mapping and Positive Class Verification

1. **Mapping:**
   - Vulnerable code: **Label 1** (Positive Class)
   - Patched / Safe code: **Label 0** (Negative Class)
2. **Formulae Applied:**
   - $\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}} = \frac{\text{Predicted Vuln} \cap \text{Actual Vuln}}{\text{Actual Vuln}}$
   - $\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}} = \frac{\text{Predicted Vuln} \cap \text{Actual Vuln}}{\text{Predicted Vuln}}$
   - $\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}} = \frac{\text{Predicted Vuln} \cap \text{Actual Safe}}{\text{Actual Safe}}$

**Verdict: VERIFIED.** The positive class is strictly mapped to vulnerable functions.

---

## Audit Point 8: Cross-Experiment Test Sample Reuse

We cross-referenced unique function IDs (`function_id`) across all splits:
- Phase 1 Test Seen IDs ($N=1,698$) $\cap$ Phase 2 Test Seen IDs ($N=834$) = **0**
- Phase 1 Test Held-Out IDs ($N=2,116$) $\cap$ Phase 2 Test Held-Out IDs ($N=2,272$) = **0**
- Total Overlap between Phase 1 and Phase 2 file paths = **0**

**Verdict: VERIFIED.** Phase 1 and Phase 2 were evaluated on completely distinct source files and test subsets.

---

## Status of Saved Artifacts:
- **Phase 1 Predictions:** Saved at `D:\cybersec_2\results\predictions_seen.json` and `predictions_unseen.json`.
- **Phase 2 Predictions:** Per-sample prediction files (`predictions_seen_phase2.json`, `predictions_unseen_phase2.json`) were not originally exported to disk by `run_phase2.py`, though full per-CWE aggregated metrics were preserved in `phase2_results.json`. The individual prediction records have now been generated and verified from `best_phase2_model.pt`.
