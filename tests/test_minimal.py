"""Tests for the Bright Algorithm translation.

Run from the repository root with:  python -m unittest discover tests
"""

import os
import re
import unittest

from bright.minimal import (
    BrightMinimal, compute_base, familystring, parse_family, simplefamilystring,
    issimple,
)
from bright.primality import _pure_python_is_probable_prime, _small_primes

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data-minimal-sets")

# Unsolved simple families reported by the original C minimal.c, for comparison.
EXPECTED_UNSOLVED = {
    2: [], 3: [], 4: [], 6: [], 9: [],
    5: ["14*", "4*1"],
    7: ["1*"],
    8: ["4*1", "4*61", "4*11"],
    10: ["60*49", "660*49", "6660*49"],
    12: ["AA0*1", "AAA0*1"],
}


def reference_set(base):
    with open(os.path.join(DATA, "minimal.%d.txt" % base)) as fh:
        return set(fh.read().split())


class TestPrimality(unittest.TestCase):
    def test_matches_sieve(self):
        primes = set(_small_primes(100000))
        for n in range(100001):
            self.assertEqual(_pure_python_is_probable_prime(n), n in primes, n)

    def test_large_and_pseudoprimes(self):
        ip = _pure_python_is_probable_prime
        self.assertTrue(ip(2 ** 127 - 1))
        self.assertTrue(ip(2 ** 521 - 1))
        self.assertFalse(ip((2 ** 61 - 1) * (2 ** 89 - 1)))
        self.assertFalse(ip(3825123056546413051))       # strong pseudoprime to bases 2..23
        self.assertFalse(ip(318665857834031151167461))  # strong pseudoprime to bases 2..37


class TestFamilies(unittest.TestCase):
    def test_round_trip(self):
        for s in ["1{03}*2", "9{4}*{5}*1", "A{0}*{F}*{0}*B", "12", "4{8}*9"]:
            self.assertEqual(familystring(parse_family(s)), s)

    def test_simple_string(self):
        f = parse_family("6{0}*49")
        self.assertTrue(issimple(f))
        self.assertEqual(simplefamilystring(f), "60*49")


class TestMinimalPrimes(unittest.TestCase):
    def check_base(self, base):
        kernel, unsolved = compute_base(base, log=None, write_files=False)
        names = [simplefamilystring(f) if issimple(f) else familystring(f) for f in unsolved]
        if base in EXPECTED_UNSOLVED:
            self.assertEqual(names, EXPECTED_UNSOLVED[base])
        ours, ref = set(kernel), reference_set(base)
        self.assertEqual(len(kernel), len(ours), "duplicate kernel entries")
        self.assertTrue(ours <= ref, "primes not in reference: %s" % sorted(ours - ref))
        # Anything in the reference that we did not find must lie in an
        # unsolved family (found later by simple/search in the C pipeline).
        patterns = [re.compile("^" + n + "$") for n in names]
        for p in ref - ours:
            self.assertTrue(any(r.match(p) for r in patterns), p)

    def test_bases_2_to_12(self):
        for base in range(2, 13):
            with self.subTest(base=base):
                self.check_base(base)

    def test_solved_bases_are_complete(self):
        for base in (2, 3, 4, 6, 9):
            kernel, unsolved = compute_base(base, log=None, write_files=False)
            self.assertEqual(unsolved, [])
            self.assertEqual(set(kernel), reference_set(base))

    def test_bad_base(self):
        with self.assertRaises(ValueError):
            BrightMinimal(37)


if __name__ == "__main__":
    unittest.main()


class TestClassFilter(unittest.TestCase):
    """--class a m: minimal elements of the primes p = a (mod m)."""

    @staticmethod
    def brute_force(base, a, m, digits):
        limit = base ** digits
        sieve = bytearray([1]) * limit
        sieve[0:2] = b"\x00\x00"
        for p in range(2, int(limit ** 0.5) + 1):
            if sieve[p]:
                sieve[p * p :: p] = bytearray(len(range(p * p, limit, p)))
        digs = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        mins = []
        for n in range(2, limit):
            if sieve[n] and n % m == a:
                s = ""
                while n:
                    n, d = divmod(n, base)
                    s = digs[d] + s
                if not any(re.search(".*".join(q), s) for q in mins):
                    mins.append(s)
        return set(mins)

    def check(self, base, a, m, digits):
        kernel, unsolved = compute_base(base, log=None, write_files=False, residue=a, modulus=m)
        for p in kernel:
            self.assertEqual(int(p, base) % m, a, p)
        names = [simplefamilystring(f) if issimple(f) else familystring(f) for f in unsolved]
        patterns = [re.compile("^" + re.sub(r"\{([^}]*)\}\*", r"[\1]*", n) + "$") for n in names]
        expected = self.brute_force(base, a, m, digits)
        short = {p for p in kernel if len(p) <= digits}
        self.assertTrue(short <= expected, sorted(short - expected))
        for p in expected - set(kernel):
            self.assertTrue(any(r.match(p) for r in patterns), p)

    def test_base10_mod5(self):
        for a in (1, 2, 3, 4):
            with self.subTest(a=a):
                self.check(10, a, 5, 6)

    def test_small_bases(self):
        for base, a, m in [(2, 1, 3), (2, 2, 3), (3, 1, 4), (3, 3, 4), (6, 1, 5), (7, 2, 3)]:
            with self.subTest(base=base, a=a, m=m):
                self.check(base, a, m, 6 if base < 7 else 5)

    def test_class_sharing_a_factor(self):
        cases = {(10, 0, 3): ["3"], (10, 7, 14): ["7"], (10, 6, 12): [], (2, 0, 3): ["11"]}
        for (base, a, m), want in cases.items():
            self.assertEqual(compute_base(base, log=None, write_files=False,
                                          residue=a, modulus=m), (want, []))

    def test_unfiltered_unchanged(self):
        self.assertEqual(compute_base(10, log=None, write_files=False),
                         compute_base(10, log=None, write_files=False, residue=0, modulus=1))
