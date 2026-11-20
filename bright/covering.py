"""Covering sets for simple families (not in the C code).

``python -m bright covering`` looks at every unsolved simple family x y* z in
data/ and tries to prove that it contains no element of the target set: that
for every n >= 0 the member x y^n z is divisible by some prime p from a small
set (and is not p itself), or, with --class, lies outside the class. Such
families are removed from data/unsolved.<b>.txt, and their certificates are
appended to data/covered.<b>.txt.

How the proof works. Let x_n be the value of x y^n modulo q. Then
x_{n+1} = x_n * b + y (mod q), so x_n is determined by x_{n-1}, and the
sequence enters a cycle after at most q steps (its "preperiod" mu_q) and then
repeats with some period pi_q. The member s(n) = x_n * b^|z| + z (mod q)
inherits this. For a period L that is a multiple of pi_q for every modulus q
used, checking every n from 0 to max(mu_q) + L - 1 therefore covers all
n >= 0: beyond that range every residue repeats one already checked.

Example: 1*221 in base 10 (class 5 mod 8). With L = 6, n = 1, 4 (mod 6) give
multiples of 3; n = 3, 5 multiples of 11; n = 0 of 13; n = 2 of 7. The
periodic test in ``minimal`` only tries periods 3, 4 and 5.
"""

import os
import sys

from .common import class_of, data_files, file_for, parse_simple, read_lines, write_lines
from .digits import parser

PMAX = 2000      # primes tried
LMAX = 2520      # largest period tried


def _primes(n):
    s = bytearray([1]) * n
    s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(range(i * i, n, i)))
    return [i for i in range(n) if s[i]]


_PRIMES = _primes(PMAX)


def _cycle(q, b, x0, y):
    """Preperiod and period of x_{n+1} = x_n*b + y (mod q), from x_0 = x0."""
    seen = {}
    x, n = x0 % q, 0
    while x not in seen:
        seen[x] = n
        x = (x * b + y) % q
        n += 1
    return seen[x], n - seen[x]


def find_covering(base, start, middle, end, cls=None):
    """Certificate (L, {n mod L: divisor or 'class'}) for x y* z, or None.

    cls is (a, m) for a residue class, or None for all primes.
    """
    val = parser(base)
    x0 = val(start) if start else 0
    y = val(middle)
    zlen = len(end)
    z = val(end) if end else 0
    bz = base ** zlen

    def member_mod(q, n_max):
        """s(n) mod q for n = 0..n_max."""
        out, x = [], x0 % q
        for _ in range(n_max + 1):
            out.append((x * bz + z) % q)
            x = (x * base + y) % q
        return out

    mods = {}
    for p in _PRIMES:
        mu, pi = _cycle(p, base, x0, y)
        mods[p] = (mu, pi)
    cmu = cpi = None
    if cls is not None:
        cmu, cpi = _cycle(cls[1], base, x0, y)

    # Members small enough to equal one of the primes are checked directly.
    small_exact = {}
    for n in range(0, 12):
        v = val(start + middle * n + end) if (start + middle * n + end) else 0
        if v >= PMAX:
            break
        small_exact[n] = v

    # Residues are computed once, far enough for every period tried.
    useful = [p for p in _PRIMES if mods[p][1] <= LMAX]
    top_all = max([mods[p][0] for p in useful] + ([cmu] if cmu is not None else []) + [0]) + LMAX
    zero = {p: [r == 0 for r in member_mod(p, top_all)] for p in useful}
    cres_all = member_mod(cls[1], top_all) if cls is not None else None

    for L in range(1, LMAX + 1):
        if cpi is not None and L % cpi:
            continue
        use = [p for p in useful if L % mods[p][1] == 0]
        if not use and cls is None:
            continue
        top = max([mods[p][0] for p in use] + ([cmu] if cmu is not None else []) + [0]) + L
        residues = {p: zero[p] for p in use}
        cres = cres_all
        cert = {}
        ok = True
        for n in range(top):
            why = None
            if cres is not None and cres[n] != cls[0]:
                why = "class"
            else:
                for p in use:
                    if residues[p][n] and small_exact.get(n) != p:
                        why = p
                        break
            if why is None:
                ok = False
                break
            if n >= top - L:
                cert[n % L] = why
        if ok:
            return L, cert
    return None


def describe(L, cert):
    parts = []
    for r in range(L):
        parts.append("%d:%s" % (r, cert[r]))
    return "period %d; n mod %d -> %s" % (L, L, " ".join(parts))


def run_covering(datadir="data", out=sys.stdout):
    removed = 0
    for path, base, tag in data_files("unsolved", datadir):
        cls = class_of(tag)
        keep, covered = [], []
        for line in read_lines(path):
            if "*" not in line or "{" in line:
                keep.append(line)
                continue
            start, middle, end = parse_simple(line)
            found = find_covering(base, start, middle, end, cls)
            if found is None:
                keep.append(line)
            else:
                text = "%s  %s" % (line, describe(*found))
                covered.append(text)
                print("base %d%s: %s has no member in the target set (%s)"
                      % (base, tag, line, describe(*found)), file=out, flush=True)
        if covered:
            write_lines(path, keep)
            cov = file_for("covered", base, tag, datadir)
            write_lines(cov, read_lines(cov) + covered)
            removed += len(covered)
    print("covering: %d famil%s removed" % (removed, "y" if removed == 1 else "ies"), file=out)
    return 0


def main(argv=None):
    return run_covering()


if __name__ == "__main__":
    sys.exit(main())
