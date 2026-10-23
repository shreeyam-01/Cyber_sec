import os
import re
import json
import random
from collections import defaultdict

JULIET_DIR = r"D:\cybersec\mnt\agents\output\dataset\raw\juliet-test-suite-c\testcases"
OUTPUT_DIR = r"D:\cybersec_2\phase2_dataset"

SEEN_CWES = [
    # Memory & Resource Lifecycle (15)
    "CWE-400", "CWE-401", "CWE-404", "CWE-459", "CWE-590",
    "CWE-591", "CWE-666", "CWE-675", "CWE-761", "CWE-773",
    "CWE-775", "CWE-785", "CWE-789", "CWE-832", "CWE-562",
    # Pointer, Type Confusion & Boundaries (12)
    "CWE-464", "CWE-467", "CWE-468", "CWE-469", "CWE-475",
    "CWE-587", "CWE-588", "CWE-680", "CWE-681", "CWE-690",
    "CWE-843", "CWE-196",
    # Control Flow, Loops, Logic & Errors (24)
    "CWE-252", "CWE-390", "CWE-391", "CWE-398", "CWE-427",
    "CWE-478", "CWE-479", "CWE-480", "CWE-481", "CWE-482",
    "CWE-483", "CWE-484", "CWE-561", "CWE-563", "CWE-570",
    "CWE-571", "CWE-605", "CWE-606", "CWE-617", "CWE-665",
    "CWE-667", "CWE-674", "CWE-758", "CWE-835",
    # Sensitive Data, Info Leaks & Misc (18)
    "CWE-15", "CWE-176", "CWE-222", "CWE-223", "CWE-226",
    "CWE-242", "CWE-244", "CWE-247", "CWE-325", "CWE-510",
    "CWE-511", "CWE-526", "CWE-534", "CWE-535", "CWE-546",
    "CWE-615", "CWE-685", "CWE-688"
]

HELD_OUT_CWES = [
    # 20 Unseen Zero-Shot Classes
    "CWE-78", "CWE-90", "CWE-114", "CWE-256", "CWE-259",
    "CWE-272", "CWE-273", "CWE-284", "CWE-319", "CWE-321",
    "CWE-328", "CWE-338", "CWE-364", "CWE-366", "CWE-367",
    "CWE-377", "CWE-426", "CWE-506", "CWE-620", "CWE-780"
]

os.makedirs(OUTPUT_DIR, exist_ok=True)
random.seed(42)

def find_cwe_dir(cwe_id):
    cwe_num = cwe_id.replace("CWE-", "")
    for d in os.listdir(JULIET_DIR):
        if d.startswith(f"CWE{cwe_num}_") or d == f"CWE{cwe_num}":
            return os.path.join(JULIET_DIR, d)
    return None

def extract_bad_good(filepath):
    with open(filepath, 'r', errors='ignore', encoding='utf-8') as f:
        content = f.read()
    
    bad_func = None
    good_func = None
    
    bad_start = content.find('#ifndef OMITBAD')
    bad_end = content.find('#endif /* OMITBAD */')
    if bad_start != -1 and bad_end != -1:
        bad_code = content[bad_start:bad_end].strip()
        vuln_lines = [i for i, line in enumerate(bad_code.split('\n'), 1) if 'FLAW' in line]
        bad_func = {'code': bad_code, 'vuln_lines': vuln_lines}
        
    good_start = content.find('#ifndef OMITGOOD')
    good_end = content.find('#endif /* OMITGOOD */')
    if good_start != -1 and good_end != -1:
        good_code = content[good_start:good_end].strip()
        good_func = {'code': good_code, 'vuln_lines': []}
        
    return bad_func, good_func

def main():
    print("=" * 70)
    print("PARSING 89 REMAINING JULIET C/C++ CWE CATEGORIES")
    print(f"Seen: {len(SEEN_CWES)} classes | Held-Out Unseen: {len(HELD_OUT_CWES)} classes")
    print("=" * 70)

    records = []
    cwe_counts = defaultdict(int)

    for cwe_id in SEEN_CWES + HELD_OUT_CWES:
        cwe_dir = find_cwe_dir(cwe_id)
        if not cwe_dir:
            print(f"[!] Warning: Directory for {cwe_id} not found")
            continue
        
        c_files = []
        for root, dirs, files in os.walk(cwe_dir):
            for f in files:
                if f.endswith('.c'):
                    c_files.append(os.path.join(root, f))
        
        count = 0
        for cfile in c_files:
            bad, good = extract_bad_good(cfile)
            if bad:
                split_group = "seen" if cwe_id in SEEN_CWES else "held_out"
                records.append({
                    "function_id": f"{cwe_id}_{cwe_counts[cwe_id]:04d}",
                    "source": "juliet_test_suite_v1.3",
                    "language": "c",
                    "cwe_class": cwe_id,
                    "split_group": split_group,
                    "code_vulnerable": bad['code'],
                    "code_fixed": good['code'] if good else None,
                    "vuln_lines": bad['vuln_lines'],
                    "file_path": cfile
                })
                cwe_counts[cwe_id] += 1
                count += 1
        
        print(f"Extracted {cwe_id}: {count} records")

    print(f"\nTotal raw extracted records: {len(records)}")

    # Balance large classes: Cap at 200 samples per class to ensure fast, balanced training
    MAX_PER_CWE = 200
    balanced_records = []
    for cwe_id in SEEN_CWES + HELD_OUT_CWES:
        cwe_records = [r for r in records if r['cwe_class'] == cwe_id]
        if len(cwe_records) > MAX_PER_CWE:
            cwe_records = random.sample(cwe_records, MAX_PER_CWE)
        balanced_records.extend(cwe_records)

    seen_records = [r for r in balanced_records if r['split_group'] == 'seen']
    held_out_records = [r for r in balanced_records if r['split_group'] == 'held_out']

    random.shuffle(seen_records)
    n = len(seen_records)
    train_end = int(n * 0.70)
    val_end = int(n * 0.85)

    for i, r in enumerate(seen_records):
        if i < train_end:
            r['split'] = 'train'
        elif i < val_end:
            r['split'] = 'val'
        else:
            r['split'] = 'test_seen'

    for r in held_out_records:
        r['split'] = 'test_held_out'

    all_records = seen_records + held_out_records

    # Save dataset & summary
    out_file = os.path.join(OUTPUT_DIR, "phase2_dataset.json")
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(all_records, f, indent=2)

    summary = {
        "total": len(all_records),
        "seen_cwes_count": len(SEEN_CWES),
        "held_out_cwes_count": len(HELD_OUT_CWES),
        "by_cwe": {},
        "by_split": {}
    }
    for r in all_records:
        summary["by_cwe"][r['cwe_class']] = summary["by_cwe"].get(r['cwe_class'], 0) + 1
        summary["by_split"][r['split']] = summary["by_split"].get(r['split'], 0) + 1

    summary_file = os.path.join(OUTPUT_DIR, "phase2_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print(f"\n[DONE] Saved: {len(all_records)} balanced records to {out_file}")
    print(f"By Split: {summary['by_split']}")

    # Verify zero data leakage
    train_cwes = set(r['cwe_class'] for r in all_records if r['split'] == 'train')
    held_cwes = set(r['cwe_class'] for r in all_records if r['split'] == 'test_held_out')
    overlap = train_cwes & held_cwes
    assert len(overlap) == 0, f"Critical Data Leakage Detected: {overlap}"
    print(f"\n[LEAKAGE CHECK] PASSED: 0 overlap between Train ({len(train_cwes)} CWEs) and Held-Out ({len(held_cwes)} CWEs).")

if __name__ == "__main__":
    main()
