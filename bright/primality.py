"""Probable-prime testing for the Bright Algorithm.

The original C code calls GMP's ``mpz_probab_prime_p(n, 25)``. Modern GMP runs
a Baillie-PSW test followed by extra Miller-Rabin rounds. This module does the
same:

* if ``gmpy2`` is installed, ``gmpy2.is_prime(n, 25)`` is used (it wraps the
  same GMP routine as the C code);
* otherwise, if the GMP library itself (``libgmp``) can be found, its
  ``mpz_probab_prime_p(n, 25)`` is called directly through ``ctypes``. This is
  the same routine at the same speed, without needing gmpy2 installed. Set
  the environment variable ``BRIGHT_NO_LIBGMP=1`` to skip it;
* otherwise a pure-Python Baillie-PSW test is used (trial division, a strong
  base-2 Fermat test, then a strong Lucas test with Selfridge parameters).
  Below 3.3 * 10**24 a deterministic Miller-Rabin test is used instead.

No Baillie-PSW pseudoprime is known, so both paths agree in practice.
"""

from math import isqrt

try:  # pragma: no cover - depends on the environment
    import gmpy2 as _gmpy2
except ImportError:  # pragma: no cover
    _gmpy2 = None

__all__ = ["is_probable_prime", "BACKEND"]


def _small_primes(limit):
    sieve = bytearray([1]) * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, isqrt(limit) + 1):
        if sieve[p]:
            sieve[p * p :: p] = bytearray(len(range(p * p, limit + 1, p)))
    return [p for p in range(limit + 1) if sieve[p]]


_TRIAL_LIMIT = 1000
_SMALL_PRIMES = _small_primes(_TRIAL_LIMIT)
# Deterministic Miller-Rabin bases valid for n < 3,317,044,064,679,887,385,961,981.
_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)
_MR_DETERMINISTIC_LIMIT = 3317044064679887385961981


def _strong_probable_prime(n, a):
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    x = pow(a, d, n)
    if x == 1 or x == n - 1:
        return True
    for _ in range(s - 1):
        x = x * x % n
        if x == n - 1:
            return True
    return False


def _jacobi(a, n):
    a %= n
    result = 1
    while a:
        while a % 2 == 0:
            a //= 2
            if n % 8 in (3, 5):
                result = -result
        a, n = n, a
        if a % 4 == 3 and n % 4 == 3:
            result = -result
        a %= n
    return result if n == 1 else 0


def _strong_lucas_probable_prime(n):
    """Strong Lucas test with Selfridge's method A parameters (n odd, > 2)."""
    r = isqrt(n)
    if r * r == n:
        return False
    D = 5
    while True:
        j = _jacobi(D, n)
        if j == -1:
            break
        if j == 0 and abs(D) != n:
            return False
        D = -D - 2 if D > 0 else -D + 2
    P, Q = 1, (1 - D) // 4

    d = n + 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1

    def half(x):
        x %= n
        return (x if x % 2 == 0 else x + n) // 2 % n

    U, V, Qk = 1, P % n, Q % n
    for bit in bin(d)[3:]:
        U = U * V % n
        V = (V * V - 2 * Qk) % n
        Qk = Qk * Qk % n
        if bit == "1":
            U, V = half(P * U + V), half(D * U + P * V)
            Qk = Qk * Q % n

    if U == 0 or V == 0:
        return True
    for _ in range(s - 1):
        V = (V * V - 2 * Qk) % n
        if V == 0:
            return True
        Qk = Qk * Qk % n
    return False


def _pure_python_is_probable_prime(n):
    if n < 2:
        return False
    for p in _SMALL_PRIMES:
        if n % p == 0:
            return n == p
    if n < _TRIAL_LIMIT * _TRIAL_LIMIT:
        return True
    if n < _MR_DETERMINISTIC_LIMIT:
        return all(_strong_probable_prime(n, a) for a in _MR_BASES)
    return _strong_probable_prime(n, 2) and _strong_lucas_probable_prime(n)


def _load_libgmp():
    """``mpz_probab_prime_p`` from libgmp through ctypes, or None."""
    import os
    if os.environ.get("BRIGHT_NO_LIBGMP"):
        return None
    try:
        import ctypes
        import ctypes.util
        names = [ctypes.util.find_library("gmp"), "libgmp.so.10", "libgmp.so",
                 "libgmp.10.dylib", "libgmp.dylib", "libgmp-10.dll", "gmp.dll"]
        lib = None
        for name in names:
            if not name:
                continue
            try:
                lib = ctypes.CDLL(name)
                break
            except OSError:
                continue
        if lib is None:
            return None

        class _Mpz(ctypes.Structure):
            _fields_ = [("alloc", ctypes.c_int), ("size", ctypes.c_int),
                        ("d", ctypes.c_void_p)]

        ptr = ctypes.POINTER(_Mpz)
        init, clear = lib.__gmpz_init, lib.__gmpz_clear
        init.argtypes = clear.argtypes = [ptr]
        imp = lib.__gmpz_import
        imp.argtypes = [ptr, ctypes.c_size_t, ctypes.c_int, ctypes.c_size_t,
                        ctypes.c_int, ctypes.c_size_t, ctypes.c_char_p]
        test = lib.__gmpz_probab_prime_p
        test.argtypes = [ptr, ctypes.c_int]
        test.restype = ctypes.c_int

        def probab_prime_p(n, reps=25):
            if n < 2:
                return 0
            z = _Mpz()
            init(ctypes.byref(z))
            try:
                data = n.to_bytes((n.bit_length() + 7) // 8, "big")
                imp(ctypes.byref(z), len(data), 1, 1, 1, 0, data)
                return test(ctypes.byref(z), reps)
            finally:
                clear(ctypes.byref(z))

        # Sanity check before trusting it.
        if [probab_prime_p(k) > 0 for k in (1, 2, 9, 97, 561, 2**89 - 1, 2**89 + 1)] \
                != [False, True, False, True, False, True, False]:
            return None
        return probab_prime_p
    except Exception:  # pragma: no cover - any failure means: don't use it
        return None


if _gmpy2 is not None:  # pragma: no cover

    def is_probable_prime(n):
        """Equivalent of ``mpz_probab_prime_p(n, 25) > 0``."""
        return bool(_gmpy2.is_prime(n, 25))

    BACKEND = "gmpy2"
else:
    _libgmp_test = _load_libgmp()
    if _libgmp_test is not None:

        def is_probable_prime(n):
            """``mpz_probab_prime_p(n, 25) > 0``, called in libgmp directly."""
            return _libgmp_test(n, 25) > 0

        BACKEND = "libgmp"
    else:
        is_probable_prime = _pure_python_is_probable_prime
        BACKEND = "pure-python"
