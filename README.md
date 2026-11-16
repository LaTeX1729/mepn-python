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
| `minimal.c` | `bright/minimal.py` | Done. Output identical to the C program for bases 2–20 |
| `simple.c`, `search.c`, `sieving*.c`, `merge.c` | — | To do |
| `organize.c`, `check.c`, `summary.c`, `unsolved.c` | — | To do |
| `srsieve/` | — | Separate refactor, kept as the original C for now |

## Usage

Requires Python 3.8+. No packages are needed. If [`gmpy2`](https://pypi.org/project/gmpy2/) is installed, it is used for faster primality testing.

```sh
python -m bright.minimal 2 10         # bases 2 to 10
python -m bright.minimal 17           # a single base
python -m bright.minimal resume 17 8  # resume base 17 after iteration 8
```

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

Run the tests with:

```sh
python -m unittest discover tests
```

## Notes on the original C code

* **It gives wrong results on current Linux.** `minimal.c` builds strings with `sprintf(str, "%s%c", str, c)`, which reads and writes the same buffer. glibc 2.37 and later no longer appends in this case; it overwrites. Compiled as-is on a modern system, the program finds only 6 of the 8 base-5 minimal primes and then loops forever. The Python version uses the intended "append" behaviour. To rebuild the C for comparison, route `sprintf` through a temporary buffer.
* **Resuming reads from a closed file.** `minimal resume b i` reads the unsolved families through the kernel file handle it has just closed. This is undefined behaviour. It currently works only because glibc reuses the closed handle's memory for the next file opened. The Python version reads `iter/unsolved-base<b>-iter<i>.txt` directly. A resumed run gives the same results as a full run (checked on base 13 from iteration 5).
* **Primality testing.** The C code uses GMP's `mpz_probab_prime_p(n, 25)`. Without `gmpy2`, the Python uses a Baillie–PSW test (deterministic Miller–Rabin below 3.3·10²⁴). No Baillie–PSW pseudoprime is known.
