# Computed minimal sets

Minimal sets computed with this repository's code that are not in `data-minimal-sets/`. That folder stays exactly as published, as the reference for the tests. File names follow `data/`: `minimal.<b>.<a>mod<m>.txt` holds the minimal primes of base b that are ≡ a (mod m). A set that is not complete also has an `unsolved.<b>.<a>mod<m>.txt` file listing its open families.

All 103 sets below are **complete**: no families remain open.

## Coverage

The project computes the classes modulo 2, 3, 4, 6 and 8 with gcd(a, m) = 1 in the bases with at most two terminal digits: 2, 3, 4, 5, 6, 8, 10, 12, 14, 18, 20, 24, 30, 42 and 60 (see `reports/terminal-digits.tex`). That is 165 sets, of which 102 are complete here. Base 16, 3 mod 4 is the worked example from the main README. The status of the remaining 63 sets is in `reports/class-minimal-sets.tex`.

## Unrestricted sets

Minimal sets for all primes, in bases with no published set in `data-minimal-sets/`.

| Base | Primes | Longest (digits) | `simple` lengths | `search` lengths | Commit |
|---|---|---|---|---|---|
| 60 | 16,146 | 1,938 | 1–300 | 300–1937 | 30b4978 |

Base 60 has two possible terminal digits, 1 and 49 (`n`), since every other unit below 60 is prime (`reports/terminal-digits.tex`). Every multi-digit element ends in one of them: 7,548 in 1 and 8,581 in `n`. The longest is e^1937 1. The set passed checks 1–3 below (check 4 needs a published set). It took about 35 minutes on one core, most of it in the first round of `minimal`, which went through about 78,000 families.

## Sets

| Base | Class | Primes | Longest (digits) | `simple` lengths | `search` lengths | Commit |
|---|---|---|---|---|---|---|
| 2 | 1 mod 2 | 1 | 2 | not needed | — | 5f7a5a5 |
| 2 | 1 mod 3 | 1 | 3 | not needed | — | 5f7a5a5 |
| 2 | 2 mod 3 | 1 | 2 | not needed | — | 5f7a5a5 |
| 2 | 1 mod 4 | 1 | 3 | not needed | — | 5f7a5a5 |
| 2 | 3 mod 4 | 1 | 2 | not needed | — | 5f7a5a5 |
| 2 | 1 mod 6 | 1 | 3 | not needed | — | 5f7a5a5 |
| 2 | 5 mod 6 | 1 | 3 | not needed | — | 5f7a5a5 |
| 2 | 1 mod 8 | 2 | 39 | 1–36 | — | 5f7a5a5 |
| 2 | 3 mod 8 | 1 | 2 | not needed | — | 5f7a5a5 |
| 2 | 5 mod 8 | 1 | 3 | not needed | — | 5f7a5a5 |
| 2 | 7 mod 8 | 1 | 3 | not needed | — | 5f7a5a5 |
| 3 | 1 mod 2 | 4 | 3 | not needed | — | 5f7a5a5 |
| 3 | 1 mod 3 | 2 | 3 | not needed | — | 5f7a5a5 |
| 3 | 2 mod 3 | 1 | 1 | not needed | — | 5f7a5a5 |
| 3 | 1 mod 4 | 5 | 5 | not needed | — | 5f7a5a5 |
| 3 | 3 mod 4 | 2 | 2 | not needed | — | 5f7a5a5 |
| 3 | 1 mod 6 | 2 | 3 | not needed | — | 5f7a5a5 |
| 3 | 5 mod 6 | 1 | 2 | not needed | — | 5f7a5a5 |
| 3 | 1 mod 8 | 29 | 36 | 1–32 | — | 5f7a5a5 |
| 3 | 3 mod 8 | 4 | 4 | not needed | — | 5f7a5a5 |
| 3 | 5 mod 8 | 3 | 4 | not needed | — | 5f7a5a5 |
| 3 | 7 mod 8 | 8 | 9 | not needed | — | 5f7a5a5 |
| 4 | 1 mod 2 | 3 | 3 | not needed | — | 5f7a5a5 |
| 4 | 1 mod 3 | 18 | 12,702 | 1–300 | 300–12700 | 6942fcf |
| 4 | 2 mod 3 | 2 | 2 | not needed | — | 5f7a5a5 |
| 4 | 1 mod 4 | 3 | 3 | not needed | — | 5f7a5a5 |
| 4 | 3 mod 4 | 1 | 1 | not needed | — | 5f7a5a5 |
| 4 | 1 mod 6 | 18 | 12,702 | 1–300 | 300–12700 | 6942fcf |
| 4 | 5 mod 6 | 3 | 3 | not needed | — | 5f7a5a5 |
| 4 | 1 mod 8 | 9 | 20 | 1–17 | — | 5f7a5a5 |
| 4 | 3 mod 8 | 1 | 1 | not needed | — | 5f7a5a5 |
| 4 | 5 mod 8 | 2 | 2 | not needed | — | 5f7a5a5 |
| 4 | 7 mod 8 | 2 | 3 | not needed | — | 5f7a5a5 |
| 5 | 1 mod 2 | 9 | 5 | 1–4 | — | 5f7a5a5 |
| 5 | 1 mod 3 | 49 | 206 | 1–203 | — | ae2a7b7 |
| 5 | 2 mod 3 | 7 | 4 | not needed | — | ae2a7b7 |
| 5 | 1 mod 4 | 80 | 86 | 1–83 | — | 5f7a5a5 |
| 5 | 3 mod 4 | 4 | 3 | not needed | — | 5f7a5a5 |
| 5 | 1 mod 6 | 49 | 206 | 1–203 | — | 5f7a5a5 |
| 5 | 5 mod 6 | 19 | 54 | 1–51 | — | 5f7a5a5 |
| 5 | 3 mod 8 | 60 | 947 | 1–300 | 300–942 | ae2a7b7 |
| 6 | 1 mod 2 | 7 | 5 | not needed | — | 5f7a5a5 |
| 6 | 1 mod 3 | 7 | 5 | not needed | — | 5f7a5a5 |
| 6 | 2 mod 3 | 2 | 1 | not needed | — | 5f7a5a5 |
| 6 | 1 mod 4 | 10 | 6 | 1–4 | — | 5f7a5a5 |
| 6 | 3 mod 4 | 6 | 3 | not needed | — | 5f7a5a5 |
| 6 | 1 mod 6 | 7 | 5 | not needed | — | 5f7a5a5 |
| 6 | 5 mod 6 | 1 | 1 | not needed | — | 5f7a5a5 |
| 6 | 1 mod 8 | 75 | 79 | 1–76 | — | 5f7a5a5 |
| 6 | 3 mod 8 | 8 | 4 | not needed | — | 5f7a5a5 |
| 6 | 5 mod 8 | 7 | 6 | not needed | — | 5f7a5a5 |
| 6 | 7 mod 8 | 10 | 7 | 1–6 | — | 5f7a5a5 |
| 8 | 1 mod 2 | 15 | 9 | 1–8 | — | 5f7a5a5 |
| 8 | 1 mod 4 | 38 | 13 | 1–13 | — | 5f7a5a5 |
| 8 | 3 mod 4 | 2 | 1 | not needed | — | 5f7a5a5 |
| 8 | 1 mod 8 | 38 | 13 | 1–13 | — | 5f7a5a5 |
| 8 | 3 mod 8 | 1 | 1 | not needed | — | 5f7a5a5 |
| 8 | 5 mod 8 | 1 | 1 | not needed | — | 5f7a5a5 |
| 8 | 7 mod 8 | 1 | 1 | not needed | — | 5f7a5a5 |
| 10 | 1 mod 2 | 33 | 8 | 1–5 | — | 5f7a5a5 |
| 10 | 2 mod 3 | 251 | 66 | 1–65 | — | 5f7a5a5 |
| 10 | 1 mod 4 | 146 | 79 | 1–77 | — | 5f7a5a5 |
| 10 | 3 mod 4 | 113 | 19,153 | 1–300 | 300–19151 | e7ba51b |
| 10 | 5 mod 6 | 309 | 66 | 1–65 | — | 5f7a5a5 |
| 10 | 3 mod 8 | 439 | 19,153 | 1–300 | 300–19151; 1 family covered | 6942fcf |
| 10 | 5 mod 8 | 868 | 960 | 1–300 | 300–957; 1 family covered | 6942fcf |
| 12 | 1 mod 2 | 22 | 8 | 1–5 | — | 5f7a5a5 |
| 12 | 1 mod 3 | 40 | 8 | 1–5 | — | 5f7a5a5 |
| 12 | 2 mod 3 | 3 | 1 | not needed | — | 5f7a5a5 |
| 12 | 1 mod 4 | 52 | 8 | 1–5 | — | 5f7a5a5 |
| 12 | 3 mod 4 | 3 | 1 | not needed | — | 5f7a5a5 |
| 12 | 1 mod 6 | 40 | 8 | 1–5 | — | 5f7a5a5 |
| 12 | 5 mod 6 | 2 | 1 | not needed | — | 5f7a5a5 |
| 12 | 3 mod 8 | 132 | 7,735 | 1–300 | 300–7733 | ae2a7b7 |
| 12 | 5 mod 8 | 63 | 45 | 1–43 | — | 5f7a5a5 |
| 12 | 7 mod 8 | 103 | 30 | 1–27 | — | 5f7a5a5 |
| 14 | 1 mod 2 | 241 | 86 | 1–83 | — | 5f7a5a5 |
| 14 | 1 mod 4 | 1,402 | 12,442 | 1–300 | 300–12439 | 6942fcf |
| 16 | 3 mod 4 | 359 | 1,519 | 1–100 | 100–1517 | 32518ac |
| 18 | 1 mod 2 | 50 | 33 | 1–30 | — | 5f7a5a5 |
| 18 | 1 mod 3 | 111 | 33 | 1–30 | — | 5f7a5a5 |
| 18 | 2 mod 3 | 4 | 1 | not needed | — | 5f7a5a5 |
| 18 | 1 mod 6 | 111 | 33 | 1–30 | — | 5f7a5a5 |
| 18 | 5 mod 6 | 3 | 1 | not needed | — | 5f7a5a5 |
| 20 | 1 mod 2 | 917 | 449 | 1–300 | 300–447 | 5f7a5a5 |
| 20 | 1 mod 4 | 1,380 | 1,587 | 1–300 | 300–1585 | 5f7a5a5 |
| 20 | 3 mod 4 | 4 | 1 | not needed | — | 5f7a5a5 |
| 24 | 1 mod 2 | 360 | 100 | 1–98 | — | 5f7a5a5 |
| 24 | 1 mod 3 | 811 | 100 | 1–98 | — | 5f7a5a5 |
| 24 | 2 mod 3 | 5 | 1 | not needed | — | 5f7a5a5 |
| 24 | 1 mod 4 | 648 | 100 | 1–98 | — | 5f7a5a5 |
| 24 | 3 mod 4 | 5 | 1 | not needed | — | 5f7a5a5 |
| 24 | 1 mod 6 | 811 | 100 | 1–98 | — | 5f7a5a5 |
| 24 | 5 mod 6 | 4 | 1 | not needed | — | 5f7a5a5 |
| 24 | 1 mod 8 | 891 | 100 | 1–98 | — | 5f7a5a5 |
| 24 | 3 mod 8 | 3 | 1 | not needed | — | 5f7a5a5 |
| 24 | 5 mod 8 | 2 | 1 | not needed | — | 5f7a5a5 |
| 24 | 7 mod 8 | 2 | 1 | not needed | — | 5f7a5a5 |
| 30 | 1 mod 2 | 220 | 1,024 | 1–300 | 300–1022 | 5f7a5a5 |
| 30 | 1 mod 3 | 489 | 1,024 | 1–300 | 300–1022 | 5f7a5a5 |
| 30 | 2 mod 3 | 6 | 1 | not needed | — | 5f7a5a5 |
| 30 | 1 mod 6 | 489 | 1,024 | 1–300 | 300–1022 | 5f7a5a5 |
| 30 | 5 mod 6 | 5 | 1 | not needed | — | 5f7a5a5 |

**Search lengths** are the repeat counts n tested in families x yⁿ z. `simple` stops as soon as no families are left, so its range ends at the length where the last family was solved. Likewise `search` ends at the exponent of the last family's prime. "Not needed" means `minimal` left no open families.

**How they were computed.** `python -m bright minimal B --class a m`, then `simple 1 300` and `organize`. Where families remained, this was followed by `sieve-start 300 3000`, `sieve B --class a m --pmax 1e6`, `search 300 3000` and `organize`. Base 16, 3 mod 4 used 100 and 2000 instead of 300 and 3000. Sets at commit ae2a7b7 or later used `search 300 10000` (and, where needed, further searches in steps of 10,000) with GMP's `mpz_probab_prime_p` called directly (no gmpy2 or LLR); the others used the built-in test. Commit ae2a7b7 adds a test for class runs that lets the base-5 sets finish; rerunning the 92 earlier class sets with it reproduced every one exactly.

**Covered families.** "1 family covered" means that the last open families were removed by `python -m bright covering`, which proves that a family has no member in the class: for a period L, every member x yⁿ z is divisible by a small prime or lies outside the class, according to n mod L. The certificates are in `covered.<b>.<a>mod<m>.txt` next to the set, one family per line, and were also checked on the actual numbers for n ≤ 600.

**Checks.** Every set was checked independently of the program:

1. each entry is a probable prime in the class;
2. no entry contains another as a subsequence;
3. every prime in the class below 2·10⁷ contains an entry;
4. where a published set exists in `data-minimal-sets/` (every base here except 60), each published minimal prime that lies in the class appears in the computed set. A minimal prime of the full set is also minimal for any class that contains it, so this checks the computed sets against independent data.

The base-10, 1 mod 4 set (146 primes, the longest with 79 digits) also agrees with the figures given by Bright, Devillers and Shallit.

**Notes.**

* 1 mod 6 gives the same set as 1 mod 3 in every base, because every prime ≡ 1 (mod 3) is odd.
* 5 mod 6 is 2 mod 3 without the prime 2: it drops 2 and gains the primes that 2 used to rule out (in base 10, for example, 2087 and 20021).
* 1 mod 2 is the set for the odd primes, which is the published set with 2 removed plus the odd primes that 2 used to rule out.
* In bases 12 and 20, 3 mod 4, the sets are just the one-digit primes in the class. Since the base is ≡ 0 (mod 4), the last digit alone fixes the residue mod 4. Every digit ≡ 3 (mod 4) that is coprime to the base is itself prime (3, 7, 11, and 19 in base 20), and in base 20 a number ending in 15 is divisible by 5.
