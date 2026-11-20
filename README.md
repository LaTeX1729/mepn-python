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
| `minimal.c` | `bright/minimal.py` | Output identical to the C for bases 2–20 and 36. Extends to bases up to 62 and adds a `--class a m` filter |
| `simple.c` | `bright/simple.py` | Output identical to the C |
| `organize.c` | `bright/organize.py` | Output identical to the C |
| `sieving.start.c`, `sieving.c`, `merge.c` | `bright/sieving.py` | Output identical to the C. Calls srsieve |
| `search.c` | `bright/search.py` | Same tests and results as the C. Uses LLR if present, otherwise a built-in test |
| `check.c`, `summary.c`, `unsolved.c` | — | Not translated (optional verification and reporting tools) |
| `srsieve/` | `bin/` | srsieve stays in C. Tested executables for Windows and Linux are included |

## Bases and digits

Bases 2 to 62 are supported. Digits are `0`–`9`, then `A`–`Z` (10–35), then `a`–`z` (36–61). For example, in base 60 the digit `x` is 59. This is GMP's convention and the one used in `data-minimal-sets`. Bases up to 36 use only uppercase letters, as in the original C, which stops at base 36.

## Usage

Requires Python 3.8+. It runs with no extra packages, but installing **gmpy2** is recommended for speed:

```sh
pip install gmpy2            # or: pip install -r requirements.txt
```

gmpy2 is a standalone library, not part of a larger package. It wraps GMP, the same arithmetic library the original C code uses, and ships ready-made for Windows, macOS and Linux. With it installed, primality testing uses GMP's own `mpz_probab_prime_p`, exactly as in the C version.

Without gmpy2, the program looks for the GMP library itself (`libgmp`, present on most Linux systems, WSL included) and calls `mpz_probab_prime_p` directly. That is the same routine at the same speed. Only if neither is available does it fall back to a built-in Python test, which is about 15 times slower at 3,000 digits and impractical beyond about 10,000. To check which is in use:

```sh
python -c "import bright.primality as p; print(p.BACKEND)"   # gmpy2, libgmp or pure-python
```

Set `BRIGHT_NO_LIBGMP=1` to skip the direct libgmp call.

### The full pipeline

All commands run from the folder where `data/` should be kept:

```sh
python -m bright minimal 2 20            # 1. minimal primes + unsolved families
python -m bright simple 1 1000           # 2. test families at lengths 1..1000 (stops early once none are left)
                                         #    later: simple - 2000 continues from where each file stopped
python -m bright organize                # 3. sort lists, drop redundant entries
python -m bright sieve-start 1000 20000  # 4. sieve files for lengths 1000..20000
python -m bright sieve 17 --pmax 1e9     # 5. sieve base 17 with srsieve (optional, speeds up 6; one base at a time)
python -m bright search 1000 20000       # 6. test what is left (LLR if available)
python -m bright organize                # 7. tidy up again
```

`simple` records the last length it finished for each unsolved file in `data/simple.<b>.txt` (e.g. `data/simple.10.3mod4.txt`), so `python -m bright simple - M` carries on from there up to M. Only an unbroken run of lengths from 1 counts, so if you skip lengths the record stays at the last one before the gap. `minimal` deletes the record when it writes a new unsolved list. `search` needs no such record: it removes each exponent it has tested from `data/sieve.<b>.txt`, and `python -m bright search -` carries on with what is left.

`python -m bright --help` lists the commands. For example, base 20 runs completely in a few seconds:

```sh
python -m bright minimal 20
python -m bright simple 1 100
python -m bright organize
python -m bright sieve-start 100 1000
python -m bright sieve 20 --pmax 1e6
python -m bright search 100 1000
python -m bright organize      # data/minimal.20.txt now holds all 651 minimal primes
```

### How long can the primes get?

Some bases have minimal primes with tens of thousands of digits (base 13's largest is 8 0^32017 111), and the reference sets in `data-minimal-sets` go much further: the largest in base 17 has 111,334 digits, in base 21 479,150 and in base 23 800,874. Those need long sieving and searching, which is where srsieve and LLR pay off.

In general, the first prime in a simple family can be very long, or there may be none at all, and nothing in the algorithm bounds its length in advance. The family 1 0* 1 in base 10, the numbers 10^k + 1, shows how hard this can be. Such a number can be prime only when k is a power of 2. Only two primes of this form are known, 11 and 101; 10^(2^n) + 1 is known to be composite for n = 2 to 13 (OEIS A102050 lists a prime factor of each), and whether any further prime exists is an open question. (In the unfiltered base-10 run this family is settled at once, because each member contains 11. With `--class`, such families can remain open.) This is why a family can stay in `data/unsolved.<b>.txt` after `simple`, and why `search` has no natural end.

### srsieve

srsieve (by Geoffrey Reynolds, GPL; source in `srsieve/`) is included ready to run:

* `bin/windows-x64/srsieve.exe`, which needs only standard Windows system files
* `bin/linux-x64/srsieve`, statically linked

`python -m bright sieve` finds it automatically, or you can point to another copy with `--srsieve PATH` or the `BRIGHT_SRSIEVE` environment variable. Both executables are built by GitHub Actions (`.github/workflows/srsieve.yml`) and pass srsieve's full test suite before they are committed. To build it yourself, run `make` in `srsieve/`. On Windows, use MSYS2's MinGW-w64 toolchain.

The C `sieving` program stopped srsieve every two hours with the Unix `timeout` command, which Windows lacks. The Python version runs srsieve in rounds, each ending at a prime limit, so srsieve always finishes and saves normally. Ctrl-C stops it safely.

### LLR (optional)

`search` uses LLR (Jean Penné, http://jpenne.free.fr/index2.html) when it finds it. Put it here:

* Linux, including WSL: `bin/linux-x64/sllr64`
* Windows: `bin/windows-x64/cllr64.exe`, with its DLLs in the same folder

It is also found as `llr`/`llr64` in those folders, in the current folder, or on PATH, or you can set `--llr PATH` or `BRIGHT_LLR`. The first line `search` prints shows which test is in use. If LLR exists but isn't executable (unzipping on Linux can drop the permission), `search` tells you to run `chmod +x`. LLR writes its own files (such as `lresults.txt`, `llr.ini`) in the folder you run from.

`search` accepts LLR's "PRP" results, and also proven primes ("is prime!"), which LLR reports for forms like k·bⁿ±1. `search.c` only recognised "PRP" and would retry such a number forever.

Without LLR, the built-in test is used. It is fine for numbers with a few thousand digits; LLR is much faster beyond that. Use `--no-llr` to force the built-in test.

### Filtering by residue class

`--class a m` restricts the search to primes p ≡ a (mod m). The program then computes the minimal elements of that set: the primes in the class that contain no smaller prime from the class as a subsequence of their digits.

```sh
python -m bright minimal 10 --class 1 4   # base 10, primes = 1 mod 4
python -m bright minimal 2 16 --class 2 3  # bases 2-16, primes = 2 mod 3
```

To run every class a mod m with gcd(a, m) = 1, give only the modulus. The bases can be a range, a list, or a Python list comprehension (in quotes):

```sh
python -m bright minimal 10 --class 8                     # base 10: 1, 3, 5 and 7 mod 8
python -m bright minimal 2-16,30 --class 4                # these bases, 1 and 3 mod 4
python -m bright minimal "[b for b in range(2, 37) if b % 2 == 0]" --class 3
python -m bright minimal "[b for b in range(2, 37) if not isprime(b)]" --class 4   # composite bases only
```

In a list comprehension you can use `range`, `isprime`, `gcd`, `isqrt`, `all`, `any`, `min`, `max`, `len` and `sorted`.

Classes with gcd(a, m) > 1 are skipped, since each holds at most one prime. `sieve` accepts the same forms, e.g. `sieve 10 --class 8`, and sieves each class that has a sieve file. Put the bases before `--class`.

Verified minimal sets for several classes are kept in [`data-computed/`](data-computed/README.md), with how far each search went. `data-minimal-sets/` holds only the published reference sets.

Results go to files tagged with the class, e.g. `data/minimal.10.1mod4.txt` and `iter/minimal-base10.1mod4-iter3.txt`, so they don't overwrite unfiltered runs.

The rest of the pipeline works the same way. `simple`, `organize`, `sieve-start` and `search` handle every file in `data/`, tagged or not, so they need no extra option. Only `sieve` needs `--class` again, because it works on one base and class at a time.

For example, base 16 with primes = 3 mod 4 runs completely in about 10 seconds:

```sh
python -m bright minimal 16 --class 3 4
python -m bright simple 1 100
python -m bright organize       # 8 families left, e.g. F8*F
python -m bright sieve-start 100 2000
python -m bright sieve 16 --class 3 4 --pmax 1e6
python -m bright search 100 2000
python -m bright organize       # data/minimal.16.3mod4.txt now holds all 359 minimal primes
```

The last family to fall is F8*F, whose first prime in the class is F 8^1517 F, with 1,519 digits. The result was checked independently: all 359 numbers are probable primes ≡ 3 (mod 4), none contains another as a subsequence, and every prime ≡ 3 (mod 4) below 16⁶ contains one of them.

Other bases and classes follow the same pattern, e.g. `minimal 30 --class 3 4` and `sieve 30 --class 3 4`, but may need much longer ranges in `sieve-start` and `search`.

This is an extension, not part of Bright's original program. Two changes keep the algorithm correct:

* **Adding primes:** a prime joins the set only if it is in the class.
* **Ruling out families:** a family is discarded when none of its members can be in the class. The program tracks which remainders mod m the family's members can reach, the same technique the original uses mod 30.

`sieve-start` also applies the class: exponents whose member is outside the class are dropped, and a family with nothing left in the range is left out of the sieve file (it stays in `data/unsolved.<b>.<a>mod<m>.txt`).

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

The follow-up programs were also checked against their C versions on the unsolved families of bases 2–20: `simple` (lengths 1–400), `organize`, `sieve-start` (lengths 400–1500), sieving to p = 10⁶ with `merge`, and `search` (lengths 400–1000). Every data file came out identical. After `simple` and `organize`, 14 of the 19 bases are complete and match `data-minimal-sets` exactly.

GitHub Actions (`.github/workflows/tests.yml`) runs the tests and a complete base-20 run on Windows and Linux, with and without gmpy2.

Run the tests with:

```sh
python -m unittest discover tests
```

## Notes on the original C code

* **It gives wrong results on current Linux.** `minimal.c` builds strings with `sprintf(str, "%s%c", str, c)`, which reads and writes the same buffer. glibc 2.37 and later no longer appends in this case; it overwrites. Compiled as-is on a modern system, the program finds only 6 of the 8 base-5 minimal primes and then loops forever. The Python version uses the intended "append" behaviour. To rebuild the C for comparison, route `sprintf` through a temporary buffer.
* **Resuming reads from a closed file.** `minimal resume b i` reads the unsolved families through the kernel file handle it has just closed. This is undefined behaviour. It currently works only because glibc reuses the closed handle's memory for the next file opened. The Python version reads `iter/unsolved-base<b>-iter<i>.txt` directly. A resumed run gives the same results as a full run (checked on base 13 from iteration 5).
* **`simple.c` has the same sprintf problem** when it builds candidates, so on current Linux it tests the wrong numbers.
* **Primality testing.** The C code uses GMP's `mpz_probab_prime_p(n, 25)`. The Python calls the same routine through gmpy2 or directly in libgmp when either is available; otherwise it uses a Baillie–PSW test (deterministic Miller–Rabin below 3.3·10²⁴). No Baillie–PSW pseudoprime is known.
