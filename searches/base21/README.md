# Base 21: the family G{0}FK

Base 21 has one unsolved family, `G{0}FK` (written `G0*FK` by this program). Its members are

    G 0^n FK (base 21) = 7056 · 21^n + 335,

and a prime in it would complete the minimal set for base 21. The family has no covering set and no algebraic factorization (`reports/covering.tex`), so it has to be searched.

**Where the search starts.** Bright, Devillers and Shallit (January 2015) give a searched height of 260,000 for base 21. The prime C F^479149 0K, which settled the other base-21 family, implies the search reached at least about 480,000. This sieve therefore covers **n = 480,000 to 1,000,000**. Check the current status before testing: others may have gone further.

**Files**

| File | Contents |
|---|---|
| `sieve.21.txt` | the surviving exponents, in this program's sieve format (`pmin=` line, family, exponents) |
| `G0FK.abc` | the same exponents as an LLR input file (`ABC 7056*21^$a+335`) |
| `unsolved.21.txt` | the family, for `search` |
| `progress.txt` | one line per sieving session: sieve limit and number of candidates |

The sieve limit is the `pmin=` value in `sieve.21.txt`. Every exponent removed has a prime factor below that limit. Sieving is done with srsieve in check-ins and the files here are updated after each one.

**Testing with LLR directly** (fastest; run in a folder of its own):

    sllr64 -d G0FK.abc

LLR works through the file in order and records results in `lresults.txt`. Any result other than "not prime" is a candidate prime; check it again with another program before announcing it.

**Testing with this program** (it then updates the files as it goes):

    mkdir -p ~/runs/b21/data && cd ~/runs/b21
    cp ~/mepn-python/searches/base21/sieve.21.txt ~/mepn-python/searches/base21/unsolved.21.txt data/
    cp ~/mepn-python/data-minimal-sets/minimal.21.txt data/
    PYTHONPATH=~/mepn-python python -m bright search -

`search -` tests the exponents in increasing order, removes each composite from `data/sieve.21.txt` and stops when it finds a prime, which it adds to `data/minimal.21.txt`.

**Cost.** At n = 480,000 a member has about 635,000 decimal digits. One test takes many hours with GMP; LLR is much faster. Heuristically, the range 480,000–1,000,000 holds about 0.5 primes of this family (`reports/complexity.tex`), a chance of roughly 40% of finding one.

**Deeper sieving on a GPU.** Mark Rodenkirch's mtsieve (with OpenCL) can continue the sieve on a graphics card, starting from the `pmin=` value here.
