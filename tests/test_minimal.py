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
