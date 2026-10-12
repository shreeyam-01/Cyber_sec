import os
import re
import json
from typing import List, Tuple, Dict, Any

def sanitize_code(code: str) -> str:
    """
    Remove Juliet leakage signals consistently with baseline evaluation:
    - Function names ending in _bad or _good
    - Preprocessor directives like #ifndef OMITBAD / OMITGOOD
    - Comments containing FLAW, FIX, INCIDENTAL, etc.
    - Variable names like badData, goodG2BData, badSink, etc.
    """
    if not code:
        return ""
    lines = code.split('\n')
    clean_lines = []
    
    for line in lines:
        # Skip function declaration lines containing _bad or _good
        if re.search(r'\b\w*_(bad|good)\w*\s*\(', line):
            continue
            
        # Skip OMITBAD and OMITGOOD directives
        if 'OMITBAD' in line or 'OMITGOOD' in line:
            continue
        
        # Remove C comments
        line = re.sub(r'/\*.*?\*/', '', line)
        line = re.sub(r'//.*$', '', line)
        
        # Remove leakage tokens (case insensitive)
        line = re.sub(
            r'\b(bad|good|flaw|fix|badData|goodG2BData|badSink|goodG2BSink|goodG2B|goodB2G)\b',
            'VAR',
            line,
            flags=re.IGNORECASE
        )
        
        if not line.strip():
            continue
            
        clean_lines.append(line)
    
    return '\n'.join(clean_lines)


class JulietDataset:
    def __init__(self, dataset_path: str):
        self.dataset_path = dataset_path
        with open(dataset_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
            
        self.verify_no_leakage()

    def verify_no_leakage(self):
        """Verify train CWEs and held-out test CWEs are strictly disjoint."""
        train_cwes = set(r['cwe_class'] for r in self.raw_data if r['split'] == 'train')
        held_cwes = set(r['cwe_class'] for r in self.raw_data if r['split'] == 'test_held_out')
        overlap = train_cwes & held_cwes
        assert len(overlap) == 0, f"Critical Data Leakage: CWE overlap detected: {overlap}"
        print(f"[Dataset] Verified 0 overlap between Train ({len(train_cwes)} CWEs) and Held-out ({len(held_cwes)} CWEs).")

    def get_split_samples(self, split_name: str) -> Tuple[List[str], List[int], List[str], List[str]]:
        """
        Returns:
            texts: List of sanitized code strings
            labels: List of int labels (1 for vuln, 0 for fixed/safe)
            cwes: List of CWE IDs
            func_ids: List of function IDs
        """
        records = [r for r in self.raw_data if r['split'] == split_name]
        texts, labels, cwes, func_ids = [], [], [], []
        
        for r in records:
            # Vulnerable sample
            vuln_clean = sanitize_code(r['code_vulnerable'])
            texts.append(vuln_clean)
            labels.append(1)
            cwes.append(r['cwe_class'])
            func_ids.append(r['function_id'] + "_vuln")
            
            # Safe/fixed sample
            if r['code_fixed'] is not None:
                fixed_clean = sanitize_code(r['code_fixed'])
                texts.append(fixed_clean)
                labels.append(0)
                cwes.append(r['cwe_class'])
                func_ids.append(r['function_id'] + "_fixed")
                
        return texts, labels, cwes, func_ids
