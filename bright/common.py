"""Shared helpers for the follow-up programs (simple, organize, sieving, search).

Files live in ``data/`` exactly as in Curtis Bright's mepn:

* ``data/minimal.<b>.txt``   minimal primes found so far in base b
* ``data/unsolved.<b>.txt``  unsolved simple families, one per line, e.g. ``60*49``
* ``data/sieve.<b>.txt``     sieve file (srsieve format) used by search

Runs made with ``--class a m`` use a tag in the file name, e.g.
``data/unsolved.10.1mod4.txt``. The tag is carried through every program, so
a filtered run only ever adds primes from its own class.
"""

import os
import re
import tempfile
from math import gcd

from .primality import is_probable_prime

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

_NAME = re.compile(r"^(minimal|unsolved|sieve)\.(\d+)((?:\.\d+mod\d+)?)\.txt$")
_TAG = re.compile(r"^\.(\d+)mod(\d+)$")


def data_files(kind, datadir="data"):
    """[(path, base, tag)] for data/<kind>.<b>[tag].txt, sorted by base then tag.

    (The C programs used directory order; sorting makes runs reproducible.)
    """
    out = []
    if not os.path.isdir(datadir):
        return out
    for name in os.listdir(datadir):
        m = _NAME.match(name)
        if m and m.group(1) == kind:
            out.append((os.path.join(datadir, name), int(m.group(2)), m.group(3)))
    out.sort(key=lambda t: (t[1], t[2]))
    return out


def file_for(kind, base, tag, datadir="data"):
    return os.path.join(datadir, "%s.%d%s.txt" % (kind, base, tag))


def class_of(tag):
    """'.1mod4' -> (1, 4); '' -> None."""
    m = _TAG.match(tag)
    return (int(m.group(1)), int(m.group(2))) if m else None


def in_target_set(n, tag):
    """Prime, and in the residue class given by the tag (if any)."""
    cls = class_of(tag)
    if cls is not None and n % cls[1] != cls[0]:
        return False
    return is_probable_prime(n)


def read_lines(path):
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return [line.rstrip("\r\n") for line in fh if line.rstrip("\r\n")]


def write_lines(path, lines):
    """Write atomically: a crash never leaves a half-written data file."""
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp-")
    with os.fdopen(fd, "w", newline="\n") as fh:
        for line in lines:
            fh.write(line + "\n")
    os.replace(tmp, path)


def append_line(path, line):
    with open(path, "a", newline="\n") as fh:
        fh.write(line + "\n")


def parse_simple(line):
    """'60*49' -> ('6', '0', '49'): start, repeated digit, end."""
    l = line.index("*")
    return line[: l - 1], line[l - 1], line[l + 1 :]


def subword(prime, start, middle, end):
    """Port of mepn's subword(): is ``prime`` a subsequence of
    start + middle^k + end, and with how many middle digits k?

    Returns (found, k). Matching is greedy, exactly as in the C code.
    """
    i = j = l = k = 0
    lp, ls, le = len(prime), len(start), len(end)
    while True:
        if j != ls:
            if prime[i] == start[j]:
                i += 1
            j += 1
        elif l == 0 and prime[i] == middle:
            k += 1
            i += 1
        else:
            if l < le and prime[i] == end[l]:
                i += 1
            l += 1
        if i == lp:
            return True, k
        if l == le + 1:
            return False, k


def has_kernel_subword(kernel, start, middle, end, num):
    """The first kernel prime contained in start + middle^num + end, or None."""
    for p in kernel:
        found, k = subword(p, start, middle, end)
        if found and k <= num:
            return p
    return None


def family_sequence(base, start, middle, end):
    """Write the family start middle^n end as (K * base^n + C) / Q.

    Returns (K, C, Q, A, zlen) where A = K / base^zlen, as computed in
    sieving.start.c and search.c.
    """
    zlen = len(end)
    x = int(start, base) if start else 0
    y = int(middle, base)
    z = int(end, base) if end else 0
    g = gcd(y, base - 1)
    q = (base - 1) // g
    K = (y // g + x * q) * base ** zlen
    C = -((y // g) * base ** zlen - z * q)
    return K, C, q, K // base ** zlen, zlen
