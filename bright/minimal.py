"""The Bright Algorithm: minimal primes in base b.

A Python translation of ``minimal.c`` from Curtis Bright's mepn
(https://github.com/curtisbright/mepn), described in C. Bright, R. Devillers
and J. Shallit, "Minimal elements for the prime numbers", Experimental
Mathematics 25(3), 2016.

It computes the minimal primes in each base from l to h. Where it cannot
settle everything, it also reports the unsolved "simple" families, which are
searched afterwards by ``simple``/``search``.

Usage (same as the C program; run from the directory where ``data/`` and
``iter/`` should be written)::

    python -m bright.minimal l h
    python -m bright.minimal b
    python -m bright.minimal resume b i     # resume base b from iteration i

Data model
----------
A *family* is a list of nodes ``[digit, repeats]``. It stands for the language
``d0 R0* d1 R1* ...``: each node is a fixed digit followed by any string over
its repeat digits. ``EMPTY`` (255 in the C code) marks a node with no fixed
digit. Printed form: ``1{0,3}*`` is written ``1{03}*``.

The *kernel* is the list of minimal primes found so far, as base-b strings.

Lists of unsolved families hold ``(family, split)`` pairs, where ``split``
mirrors the C ``split`` flag: 2 = freshly split, 1 = may still split,
0 = no further splitting this iteration.

This is a faithful translation: the order of operations, iteration counters
and output files match the C program, so results can be compared line for
line. One deliberate difference: string building uses the intended "append"
semantics. The C code's ``sprintf(str, "%s%c", str, ...)`` idiom gives wrong
results on glibc 2.37 and later.
"""

import os
import re
import sys
from math import gcd, isqrt

from .digits import DIGITS, MAX_BASE, check_base, parser, to_str
from .primality import is_probable_prime

EMPTY = 255


# ---------------------------------------------------------------------------
# Family helpers (pure functions on the family data structure)
# ---------------------------------------------------------------------------

_DIGCH = [DIGITS[d] if d < len(DIGITS) else "" for d in range(256)]


def digitchar(d):
    return "" if d == EMPTY else DIGITS[d]


def invdigitchar(c):
    return DIGITS.index(c)


def copyfamily(f):
    return [[d, list(r)] for d, r in f]


def issimple(f):
    """Exactly one node has repeats, and it has exactly one repeat digit."""
    hasrepeat = False
    for _, r in f:
        if len(r) > 1:
            return False
        if len(r) == 1:
            if hasrepeat:
                return False
            hasrepeat = True
    return hasrepeat


def familystring(f):
    out = []
    for d, r in f:
        out.append(digitchar(d))
        if r:
            out.append("{" + "".join(digitchar(x) for x in r) + "}*")
    return "".join(out)


def simplefamilystring(f):
    """Compact form for a simple family, e.g. ``60*49``."""
    repeateddigit = repeatedpos = None
    for i, (_, r) in enumerate(f):
        if len(r) == 1:
            repeateddigit, repeatedpos = r[0], i
            break
    j = -1
    for i in range(repeatedpos, -1, -1):
        if f[i][0] != repeateddigit and f[i][0] != EMPTY:
            j = i
            break
    k = len(f)
    for i in range(repeatedpos + 1, len(f)):
        if f[i][0] != repeateddigit and f[i][0] != EMPTY:
            k = i
            break
    return ("".join(digitchar(f[i][0]) for i in range(j + 1))
            + digitchar(repeateddigit) + "*"
            + "".join(digitchar(f[i][0]) for i in range(k, len(f))))


def instancestring(f, picks=()):
    """The family's fixed digits, with chosen repeat digits inserted.

    ``picks`` is a sequence of ``(node, index)`` pairs. After node ``x``'s
    fixed digit, ``f[x][1][y]`` is inserted for every pick ``(x, y)``, in the
    order given. This one function covers the C functions
    empty/instance/double/triple/quad/quintinstancestring.
    """
    parts = [_DIGCH[d] for d, _ in f]
    for x, y in picks:
        parts[x] += DIGITS[f[x][1][y]]
    return "".join(parts)


def startinstancestring(f, length):
    return "".join(digitchar(f[i][0]) for i in range(length + 1))


def endinstancestring(f, start):
    return "".join(digitchar(f[i][0]) for i in range(start + 1, len(f)))


def without(reps, idx):
    return [x for k, x in enumerate(reps) if k != idx]


def is_subsequence(q, p):
    """True if q can be obtained from p by deleting characters."""
    if len(q) > len(p):
        return False
    it = iter(p)
    return all(c in it for c in q)


def _exact_root(n, k):
    """(root, exact) for the integer k-th root of n, like ``mpz_root``."""
    if n < 0:
        r, exact = _exact_root(-n, k)
        return -r, exact
    r = isqrt(n) if k == 2 else _iroot(n, k)
    return r, r ** k == n


def _iroot(n, k):
    lo, hi = 0, 1 << (n.bit_length() // k + 1)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if mid ** k <= n:
            lo = mid
        else:
            hi = mid - 1
    return lo


# ---------------------------------------------------------------------------
# The algorithm
# ---------------------------------------------------------------------------

class BrightMinimal:
    """State for one base: the kernel K and the iteration counter.

    ``base``, ``iter`` and ``K`` were globals in the C program.
    """

    def __init__(self, base, log=None, residue=None, modulus=None):
        check_base(base)
        if (residue is None) != (modulus is None):
            raise ValueError("give both residue and modulus, or neither")
        if modulus is not None:
            if modulus < 1:
                raise ValueError("modulus must be at least 1")
            residue %= modulus
        self.base = base
        self._parse = parser(base)
        self.iter = 0
        self.K = []
        self.log = log
        self.residue = residue
        self.modulus = modulus

    @property
    def tag(self):
        """Suffix for output file names: '' or e.g. '.1mod4'."""
        return "" if self.modulus is None else ".%dmod%d" % (self.residue, self.modulus)

    # -- numbers ----------------------------------------------------------
    def val(self, s):
        """``mpz_set_str(.., s, base)``; an empty string leaves the value 0."""
        return self._parse(s) if s else 0

    def isprime(self, s):
        """Membership in the target set: prime and, if a filter is set,
        congruent to residue mod modulus."""
        n = self.val(s)
        if self.modulus is not None and n % self.modulus != self.residue:
            return False
        return is_probable_prime(n)

    def misses_class(self, p):
        """True if no member of family p can be a prime in the class.

        The residues reachable by members of the family are computed exactly
        modulo L = lcm(m, 30), in the same way as the mod-30 test in
        hasdivisor. A member can be a prime in the class only if its residue r
        satisfies r = a (mod m) and gcd(r, 30) = 1, or is one of the primes 2, 3
        and 5; those have at most three digits in any base, so they are
        already in the kernel or not minimal, and discarding the family loses
        nothing. Testing both conditions on the same
        residues catches families where every member is either outside the
        class or divisible by 2, 3 or 5, such as 11 0* 4* 1 in base 5 with the
        class 3 mod 8 (odd number of 4s: divisible by 3; even: 7 mod 8),
        which neither condition rules out on its own.
        """
        if self.modulus is None:
            return False
        m, B = self.modulus, self.base
        m = m * 30 // gcd(m, 30)
        reach = {0}
        for d, r in p:
            if d != EMPTY:
                reach = {(x * B + d) % m for x in reach}
            frontier = list(reach)
            while frontier:
                x = frontier.pop()
                for rep in r:
                    y = (x * B + rep) % m
                    if y not in reach:
                        reach.add(y)
                        frontier.append(y)
        a, mod = self.residue, self.modulus
        return not any(x % mod == a and gcd(x, 30) == 1 for x in reach)

    # -- subword index -----------------------------------------------------
    # A kernel prime q of length >= 2 can only be a subsequence of p if p has
    # q[0] somewhere before an occurrence of q[-1].  Kernel primes are grouped
    # by that (first, last) pair, and each group is one compiled regex.  For a
    # string p only the groups whose pair occurs in p are tried, which is a
    # small fraction of the kernel once it holds thousands of primes.
    # Single-digit kernel primes are kept in a set.

    @staticmethod
    def _compile(primes):
        alts = ["".join("[^%s]*%s" % (re.escape(c), re.escape(c)) for c in q) for q in primes]
        return re.compile("(?:" + "|".join(alts) + ")").match

    def _sync_index(self):
        K = self.K
        if getattr(self, "_indexed_list", None) is not K:
            self._indexed_list = K
            self._indexed_len = 0
            self._singles = set()
            self._groups = {}      # (first, last) -> list of primes
            self._matchers = {}    # (first, last) -> compiled match, or None if stale
            self._seen = {}        # p -> -1 (has a kernel subword) or kernel length checked
        n = len(K)
        if n == self._indexed_len:
            return
        groups, matchers = self._groups, self._matchers
        for q in K[self._indexed_len:n]:
            if len(q) == 1:
                self._singles.add(q)
            else:
                key = (q[0], q[-1])
                groups.setdefault(key, []).append(q)
                matchers[key] = None
        self._indexed_len = n

    # Strings repeat a lot (about two calls in three), and the kernel only
    # grows, so results are cached: a string with a kernel subword keeps one,
    # and a string without one only needs the primes added since.  The cache
    # is cleared when it reaches _SEEN_MAX entries, to bound memory.
    _SEEN_MAX = 2_000_000

    def nosubword(self, p):
        """True if no kernel prime is a subsequence of p."""
        self._sync_index()
        n = self._indexed_len
        seen = self._seen
        c = seen.get(p)
        if c is not None:
            if c < 0:
                return False
            if c == n:
                return True
            if n - c <= 32:
                for q in self.K[c:n]:
                    if is_subsequence(q, p):
                        seen[p] = -1
                        return False
                seen[p] = n
                return True
        ok = self._nosubword_index(p)
        if len(seen) >= self._SEEN_MAX:
            seen.clear()
        seen[p] = n if ok else -1
        return ok

    def _nosubword_index(self, p):
        first = {}
        last = {}
        for i, c in enumerate(p):
            if c not in first:
                first[c] = i
            last[c] = i
        singles = self._singles
        if singles and not singles.isdisjoint(first):
            return False
        groups, matchers = self._groups, self._matchers
        for a, i in first.items():
            for b, j in last.items():
                if i < j:
                    key = (a, b)
                    if key in groups:
                        m = matchers[key]
                        if m is None:
                            m = matchers[key] = self._compile(groups[key])
                        if m(p):
                            return False
        return True

    def nosubwordskip(self, p, skip):
        for i, q in enumerate(self.K):
            if i != skip and is_subsequence(q, p):
                return False
        return True

    def newminimal(self, p):
        return self.nosubword(p) and self.isprime(p)

    # -- divisibility tests ------------------------------------------------
    def hasdivisor(self, p):
        """True if every number in family p is provably composite."""
        B = self.base
        val = self.val
        L = len(p)
        nr = [len(r) for _, r in p]

        nodes = [_DIGCH[d] for d, _ in p]
        reps = [[DIGITS[x] for x in r] for _, r in p]
        join = "".join
        parse = self._parse

        def inst(*picks):
            # Same string as instancestring(p, picks), built more cheaply.
            parts = nodes[:]
            for x, y in picks:
                parts[x] += reps[x][y]
            s = join(parts)
            return parse(s) if s else 0

        def gcd_all(g, values):
            # gcd over values, stopping once it is 1: every test below only
            # asks whether a gcd is > 1 (and < empty), and a gcd of 1 stays 1,
            # so the decisions are exactly those of the full loops in the C
            # code, which this replaces.
            for v in values:
                g = gcd(g, v)
                if g == 1:
                    return 1
            return g

        empty = inst()
        rep_nodes = [i for i in range(L) if nr[i] > 0]
        numrepeats = len(rep_nodes)
        if numrepeats == 0:
            return False

        # One divisor for the whole family.
        g = gcd_all(empty, (inst((i, j)) for i in range(L) for j in range(nr[i])))
        if g > 1 and empty > g:
            return True

        # Two divisors: split by whether the repeats at node m are used an
        # even or odd number of times.
        for m in rep_nodes:
            gcd1 = gcd_all(empty, (inst((i, j)) for i in range(L) if i != m
                                   for j in range(nr[i])))
            gcd1 = gcd_all(gcd1, (inst((m, i), (m, j))
                                  for i in range(nr[m]) for j in range(nr[m])))
            if not (gcd1 > 1 and empty > gcd1):
                continue
            gcd2 = 0
            for n in range(nr[m]):
                gcd2 = gcd_all(gcd2, [inst((m, n))])
                gcd2 = gcd_all(gcd2, (inst((i, j), (m, n)) for i in range(L) if i != m
                                      for j in range(nr[i])))
                gcd2 = gcd_all(gcd2, (inst((m, i), (m, j), (m, k)) for i in range(nr[m])
                                      for j in range(nr[m]) for k in range(nr[m])))
                if gcd2 == 1:
                    break
            if gcd2 > 1 and empty > gcd2:
                return True

        # gcd2: odd-count divisor at the first repeating node.
        firstrepeat = rep_nodes[0]
        fr = firstrepeat
        gcd2 = 0
        for j in range(nr[fr]):
            gcd2 = gcd_all(gcd2, [inst((fr, j))])
            gcd2 = gcd_all(gcd2, (inst((fr, j), (k, l), (k, n)) for k in range(L)
                                  for l in range(nr[k]) for n in range(nr[k])))
            if gcd2 == 1:
                break

        if numrepeats == 2:
            sr = rep_nodes[1]
            gcd1 = gcd_all(empty, (inst((i, j), (i, l)) for i in range(L)
                                   for j in range(nr[i]) for l in range(nr[i])))
            ok = gcd1 > 1 and empty > gcd1 and gcd2 > 1 and empty > gcd2
            if ok:
                temp2 = 0
                for j in range(nr[sr]):
                    temp2 = gcd_all(temp2, [inst((sr, j))])
                    temp2 = gcd_all(temp2, (inst((sr, j), (k, l), (k, n)) for k in range(L)
                                            for l in range(nr[k]) for n in range(nr[k])))
                    if temp2 == 1:
                        break
                ok = temp2 > 1 and empty > temp2
            if ok:
                temp3 = gcd_all(0, (inst((fr, j), (sr, l))
                                    for j in range(nr[fr]) for l in range(nr[sr])))
                temp3 = gcd_all(temp3, (inst((fr, a), (fr, b), (fr, c), (sr, d))
                                        for a in range(nr[fr]) for b in range(nr[fr])
                                        for c in range(nr[fr]) for d in range(nr[sr])))
                temp3 = gcd_all(temp3, (inst((fr, a), (sr, b), (sr, c), (sr, d))
                                        for a in range(nr[fr]) for b in range(nr[sr])
                                        for c in range(nr[sr]) for d in range(nr[sr])))
                if temp3 > 1 and empty > temp3:
                    return True

        if numrepeats == 1:
            for i in range(L):
                if nr[i] != 1:
                    continue
                end = endinstancestring(p, i)
                zlen = len(end)
                z = val(end)
                y = p[i][1][0]
                start = startinstancestring(p, i)
                x = val(start)
                middle = digitchar(y)

                def s(n):
                    return val(start + middle * n + end)

                # Periodic divisors with period 3, 4 and 5.
                for period in (3, 4, 5):
                    gs = [gcd(s(r), s(r + period)) for r in range(period)]
                    if all(t > 1 and empty > t for t in gs):
                        return True

                # Algebraic factorisations:
                # s(n) * (B-1)/g = A * B^n - C, with A = (y/g + x(B-1)/g) B^zlen
                # and C = (y/g) B^zlen - z (B-1)/g.
                g = gcd(y, B - 1)
                q = (B - 1) // g
                A = (y // g + x * q) * B ** zlen
                C = (y // g) * B ** zlen - z * q

                rA, exactA = _exact_root(A, 2)
                if exactA and C >= 0:
                    rC, exactC = _exact_root(C, 2)
                    if exactC:
                        diff = rA - rC
                        _, base_square = _exact_root(B, 2)
                        if diff > q and base_square:
                            return True  # difference of squares
                        elif diff > q and gcd2 > 1 and empty > gcd2:
                            return True  # squares for even n, gcd2 for odd n

                rA, exactA = _exact_root(A, 3)
                if exactA:
                    rC, exactC = _exact_root(C, 3)
                    if exactC:
                        diff = rA - rC
                        if diff > q and _exact_root(B, 3)[1]:
                            return True  # difference of cubes

        # Every member divisible by 2, 3 or 5: track residues mod 30.
        residues = [False] * 30
        residues[0] = True
        for d, r in p:
            if d != EMPTY:
                newres = [False] * 30
                for j in range(30):
                    if residues[j]:
                        newres[(j * B + d) % 30] = True
                residues = newres
            changed = True
            while changed:
                changed = False
                for rep in r:
                    for l in range(30):
                        if residues[l] and not residues[(l * B + rep) % 30]:
                            residues[(l * B + rep) % 30] = True
                            changed = True
        if not any(residues[i] and gcd(i, 30) == 1 for i in range(30)):
            return True

        # Filter: no member of the family lies in the residue class.
        if self.misses_class(p):
            return True

        return False

    # -- examine -----------------------------------------------------------
    def examine(self, f):
        """Simplify family f in place. Return True if it stays unsolved."""
        s = instancestring(f)
        if not self.nosubword(s):
            return False
        if self.isprime(s):
            self.K.append(s)
            return False

        trivial = True
        for i in range(len(f)):
            f[i][1] = [rep for j, rep in enumerate(f[i][1])
                       if self.nosubword(instancestring(f, ((i, j),)))]
            if f[i][1]:
                trivial = False

        # Simplify y*y^n y* patterns.
        lastdigit = 0
        dosimplify = False
        for i in range(len(f)):
            d = f[i][0]
            if (dosimplify and len(f[i][1]) == 1 and f[i][1][0] == lastdigit
                    and (lastdigit == d or d == EMPTY)):
                f[i][1] = []
            if d != EMPTY:
                if d != lastdigit:
                    dosimplify = False
                lastdigit = d
            if len(f[i][1]) == 1:
                dosimplify = True
                lastdigit = f[i][1][0]
            elif len(f[i][1]) > 1:
                dosimplify = False

        if trivial:
            return False
        if self.hasdivisor(f):
            return False
        return True

    # -- splitting ---------------------------------------------------------
    @staticmethod
    def _with_copies(f, i, digit, reps, copies):
        """Copy f with ``copies`` nodes (digit, reps) inserted after node i."""
        newf = copyfamily(f[: i + 1])
        newf += [[digit, list(reps)] for _ in range(copies)]
        newf += copyfamily(f[i + 1 :])
        return newf

    def split(self, f, unsolved, insplit):
        if insplit == 0:
            unsolved.append((f, 0))
            return 0
        for i in range(len(f)):
            for j in range(len(f[i][1])):
                removed = f[i][1][j]
                rest = without(f[i][1], j)
                copyf = copyfamily(f)
                copyf[i][1] = list(rest)

                # If removed^n is a kernel subword (n = 2, 3, 4, 10), then
                # removed appears at most n-1 times.
                for n in (2, 3, 4, 10):
                    if not self.nosubword(instancestring(f, ((i, j),) * n)):
                        unsolved.append((copyf, 2))
                        for c in range(1, n):
                            unsolved.append((self._with_copies(copyf, i, removed, rest, c), 2))
                        return 1

                if self.iter > 5:
                    empty = self.val(instancestring(f))
                    g = empty
                    for ii in range(len(f)):
                        for jj in range(len(f[ii][1])):
                            if i != ii or j != jj:
                                g = gcd(g, self.val(instancestring(f, ((ii, jj),))))
                    if g > 1 and empty > g:
                        unsolved.append((self._with_copies(f, i, removed, f[i][1], 1), 2))
                        return 1
        unsolved.append((f, 1))
        return 0

    def split2(self, f, unsolved, insplit):
        if insplit == 0:
            unsolved.append((f, 0))
            return 0
        sub = lambda *picks: not self.nosubword(instancestring(f, picks))
        for i in range(len(f)):
            for j in range(len(f[i][1])):
                for m in range(i, len(f)):
                    for k in range(len(f[m][1])):
                        if m == i and j <= k:
                            continue
                        if m == i:
                            # a = digit j, b = digit k at the same node i.
                            ab, ba = sub((i, j), (i, k)), sub((i, k), (i, j))
                            if ab and ba:
                                # a and b cannot both appear.
                                for drop in (j, k):
                                    c = copyfamily(f)
                                    c[i][1] = without(f[i][1], drop)
                                    unsolved.append((c, 1))
                                return 1
                            if self.iter > 5:
                                patterns = (
                                    (lambda: ab, (j, k)),
                                    (lambda: ba, (k, j)),
                                    (lambda: sub((i, j), (i, k), (i, j)), (j, k, j)),
                                    (lambda: sub((i, k), (i, j), (i, k)), (k, j, k)),
                                    (lambda: sub((i, j), (i, k), (i, j), (i, k)), (j, k, j, k)),
                                    (lambda: sub((i, k), (i, j), (i, k), (i, j)), (k, j, k, j)),
                                )
                                for test, drops in patterns:
                                    if test():
                                        # Forbidden pattern: rewrite R* as
                                        # {R-x1}* {R-x2}* ... .
                                        newf = copyfamily(f[:i])
                                        newf.append([f[i][0], without(f[i][1], drops[0])])
                                        for dr in drops[1:]:
                                            newf.append([EMPTY, without(f[i][1], dr)])
                                        newf += copyfamily(f[i + 1 :])
                                        unsolved.append((newf, 1))
                                        return 1
                        elif sub((i, j), (m, k)):
                            # Digit j at node i and digit k at node m cannot
                            # both appear.
                            c = copyfamily(f)
                            c[i][1] = without(f[i][1], j)
                            unsolved.append((c, 1))
                            c = copyfamily(f)
                            c[m][1] = without(f[m][1], k)
                            unsolved.append((c, 1))
                            return 1
        unsolved.append((f, insplit - 1))
        return 0

    # -- exploring ---------------------------------------------------------
    def explore(self, f, side, pos, unsolved):
        """Expand one repeating node: its first (side 1) or last (side 0)
        digit is each repeat digit in turn, or the node repeats nothing."""
        repeating = [i for i, (_, r) in enumerate(f) if r]
        i = repeating[pos % len(repeating)]
        d, reps = f[i]
        for rep in reps:
            if side == 1:
                inserted = [[d, []], [rep, list(reps)]]
            else:
                inserted = [[d, list(reps)], [rep, []]]
            newf = copyfamily(f[:i]) + inserted + copyfamily(f[i + 1 :])
            if self.examine(newf):
                unsolved.append((newf, 1))
        copyf = copyfamily(f)
        copyf[i][1] = []
        if self.examine(copyf):
            unsolved.append((copyf, 1))

    # -- bookkeeping -------------------------------------------------------
    @staticmethod
    def removedupes(unsolved):
        """Drop duplicate families, keeping the first. For a duplicated simple
        family, keep whichever spelling has the shorter family string."""
        seen = {}
        out = []
        for f, sp in unsolved:
            simple = issimple(f)
            key = simplefamilystring(f) if simple else familystring(f)
            idx = seen.get(key)
            if idx is None:
                seen[key] = len(out)
                out.append((f, sp))
            elif simple and len(familystring(f)) < len(familystring(out[idx][0])):
                out[idx] = (f, out[idx][1])
        return out

    @staticmethod
    def onlysimple(unsolved):
        return all(issimple(f) for f, _ in unsolved)

    def _say(self, msg):
        if self.log is not None:
            print(msg, file=self.log)

    # -- driver --------------------------------------------------------------
    def initial(self):
        """Kernel of 1-3 digit primes, then explore families x{R}*y."""
        B = self.base
        unsolved = []
        self.iter = 0
        if self.modulus is not None and gcd(self.residue, self.modulus) > 1:
            # Every member of the class is divisible by g = gcd(a, m) > 1, so
            # the only possible prime is g itself; as g <= a < m (or g = m
            # when a = 0), that prime is a (or m when a = 0).
            p = self.residue if self.residue else self.modulus
            self.K = [to_str(p, B)] if is_probable_prime(p) else []
            return unsolved
        for i in range(B):
            for j in range(B):
                for k in range(B):
                    if i == 0 and j == 0:
                        s = digitchar(k)
                    elif i == 0:
                        s = digitchar(j) + digitchar(k)
                    else:
                        s = digitchar(i) + digitchar(j) + digitchar(k)
                    if self.newminimal(s):
                        self.K.append(s)
        for i in range(1, B):
            for j in range(B):
                middles = [k for k in range(B)
                           if self.nosubword(digitchar(i) + digitchar(k) + digitchar(j))]
                if middles:
                    f = [[i, middles], [j, []]]
                    if not self.hasdivisor(f):
                        self.explore(f, 1, 0, unsolved)
        self.iter = 0
        return unsolved

    def run(self, unsolved, write_iter=True, iterdir="iter"):
        """Main loop. Returns the final list of unsolved families."""
        B = self.base
        while True:
            if self.onlysimple(unsolved):
                break
            didsplit = True
            splititer = 0
            while didsplit:
                didsplit = False
                for splitter in (self.split, self.split2):
                    old, unsolved = unsolved, []
                    for f, sp in old:
                        didsplit |= bool(splitter(f, unsolved, sp))
                    unsolved = self.removedupes(unsolved)
                    old, unsolved = unsolved, []
                    for f, sp in old:
                        if sp == 0 or self.examine(f):
                            unsolved.append((f, sp))
                    unsolved = self.removedupes(unsolved)
                splititer += 1
                self._say("base %-2d  iteration %-3d  split %-3d  size %-7d  remain %d"
                          % (B, self.iter, splititer, len(self.K), len(unsolved)))

            old, unsolved = unsolved, []
            for f, _ in old:
                self.explore(f, self.iter % 2, self.iter, unsolved)
            unsolved = self.removedupes(unsolved)

            if write_iter:
                os.makedirs(iterdir, exist_ok=True)
                with open(os.path.join(iterdir, "unsolved-base%d%s-iter%d.txt" % (B, self.tag, self.iter)), "w") as fh:
                    fh.writelines(familystring(f) + "\n" for f, _ in unsolved)
                with open(os.path.join(iterdir, "minimal-base%d%s-iter%d.txt" % (B, self.tag, self.iter)), "w") as fh:
                    fh.writelines(p + "\n" for p in self.K)

            if not unsolved:
                break
            self.iter += 1
        return unsolved

    def final_kernel(self):
        """Drop kernel elements that contain another element as a subword."""
        self.K = [p for i, p in enumerate(self.K) if self.nosubwordskip(p, i)]
        return self.K

    def resume(self, iteration, iterdir="iter"):
        """Reload kernel and unsolved families saved after ``iteration``."""
        B = self.base
        with open(os.path.join(iterdir, "minimal-base%d%s-iter%d.txt" % (B, self.tag, iteration))) as fh:
            self.K = [line.rstrip("\n") for line in fh if line.rstrip("\n")]
        unsolved = []
        with open(os.path.join(iterdir, "unsolved-base%d%s-iter%d.txt" % (B, self.tag, iteration))) as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line:
                    unsolved.append((parse_family(line), 2))
        self.iter = iteration + 1
        return unsolved


def parse_family(s):
    """Inverse of familystring: ``1{03}*{5}*2`` -> family."""
    f = []
    i = 0
    while i < len(s):
        if s[i] == "{":
            digit = EMPTY
        else:
            digit = invdigitchar(s[i])
            i += 1
        if i < len(s) and s[i] == "{":
            close = s.index("}", i)
            reps = [invdigitchar(c) for c in s[i + 1 : close]]
            i = close + 2  # skip "}*"
        else:
            reps = []
        f.append([digit, reps])
    return f


def compute_base(base, log=sys.stdout, write_files=True, datadir="data", iterdir="iter",
                 resume_iter=None, residue=None, modulus=None):
    """Run the Bright Algorithm for one base.

    With ``residue`` and ``modulus`` set, computes the minimal elements of
    the primes p with p = residue (mod modulus) instead of all primes.

    Returns (minimal primes, unsolved families).
    """
    bm = BrightMinimal(base, log=log, residue=residue, modulus=modulus)
    bm._say("base %d..." % base if bm.modulus is None
            else "base %d, primes = %d mod %d..." % (base, bm.residue, bm.modulus))
    if resume_iter is None:
        unsolved = bm.initial()
    else:
        unsolved = bm.resume(resume_iter, iterdir)
    unsolved = bm.run(unsolved, write_iter=write_files, iterdir=iterdir)
    kernel = bm.final_kernel()
    if write_files:
        os.makedirs(datadir, exist_ok=True)
        with open(os.path.join(datadir, "minimal.%d%s.txt" % (base, bm.tag)), "w") as fh:
            fh.writelines(p + "\n" for p in kernel)
        # A new unsolved list starts the length count for simple afresh.
        progress = os.path.join(datadir, "simple.%d%s.txt" % (base, bm.tag))
        if os.path.exists(progress):
            os.remove(progress)
        if unsolved:
            with open(os.path.join(datadir, "unsolved.%d%s.txt" % (base, bm.tag)), "w") as fh:
                for f, _ in unsolved:
                    fh.write((simplefamilystring(f) if issimple(f) else familystring(f)) + "\n")
    return kernel, [f for f, _ in unsolved]


USAGE = """\
Computes minimal primes for the given bases,
possibly along with a set of unsolved families
Usage: python -m bright minimal BASES [--class a m | --class m]
  BASES         l h                 bases l to h, e.g. 2 20
                list                e.g. 10   2-20   2-10,16,30-36
                list comprehension  e.g. "[b for b in range(2, 37) if not isprime(b)]"
  --class a m   only primes p with p = a (mod m), e.g. --class 1 4
  --class m     every class a mod m with gcd(a, m) = 1, one after another
To resume base b from iteration i: python -m bright minimal resume b i [--class a m]"""


def parse_bases(args):
    """Bases from the command line: 'l h', a list such as '2-10,16', or a
    Python expression giving a list of bases (a list comprehension).

    The expression is evaluated with only range, gcd and the like available;
    it runs on your own computer, as typed by you.
    """
    text = " ".join(args).strip()
    if not text:
        raise ValueError("no bases given")
    if len(args) == 2 and all(a.lstrip("-").isdigit() for a in args):
        lo, hi = int(args[0]), int(args[1])
        bases = list(range(lo, hi + 1))
    elif all(c in "0123456789,- " for c in text):
        bases = []
        for part in text.replace(" ", ",").split(","):
            if not part:
                continue
            if "-" in part[1:]:
                lo, hi = part.split("-", 1)
                bases.extend(range(int(lo), int(hi) + 1))
            else:
                bases.append(int(part))
    else:
        import math
        def isprime(n):
            return n >= 2 and all(n % d for d in range(2, math.isqrt(n) + 1))
        names = {"range": range, "gcd": math.gcd, "isqrt": math.isqrt, "isprime": isprime,
                 "list": list, "set": set, "sorted": sorted, "abs": abs,
                 "min": min, "max": max, "len": len, "all": all, "any": any}
        try:
            value = eval(text, {"__builtins__": {}}, names)
        except Exception as e:
            raise ValueError("could not read bases %r: %s" % (text, e))
        bases = [value] if isinstance(value, int) else list(value)
    out = []
    for b in bases:
        if not isinstance(b, int) or isinstance(b, bool):
            raise ValueError("base %r is not an integer" % (b,))
        if not 2 <= b <= 62:
            raise ValueError("base %d is outside 2..62" % b)
        if b not in out:
            out.append(b)
    return out


def coprime_residues(m):
    """Residues a in 1..m-1 with gcd(a, m) = 1 (for m = 1, just 0)."""
    from math import gcd
    return [a for a in range(m) if gcd(a, m) == 1] if m > 1 else [0]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    classes = [None]
    if "--class" in argv:
        k = argv.index("--class")
        nums = []
        for a in argv[k + 1:k + 3]:
            if a.lstrip("-").isdigit():
                nums.append(int(a))
            else:
                break
        if not nums:
            print("--class needs a m, or just m", file=sys.stderr)
            return 2
        if nums[-1] < 1:
            print("--class: the modulus must be at least 1", file=sys.stderr)
            return 2
        del argv[k:k + 1 + len(nums)]
        if len(nums) == 2:
            classes = [(nums[0] % nums[1], nums[1])]
        else:
            classes = [(a, nums[0]) for a in coprime_residues(nums[0])]
    if not argv:
        print(USAGE)
        return 0
    if argv[0] == "resume":
        if len(classes) > 1:
            print("resume needs a single class: --class a m", file=sys.stderr)
            return 2
        cls = classes[0] or (None, None)
        base, it = int(argv[1]), int(argv[2])
        compute_base(base, resume_iter=it, residue=cls[0], modulus=cls[1])
        return 0
    try:
        bases = parse_bases(argv)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    for base in bases:
        for cls in classes:
            residue, modulus = cls if cls else (None, None)
            compute_base(base, residue=residue, modulus=modulus)
    return 0


if __name__ == "__main__":
    sys.exit(main())
