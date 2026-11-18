"""Digits for bases 2 to 62.

Digits are 0-9, then A-Z (10-35), then a-z (36-61). This is GMP's
convention for bases above 36, and the one used in data-minimal-sets. In
bases up to 36 only uppercase letters are used, as in the original C code.

Python's int(s, base) only goes up to base 36 and ignores letter case, so
larger bases are converted here (with gmpy2 if available).
"""

from functools import lru_cache

try:  # pragma: no cover - depends on the environment
    import gmpy2 as _gmpy2
except ImportError:  # pragma: no cover
    _gmpy2 = None

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
MAX_BASE = len(DIGITS)  # 62
_VALUE = {c: i for i, c in enumerate(DIGITS)}


def check_base(base):
    if not 2 <= base <= MAX_BASE:
        raise ValueError("base must be between 2 and %d" % MAX_BASE)


@lru_cache(maxsize=None)
def _power(base, k):
    return base ** k


def _parse_pure(s, base):
    n = len(s)
    if n <= 32:
        v = 0
        for c in s:
            d = _VALUE.get(c, MAX_BASE)
            if d >= base:
                raise ValueError("invalid digit %r for base %d" % (c, base))
            v = v * base + d
        return v
    mid = n // 2
    return _parse_pure(s[:mid], base) * _power(base, n - mid) + _parse_pure(s[mid:], base)


def parser(base):
    """A function turning a digit string in this base into an int."""
    check_base(base)
    if base <= 36:
        return lambda s: int(s, base)
    if _gmpy2 is not None:  # pragma: no cover
        mpz = _gmpy2.mpz
        return lambda s: int(mpz(s, base))
    return lambda s: _parse_pure(s, base)


def to_int(s, base):
    return parser(base)(s)


def to_str(n, base):
    """Digit string of a non-negative int in this base."""
    check_base(base)
    if n == 0:
        return "0"
    out = []
    while n:
        n, d = divmod(n, base)
        out.append(DIGITS[d])
    return "".join(reversed(out))
