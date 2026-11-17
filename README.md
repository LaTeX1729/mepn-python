# The Bright Algorithm

The mepn-python repository is a refactoring of https://github.com/curtisbright/mepn from C to Python using Claude.

The algorithm and the original C implementation are by **Curtis Bright**. This repository calls it the *Bright Algorithm* to credit him. It is described in:

> C. Bright, R. Devillers and J. Shallit, "Minimal elements for the prime numbers", *Experimental Mathematics* 25(3), 2016, pp. 321–331.

See the repositories https://github.com/curtisbright/mepn and https://github.com/RaymondDevillers/primes.

The srsieve program is also available at https://github.com/curtisbright/mepn-data/tree/master/srsieve.

The LLR executable is available at http://jpenne.free.fr/index2.html.

## Status

| C program (mepn) | Python | Notes |
|---|---|---|
| `minimal.c` | `bright/minimal.py` | Done. Output identical to the C program for bases 2–20. Adds a `--class a m` filter |
| `simple.c`, `search.c`, `sieving*.c`, `merge.c` | — | To do |
| `organize.c`, `check.c`, `summary.c`, `unsolved.c` | — | To do |
| `srsieve/` | — | Separate refactor, kept as the original C for now |

## Usage

Requires Python 3.8+. It runs with no extra packages, but installing **gmpy2** is recommended for speed:

```sh
pip install gmpy2            # or: pip install -r requirements.txt
```

gmpy2 is a standalone library, not part of a larger package. It wraps GMP, the same arithmetic library the original C code uses, and ships ready-made for Windows, macOS and Linux. With it installed, primality testing uses GMP's own `mpz_probab_prime_p`, exactly as in the C version. To check which is in use:

```sh
python -c "import bright.primality as p; print(p.BACKEND)"   # gmpy2 or pure-python
```

Run it as follows:

```sh
python -m bright.minimal 2 10         # bases 2 to 10
python -m bright.minimal 17           # a single base
python -m bright.minimal resume 17 8  # resume base 17 after iteration 8
```

### Filtering by residue class

`--class a m` restricts the search to primes p ≡ a (mod m). The program then computes the minimal elements of that set: the primes in the class that contain no smaller prime from the class as a subsequence of their digits.

```sh
python -m bright.minimal 10 --class 1 4    # base 10, primes = 1 mod 4
python -m bright.minimal 2 16 --class 2 3  # bases 2-16, primes = 2 mod 3
```

Results go to files tagged with the class, e.g. `data/minimal.10.1mod4.txt` and `iter/minimal-base10.1mod4-iter3.txt`, so they don't overwrite unfiltered runs.

This is an extension, not part of Bright's original program. Two changes keep the algorithm correct:

* **Adding primes:** a prime joins the set only if it is in the class.
* **Ruling out families:** a family is discarded when none of its members can be in the class. The program tracks which remainders mod m the family's members can reach, the same technique the original uses mod 30.

When gcd(a, m) > 1, every member of the class is divisible by gcd(a, m). The answer is then at most one prime (a itself, or m when a = 0), and it is given directly.

The filter was checked by brute force on 108 combinations of base (2–16) and class (moduli 3–12). For each, every prime in the class below about 2·10⁷ was listed and its minimal elements computed directly. There were no disagreements. 47 runs finished with nothing unsolved and matched the brute force exactly. In 19 more, everything the brute force found but the program didn't report lies in one of the program's unsolved families. The remaining 42 took over 30 seconds and were not checked.

**Limitation:** some classes are much harder than the unfiltered problem. In base 10 with m = 7, for example, very few families can be ruled out early, so the search grows to tens of thousands of open families and can take a very long time.

As with the C program, results go to `data/minimal.<b>.txt` and (if any families remain) `data/unsolved.<b>.txt`, with per-iteration snapshots in `iter/`. Progress lines (`base … iteration … split … size … remain …`) are printed to standard output.

From Python:

```python
from bright.minimal import compute_base
primes, unsolved = compute_base(10, log=None, write_files=False)
```

## How the translation was checked

The original `minimal.c` was compiled and run next to the Python version. For every base from 2 to 20, these outputs are byte-for-byte identical:

* the progress output,
* every per-iteration file in `iter/`, and
* the final `data/minimal.<b>.txt` and `data/unsolved.<b>.txt`.

Identical iteration files mean the Python takes the same path through the search as the C, not just the same final answer.

Against `data-minimal-sets/`, the Python output never contains a prime that isn't in the reference set. Every reference prime it doesn't output lies in one of the reported unsolved families; in the C pipeline those are found later by `simple`/`search`.

### Speed

Profiling showed most of the time going to string work, not big-number arithmetic: testing whether a candidate contains an already-found prime as a subsequence, and building test numbers inside the divisibility checks. Both now run largely inside Python's C-implemented string and regular-expression routines. Timings without gmpy2:

| Base | C | Python |
|---|---|---|
| 16 | 0.8 s | 1.7 s |
| 17 | 6.8 s | 11.6 s |
| 19 | 42 s | 68 s |
| 20 | 1.3 s | 3.1 s |

gmpy2 matters more in higher bases, where the primes being tested run to hundreds of digits.

Run the tests with:

```sh
python -m unittest discover tests
```

## Notes on the original C code

* **It gives wrong results on current Linux.** `minimal.c` builds strings with `sprintf(str, "%s%c", str, c)`, which reads and writes the same buffer. glibc 2.37 and later no longer appends in this case; it overwrites. Compiled as-is on a modern system, the program finds only 6 of the 8 base-5 minimal primes and then loops forever. The Python version uses the intended "append" behaviour. To rebuild the C for comparison, route `sprintf` through a temporary buffer.
* **Resuming reads from a closed file.** `minimal resume b i` reads the unsolved families through the kernel file handle it has just closed. This is undefined behaviour. It currently works only because glibc reuses the closed handle's memory for the next file opened. The Python version reads `iter/unsolved-base<b>-iter<i>.txt` directly. A resumed run gives the same results as a full run (checked on base 13 from iteration 5).
* **Primality testing.** The C code uses GMP's `mpz_probab_prime_p(n, 25)`. Without `gmpy2`, the Python uses a Baillie–PSW test (deterministic Miller–Rabin below 3.3·10²⁴). No Baillie–PSW pseudoprime is known.
