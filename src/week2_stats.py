"""Dependency-free proportions, exact paired McNemar and Cohen's kappa."""
import math
from collections import Counter


def rate(k, n):
    if not n:
        return {'value': None, 'n': 0, 'ci95': None, 'ci95_wilson': None}
    p, z = k / n, 1.96
    half = z * math.sqrt(p * (1-p) / n)
    denom = 1 + z*z/n
    centre = (p + z*z/(2*n)) / denom
    whalf = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
    return {'value': p, 'n': n, 'count': k,
            'ci95': [max(0, p-half), min(1, p+half)],
            'ci95_wilson': [max(0, centre-whalf), min(1, centre+whalf)]}


def mcnemar(a, b):
    if len(a) != len(b):
        raise ValueError('Paired observations required')
    x = sum(i and not j for i, j in zip(a, b))
    y = sum(j and not i for i, j in zip(a, b))
    n = x + y
    p = min(1, 2 * sum(math.comb(n, k) for k in range(min(x, y)+1)) / 2**n) if n else 1.0
    return {'a_only_correct': x, 'b_only_correct': y, 'p_exact_two_sided': p,
            'note': 'Exploratory: best two selected on this same test set.'}


def kappa(a, b):
    if not a or len(a) != len(b):
        raise ValueError('Nonempty paired labels required')
    n = len(a)
    ca, cb = Counter(a), Counter(b)
    observed = sum(x == y for x, y in zip(a, b)) / n
    expected = sum(ca[k] * cb[k] for k in ca.keys() | cb.keys()) / n**2
    return {'n': n, 'agreement': observed,
            'cohen_kappa': (observed-expected)/(1-expected) if expected < 1 else None}
