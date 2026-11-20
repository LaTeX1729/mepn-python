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

    def test_simple_stops_when_nothing_is_left(self):
        os.makedirs(self.data)
        with open(os.path.join(self.data, "unsolved.10.txt"), "w") as fh:
            fh.write("1*\n")
        out = io.StringIO()
        run_simple(1, 1000, datadir=self.data, out=out)
        lines = out.getvalue().splitlines()
        self.assertIn("1^(2) (base 10) probably prime", lines)
        self.assertEqual(lines[-2], "FINISHED LEVEL 2, COUNT REMAINING 0, TIME %s"
                         % lines[-2].split("TIME ")[1])
        self.assertEqual(lines[-1], "No unsolved families left; stopping")

    def test_simple_records_progress_and_continues(self):
        from bright.simple import read_progress
        os.makedirs(self.data)
        with open(os.path.join(self.data, "unsolved.10.txt"), "w") as fh:
            fh.write("8*\n")  # always even, so it stays open
        progress = os.path.join(self.data, "simple.10.txt")
        run_simple(1, 5, datadir=self.data, out=self.quiet)
        self.assertEqual(read_progress(progress), 5)
        out = io.StringIO()
        run_simple(None, 8, datadir=self.data, out=out)
        self.assertIn("base 10: continuing from length 6", out.getvalue())
        self.assertNotIn("FINISHED LEVEL 5,", out.getvalue())
        self.assertEqual(read_progress(progress), 8)
        run_simple(20, 22, datadir=self.data, out=self.quiet)  # a gap: not recorded
        self.assertEqual(read_progress(progress), 8)

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

    def test_merge_accepts_srsieve_dropping_k_equal_1(self):
        # srsieve rewrites the family 1* (base 10) as 10^n-1, without "1*"
        os.makedirs(self.data)
        os.makedirs(self.sieve)
        with open(os.path.join(self.data, "sieve.10.txt"), "w") as fh:
            fh.write("pmin=31\n1*10^n-1\n23\n25\n29\n")
        with open(os.path.join(self.sieve, "sieve.10.txt"), "w") as fh:
            fh.write("pmin=124\n10^n-1\n23\n29\n")
        merge(self.data, self.sieve)
        expected = ["pmin=124", "1*10^n-1", "23", "29"]
        self.assertEqual(read_lines(os.path.join(self.data, "sieve.10.txt")), expected)
        self.assertEqual(read_lines(os.path.join(self.sieve, "sieve.10.txt")), expected)


    def test_sieve_start_leaves_out_families_with_no_terms(self):
        # In base 30, every member of A*1 and C*D is 1 mod 4, so with
        # --class 3 4 they have nothing to sieve; srsieve rejects such a family.
        os.makedirs(self.data)
        with open(os.path.join(self.data, "unsolved.30.3mod4.txt"), "w") as fh:
            fh.write("A*1\nB0*7\nC*D\n")
        start_sieve(100, 200, datadir=self.data, sievedir=self.sieve)
        header, blocks = parse_sieve(read_lines(os.path.join(self.data, "sieve.30.3mod4.txt")))
        self.assertEqual([f for f, _ in blocks], ["330*30^n+7"])
        self.assertTrue(blocks[0][1])


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


class LLRTest(unittest.TestCase):
    def test_output_parsing(self):
        from bright.search import parse_llr_output
        self.assertEqual(parse_llr_output("(5*12^9+1)/1 is base 3-Strong Fermat PRP! (9 decimal digits)"), "PRP")
        self.assertEqual(parse_llr_output("5*12^9-1 is prime! (10 decimal digits)  Time : 0.1 sec."), "PRP")
        self.assertEqual(parse_llr_output("(5*12^9+1)/11 is not prime.  RES64: 0123456789ABCDEF"), "composite")
        self.assertIsNone(parse_llr_output("Error"))

    def test_finds_bundled_names(self):
        from bright.search import LLR_NAMES
        from bright.sieving import find_executable, platform_dir
        d = platform_dir()
        os.makedirs(d, exist_ok=True)
        name = "sllr64" if os.name != "nt" else "cllr64.exe"
        path = os.path.join(d, name)
        if os.path.exists(path):
            self.skipTest("a real LLR is installed")
        with open(path, "w") as fh:
            fh.write("")
        try:
            os.chmod(path, 0o755)
            self.assertEqual(find_executable(LLR_NAMES, "BRIGHT_LLR_UNSET"), os.path.abspath(path))
        finally:
            os.remove(path)


class SubwordTest(unittest.TestCase):
    def test_subword(self):
        self.assertEqual(subword("649", "6", "0", "49"), (True, 0))
        self.assertEqual(subword("6009", "6", "0", "49"), (True, 2))
        self.assertEqual(subword("5", "6", "0", "49"), (False, 0))


if __name__ == "__main__":
    unittest.main()


class CommandLineTest(unittest.TestCase):
    def test_parse_bases(self):
        from bright.minimal import parse_bases
        self.assertEqual(parse_bases(["2", "5"]), [2, 3, 4, 5])
        self.assertEqual(parse_bases(["10"]), [10])
        self.assertEqual(parse_bases(["2-4,10,30-31"]), [2, 3, 4, 10, 30, 31])
        self.assertEqual(parse_bases(["[b for b in range(2, 13) if b % 4 == 0]"]), [4, 8, 12])
        self.assertEqual(parse_bases(["[b for b in range(2, 17) if not isprime(b)]"]),
                         [4, 6, 8, 9, 10, 12, 14, 15, 16])
        for bad in (["70"], ["[1, 2]"], ['__import__("os")']):
            with self.assertRaises(ValueError):
                parse_bases(bad)

    def test_coprime_residues(self):
        from bright.minimal import coprime_residues
        self.assertEqual(coprime_residues(8), [1, 3, 5, 7])
        self.assertEqual(coprime_residues(12), [1, 5, 7, 11])

    def test_class_m_runs_every_coprime_class(self):
        import contextlib
        from bright.minimal import main
        d = tempfile.mkdtemp()
        old = os.getcwd()
        try:
            os.chdir(d)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["10,12", "--class", "4"])
            names = sorted(n for n in os.listdir("data") if n.startswith("minimal"))
            self.assertEqual(names, ["minimal.10.1mod4.txt", "minimal.10.3mod4.txt",
                                     "minimal.12.1mod4.txt", "minimal.12.3mod4.txt"])
        finally:
            os.chdir(old)
            shutil.rmtree(d)


class CoveringTest(unittest.TestCase):
    def test_finds_period_6_covering(self):
        from bright.covering import find_covering
        L, cert = find_covering(10, "", "1", "221", (5, 8))
        self.assertEqual(L, 6)
        for n in range(200):
            v = int("1" * n + "221")
            self.assertEqual(v % cert[n % 6], 0)

    def test_no_covering_when_a_prime_exists(self):
        from bright.covering import find_covering
        self.assertIsNone(find_covering(16, "F", "8", "F", (3, 4)))  # F 8^1517 F
        self.assertIsNone(find_covering(10, "", "8", "9", None))     # 89 is prime

    def test_command_removes_covered_family(self):
        import contextlib
        from bright.covering import run_covering
        d = tempfile.mkdtemp()
        try:
            with open(os.path.join(d, "unsolved.10.1mod3.txt"), "w") as fh:
                fh.write("1*221\n8*9\n")
            with contextlib.redirect_stdout(io.StringIO()):
                run_covering(datadir=d, out=io.StringIO())
            self.assertEqual(read_lines(os.path.join(d, "unsolved.10.1mod3.txt")), ["8*9"])
            cov = read_lines(os.path.join(d, "covered.10.1mod3.txt"))
            self.assertEqual(len(cov), 1)
            self.assertTrue(cov[0].startswith("1*221  period 6"))
        finally:
            shutil.rmtree(d)
