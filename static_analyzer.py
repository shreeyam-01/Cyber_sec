import re
import numpy as np
from typing import List

class StaticFeatureExtractor:
    """
    Domain-informed static code analysis feature extractor.
    Extracts numerical signals capturing syntactic vulnerability hazards,
    memory bounds patterns, arithmetic limits, return-value checks,
    and defensive validation structures.
    """
    def __init__(self):
        # Unsafe string / buffer manipulation routines
        self.unsafe_string_funcs = re.compile(
            r'\b(strcpy|wcscpy|strcat|wcscat|gets|sprintf|vsprintf|scanf|sscanf|fscanf)\b',
            re.IGNORECASE
        )
        # Safe bounds-checking string routines
        self.safe_string_funcs = re.compile(
            r'\b(strncpy|wcsncpy|strncat|wcsncat|snprintf|vsnprintf|memcpy_s|strcpy_s)\b',
            re.IGNORECASE
        )
        # Memory lifecycle primitives
        self.alloc_funcs = re.compile(r'\b(malloc|alloca|calloc|realloc|new)\b')
        self.free_funcs = re.compile(r'\b(free|delete)\b')
        
        # Dangerous / weak cryptography identifiers
        self.weak_crypto = re.compile(r'\b(DES|MD5|SHA1|RC4|ECB|des_|md5_|DES_)\b', re.IGNORECASE)
        self.strong_crypto = re.compile(r'\b(AES|SHA256|SHA512|EVP_|aes_)\b', re.IGNORECASE)
        
        # Critical APIs subject to CWE-253 return-check omission
        self.ret_critical_apis = re.compile(
            r'\b(fputs|fputws|remove|unlink|fgets|fgetws|fopen|fread|fwrite)\b'
        )
        
        # Format string patterns
        self.format_calls = re.compile(r'\b(printf|fprintf|vprintf|vfprintf|syslog)\b')
        self.direct_format_risk = re.compile(r'\b(print(f|Line)|fprintf)\s*\(\s*([a-zA-Z_]\w*)\s*\)')
        
        # Integer boundary and arithmetic patterns
        self.int_limits = re.compile(r'\b(INT_MAX|INT_MIN|CHAR_MAX|CHAR_MIN|SHRT_MAX|SHRT_MIN|UINT_MAX)\b')
        self.type_casts = re.compile(r'\(\s*(int|unsigned\s+int|size_t|short|unsigned\s+short|char)\s*\)')
        
        # Validation checks
        self.null_checks = re.compile(r'(!=\s*NULL|==\s*NULL|\bNULL\b)')
        self.comparison_bounds = re.compile(r'(<|<=|>|>=|==|!=)')
        self.return_eof_check = re.compile(r'(==\s*EOF|!=\s*EOF|<=\s*0|<\s*0|==\s*0)')

    def extract_features_single(self, code: str) -> np.ndarray:
        feats = []
        lines = code.split('\n')
        num_lines = max(len(lines), 1)
        total_chars = max(len(code), 1)

        # 1-2: Code scale
        feats.append(float(num_lines))
        feats.append(float(total_chars) / 1000.0)

        # 3-5: Unsafe vs Safe string operations
        n_unsafe_str = len(self.unsafe_string_funcs.findall(code))
        n_safe_str = len(self.safe_string_funcs.findall(code))
        feats.append(float(n_unsafe_str))
        feats.append(float(n_safe_str))
        feats.append(float(n_unsafe_str) / (n_safe_str + 1.0))

        # 6-8: Memory allocation and free patterns
        n_alloc = len(self.alloc_funcs.findall(code))
        n_free = len(self.free_funcs.findall(code))
        feats.append(float(n_alloc))
        feats.append(float(n_free))
        feats.append(float(n_free - n_alloc)) # imbalance indicates leak or double free

        # 9-11: Pointer and array index manipulation
        n_ptr_ops = len(re.findall(r'(\->|\*|\bdata\b|\bpointer\b)', code))
        n_array_idx = len(re.findall(r'\[\s*[^\]]+\s*\]', code))
        n_ptr_arith = len(re.findall(r'(\+\+|\-\-|\+\s*\d+|\-\s*\d+)', code))
        feats.append(float(n_ptr_ops) / num_lines)
        feats.append(float(n_array_idx) / num_lines)
        feats.append(float(n_ptr_arith) / num_lines)

        # 12-14: Off-by-one and boundary tokens
        n_minus_one = len(re.findall(r'(\-\s*1|\+\s*1)', code))
        n_sizeof = len(re.findall(r'\bsizeof\b', code))
        feats.append(float(n_minus_one))
        feats.append(float(n_sizeof))
        feats.append(float(n_minus_one) / (n_sizeof + 1.0))

        # 15-18: Integer arithmetic, casts, and limits
        n_int_limits = len(self.int_limits.findall(code))
        n_casts = len(self.type_casts.findall(code))
        n_div_mod = len(re.findall(r'(\/|\%)', code))
        feats.append(float(n_int_limits))
        feats.append(float(n_casts))
        feats.append(float(n_div_mod))
        feats.append(float(n_casts + n_div_mod) / num_lines)

        # 19-21: Return value check patterns (CWE-253)
        n_ret_apis = len(self.ret_critical_apis.findall(code))
        n_eof_checks = len(self.return_eof_check.findall(code))
        feats.append(float(n_ret_apis))
        feats.append(float(n_eof_checks))
        feats.append(float(n_eof_checks) / (n_ret_apis + 1.0))

        # 22-24: Crypto identifiers (CWE-327)
        n_weak_crypto = len(self.weak_crypto.findall(code))
        n_strong_crypto = len(self.strong_crypto.findall(code))
        feats.append(float(n_weak_crypto))
        feats.append(float(n_strong_crypto))
        feats.append(float(n_weak_crypto) / (n_strong_crypto + 1.0))

        # 25-27: Format string vulnerabilities (CWE-134)
        n_format_calls = len(self.format_calls.findall(code))
        n_direct_fmt = len(self.direct_format_risk.findall(code))
        feats.append(float(n_format_calls))
        feats.append(float(n_direct_fmt))
        feats.append(float(n_direct_fmt) / (n_format_calls + 1.0))

        # 28-30: Conditional checks and validation density
        n_if_branches = len(re.findall(r'\b(if|else\s+if|switch)\b', code))
        n_loops = len(re.findall(r'\b(for|while|do)\b', code))
        feats.append(float(n_if_branches))
        feats.append(float(n_loops))
        feats.append(float(n_if_branches + n_loops) / num_lines)

        # 31-33: Null and defensive checks
        n_null_checks = len(self.null_checks.findall(code))
        n_bounds_cmp = len(self.comparison_bounds.findall(code))
        feats.append(float(n_null_checks))
        feats.append(float(n_bounds_cmp))
        feats.append(float(n_null_checks + n_bounds_cmp) / (n_if_branches + 1.0))

        # 34-36: Defensive termination / exit patterns
        n_returns = len(re.findall(r'\breturn\b', code))
        n_exits = len(re.findall(r'\b(exit|abort)\b', code))
        feats.append(float(n_returns))
        feats.append(float(n_exits))
        feats.append(float(n_returns + n_exits) / num_lines)

        # 37-39: Memory layout and struct alignment (CWE-188)
        n_structs = len(re.findall(r'\bstruct\b', code))
        n_offsets = len(re.findall(r'(\boffsetof\b|\bchar\s*\*\b)', code))
        feats.append(float(n_structs))
        feats.append(float(n_offsets))
        feats.append(float(n_structs + n_offsets) / num_lines)

        # 40-42: Flow control branch predicates (detecting true vs inverted branches)
        n_true_preds = len(re.findall(r'(==\s*5|5\s*==\s*5|globalReturnsTrue|staticReturnsTrue)', code))
        n_false_preds = len(re.findall(r'(!=\s*5|5\s*!=\s*5|globalReturnsFalse|staticReturnsFalse)', code))
        feats.append(float(n_true_preds))
        feats.append(float(n_false_preds))
        feats.append(float(n_false_preds - n_true_preds))

        # 43-45: Zero-checks and divisor safeguards
        n_zero_cmp = len(re.findall(r'(==\s*0|!=\s*0|==\s*NULL|!=\s*NULL)', code))
        feats.append(float(n_zero_cmp))
        feats.append(float(n_zero_cmp) / (n_div_mod + 1.0))
        feats.append(float(n_zero_cmp) / (n_alloc + 1.0))

        # 46-48: General risk ratios
        feats.append(float(n_unsafe_str + n_direct_fmt + n_weak_crypto) / (num_lines + 1.0))
        feats.append(float(n_safe_str + n_null_checks + n_eof_checks) / (num_lines + 1.0))
        feats.append(float(n_unsafe_str + n_direct_fmt + n_weak_crypto + 1.0) / 
                     (n_safe_str + n_null_checks + n_eof_checks + 1.0))

        assert len(feats) == 48, f"Feature length mismatch: expected 48, got {len(feats)}"
        return np.array(feats, dtype=np.float32)

    def extract_features_batch(self, codes: List[str]) -> np.ndarray:
        return np.vstack([self.extract_features_single(c) for c in codes])
