"""End-to-end tests: minimal -> simple / sieve-start + search -> organize."""

import io
import os
import shutil
import tempfile
import unittest

from bright.common import read_lines, subword
from bright.minimal import compute_base
from bright.organize import run_organize
from bright.search import run_search
from bright.sieving import family_line, merge, parse_sieve, start_sieve, surviving_exponents
from bright.simple import run_simple

HERE = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(HERE, "..", "data-minimal-sets")


def reference(base):
    with open(os.path.join(REF, "minimal.%d.txt" % base)) as fh:
        return fh.read().split()


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.data = os.path.join(self.dir, "data")
        self.sieve = os.path.join(self.dir, "sieve")
        self.quiet = io.StringIO()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def minimal(self, bases):
        for b in bases:
            compute_base(b, log=None, datadir=self.data, iterdir=os.path.join(self.dir, "iter"))

    def test_simple_then_organize_completes_bases(self):
        bases = (5, 7, 8, 10, 12)
        self.minimal(bases)
        run_simple(1, 60, datadir=self.data, out=self.quiet)
        run_organize(datadir=self.data, out=self.quiet)
        for b in bases:
            with self.subTest(base=b):
                # organize sorts by length then value, like the reference files
                self.assertEqual(read_lines(os.path.join(self.data, "minimal.%d.txt" % b)),
                                 sorted(reference(b), key=lambda s: (len(s), s)))
                self.assertEqual(read_lines(os.path.join(self.data, "unsolved.%d.txt" % b)), [])

    def test_sieve_and_search_complete_base_10(self):
        self.minimal([10])
        start_sieve(1, 30, datadir=self.data, sievedir=self.sieve)
        import contextlib
        with contextlib.redirect_stdout(self.quiet):
            run_search(1, 30, datadir=self.data)
        run_organize(datadir=self.data, out=self.quiet)
        self.assertEqual(read_lines(os.path.join(self.data, "minimal.10.txt")),
                         sorted(reference(10), key=lambda s: (len(s), s)))

    def test_merge_keeps_common_exponents(self):
        os.makedirs(self.data)
        os.makedirs(self.sieve)
        with open(os.path.join(self.data, "sieve.10.txt"), "w") as fh:
            fh.write("pmin=31\n600*10^n+49\n1\n2\n3\n5\n9*10^n+1\n4\n")
        with open(os.path.join(self.sieve, "sieve.10.txt"), "w") as fh:
            fh.write("pmin=1000\n600*10^n+49\n2\n3\n4\n5\n7*10^n+1\n6\n")
        merge(self.data, self.sieve)
        expected = ["pmin=1000", "600*10^n+49", "2", "3", "5"]
        self.assertEqual(read_lines(os.path.join(self.data, "sieve.10.txt")), expected)
        self.assertEqual(read_lines(os.path.join(self.sieve, "sieve.10.txt")), expected)


class SievingTest(unittest.TestCase):
    def test_family_line(self):
        self.assertEqual(family_line(10, "6", "0", "49"), "600*10^n+49")

    def test_presieve_removes_only_small_factors(self):
        base, start, middle, end = 13, "8", "0", "111"
        kept = set(surviving_exponents(base, start, middle, end, 1, 200))
        for n in range(1, 201):
            v = int(start + middle * n + end, base)
            small = any(v % p == 0 for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29))
            self.assertEqual(n in kept, not small, n)


class SubwordTest(unittest.TestCase):
    def test_subword(self):
        self.assertEqual(subword("649", "6", "0", "49"), (True, 0))
        self.assertEqual(subword("6009", "6", "0", "49"), (True, 2))
        self.assertEqual(subword("5", "6", "0", "49"), (False, 0))


if __name__ == "__main__":
    unittest.main()
