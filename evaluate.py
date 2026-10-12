import os
import json
import numpy as np
from collections import defaultdict
from typing import Dict, List, Any

def compute_metrics(y_true: List[int], preds: List[int], probs: List[float], cwes: List[str]) -> Dict[str, Any]:
    """
    Computes overall and per-CWE Recall, Precision, F1-score, False Positive Rate (FPR), and Accuracy.
    """
    cwe_stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    
    for i in range(len(y_true)):
        cwe = cwes[i]
        actual = y_true[i]
        predicted = preds[i]
        
        if actual == 1 and predicted == 1:
            cwe_stats[cwe]["tp"] += 1
        elif actual == 1 and predicted == 0:
            cwe_stats[cwe]["fn"] += 1
        elif actual == 0 and predicted == 1:
            cwe_stats[cwe]["fp"] += 1
        else:
            cwe_stats[cwe]["tn"] += 1
            
    total_tp = sum(s["tp"] for s in cwe_stats.values())
    total_fp = sum(s["fp"] for s in cwe_stats.values())
    total_fn = sum(s["fn"] for s in cwe_stats.values())
    total_tn = sum(s["tn"] for s in cwe_stats.values())
    
    recall = (total_tp / (total_tp + total_fn) * 100.0) if (total_tp + total_fn) > 0 else 0.0
    precision = (total_tp / (total_tp + total_fp) * 100.0) if (total_tp + total_fp) > 0 else 0.0
    f1 = (2.0 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    fpr = (total_fp / (total_fp + total_tn) * 100.0) if (total_fp + total_tn) > 0 else 0.0
    accuracy = ((total_tp + total_tn) / (total_tp + total_tn + total_fp + total_fn) * 100.0)
    
    per_cwe_results = {}
    for cwe in sorted(cwe_stats.keys()):
        s = cwe_stats[cwe]
        c_rec = (s["tp"] / (s["tp"] + s["fn"]) * 100.0) if (s["tp"] + s["fn"]) > 0 else 0.0
        c_prec = (s["tp"] / (s["tp"] + s["fp"]) * 100.0) if (s["tp"] + s["fp"]) > 0 else 0.0
        c_f1 = (2.0 * c_prec * c_rec / (c_prec + c_rec)) if (c_prec + c_rec) > 0 else 0.0
        c_fpr = (s["fp"] / (s["fp"] + s["tn"]) * 100.0) if (s["fp"] + s["tn"]) > 0 else 0.0
        per_cwe_results[cwe] = {
            "tp": s["tp"], "fp": s["fp"], "fn": s["fn"], "tn": s["tn"],
            "recall": round(c_rec, 2),
            "precision": round(c_prec, 2),
            "f1": round(c_f1, 2),
            "fpr": round(c_fpr, 2)
        }
        
    return {
        "recall": round(recall, 2),
        "precision": round(precision, 2),
        "f1": round(f1, 2),
        "fpr": round(fpr, 2),
        "accuracy": round(accuracy, 2),
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "tn": total_tn,
        "cwe_stats": per_cwe_results
    }

def print_evaluation_report(split_name: str, metrics: Dict[str, Any]):
    print(f"\n{'='*70}")
    print(f"EVALUATION RESULTS: {split_name.upper()}")
    print(f"{'='*70}")
    print(f"{'CWE Category':<12} {'Recall%':>9} {'Prec%':>9} {'F1%':>9} {'FPR%':>9} {'TP':>6} {'FP':>6} {'FN':>6} {'TN':>6}")
    print(f"{'-'*70}")
    for cwe, s in metrics["cwe_stats"].items():
        print(f"{cwe:<12} {s['recall']:>9.2f} {s['precision']:>9.2f} {s['f1']:>9.2f} {s['fpr']:>9.2f} {s['tp']:>6} {s['fp']:>6} {s['fn']:>6} {s['tn']:>6}")
    print(f"{'-'*70}")
    print(f"{'OVERALL':<12} {metrics['recall']:>9.2f} {metrics['precision']:>9.2f} {metrics['f1']:>9.2f} {metrics['fpr']:>9.2f} {metrics['tp']:>6} {metrics['fp']:>6} {metrics['fn']:>6} {metrics['tn']:>6}")
    print(f"Overall Accuracy: {metrics['accuracy']:.2f}%\n")
