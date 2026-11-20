# Computed minimal sets

Minimal sets computed with this repository's code that are not in `data-minimal-sets/`. That folder stays exactly as published, as the reference for the tests. File names follow `data/`: `minimal.<b>.<a>mod<m>.txt` holds the minimal primes of base b that are ≡ a (mod m). A set that is not complete also has an `unsolved.<b>.<a>mod<m>.txt` file listing its open families.

| Base | Class | Primes | Longest (digits) | Status | `simple` lengths | `search` lengths | Commit | Date |
|---|---|---|---|---|---|---|---|---|
| 10 | 1 mod 4 | 146 | 79 | complete | 1–77 | — | 32518ac | 2026-11-19 |
| 10 | 2 mod 3 | 251 | 66 | complete | 1–65 | — | 32518ac | 2026-11-19 |
| 12 | 1 mod 3 | 40 | 8 | complete | 1–5 | — | 32518ac | 2026-11-19 |
| 12 | 1 mod 4 | 52 | 8 | complete | 1–5 | — | 32518ac | 2026-11-19 |
| 12 | 3 mod 4 | 3 | 1 | complete | not needed | — | 32518ac | 2026-11-19 |
| 16 | 3 mod 4 | 359 | 1,519 | complete | 1–100 | 100–1517 | 32518ac | 2026-11-19 |
| 20 | 3 mod 4 | 4 | 1 | complete | not needed | — | 32518ac | 2026-11-19 |

**Search lengths** are the repeat counts n tested in families x yⁿ z. `simple` stops as soon as no families are left, so its range ends at the length where the last family was solved. Likewise `search` ends at the exponent of the last family's prime: in base 16, 3 mod 4, that is F 8^1517 F. For an incomplete set, these columns give how far each program has got, and every remaining minimal prime has more repeated digits than that.

**How they were computed.** `python -m bright minimal B --class a m`, then `simple 1 100` and `organize`. Where families remained, this was followed by `sieve-start 100 2000`, `sieve B --class a m --pmax 1e6`, `search 100 2000` and `organize`. The built-in primality test was used (no gmpy2 or LLR).

**Checks.** Every set was checked independently of the program. Each entry is a probable prime in the class, no entry contains another as a subsequence, and every prime in the class below 2·10⁷ contains an entry. The base-10, 1 mod 4 set (146 primes, the longest with 79 digits) agrees with the figures given by Bright, Devillers and Shallit.

**Notes.** In bases 12 and 20, 3 mod 4, the sets are just the one-digit primes in the class. Since the base is ≡ 0 (mod 4), the last digit alone fixes the residue mod 4. Every digit ≡ 3 (mod 4) that is coprime to the base is itself prime (3, 7, 11, and 19 in base 20), and in base 20 a number ending in 15 is divisible by 5.
