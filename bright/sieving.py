"""Sieving for the long searches (ports of sieving.start.c, sieving.c, merge.c).

A simple family ``x y* z`` has members (K * b^n + C) / Q. srsieve removes
exponents n for which K * b^n + C has a prime factor p >= pmin. Primes that
divide Q, and all primes below pmin, are handled here instead, so srsieve
never removes a member because of a factor of Q.

Commands::

    python -m bright sieve-start N M   # sieve files for every unsolved family, n in [N, M]
    python -m bright sieve B [--pmax P] [--srsieve PATH]
    python -m bright merge

Files: ``data/sieve.<b>.txt`` is the copy that ``search`` updates;
``sieve/sieve.<b>.txt`` is srsieve's working copy. ``merge`` keeps only the
exponents present in both, so neither program repeats the other's work.
(The C version kept the working copy in ``srsieve/``; here that folder holds
the srsieve source.)
"""

import os
import platform
import shutil
import subprocess
import sys

from .common import (class_of, data_files, family_sequence, file_for, parse_simple, read_lines,
                     write_lines)

SIEVE_DIR = "sieve"
_SMALL_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]


def _primes_below(n):
    return [p for p in range(2, n) if all(p % d for d in range(2, int(p ** 0.5) + 1))]


def _largest_prime_factor(n):
    best, d = 1, 2
    while d * d <= n:
        while n % d == 0:
            best, n = d, n // d
        d += 1
    return max(best, n) if n > 1 else best


def pmin_for(base):
    """31 as in the C code; higher if b-1 has a prime factor >= 31 (bases > 31)."""
    return max(31, _largest_prime_factor(base - 1) + 1)


def family_line(base, start, middle, end):
    K, C, _, _, _ = family_sequence(base, start, middle, end)
    return "%d*%d^n%+d" % (K, base, C)


def surviving_exponents(base, start, middle, end, n, m, tag=""):
    """Exponents in [n, m] that pass the small-prime presieve (and the class)."""
    K, C, q, _, _ = family_sequence(base, start, middle, end)
    primes = _SMALL_PRIMES if base <= 31 else _primes_below(pmin_for(base))
    divis = bytearray(m + 1)
    for k in primes:
        # Members divisible by k occur at an arithmetic progression of n;
        # find two consecutive ones, as sieving.start.c does.
        first = diff = 0
        for num in range(n, n + 2 * k + 1):
            if (K * pow(base, num, k * q) + C) % (k * q) // q % k == 0:
                if first == 0:
                    first = num
                else:
                    diff = num - first
                    break
        if diff > 0:
            for num in range(first, m + 1, diff):
                divis[num] = 1
    cls = class_of(tag)
    if cls is not None:
        a, mod = cls
        mq = mod * q
        for num in range(n, m + 1):
            if not divis[num] and (K * pow(base, num, mq) + C) % mq // q % mod != a:
                divis[num] = 1
    return [num for num in range(n, m + 1) if not divis[num]]


def start_sieve(n, m, datadir="data", sievedir=SIEVE_DIR):
    for path, base, tag in data_files("unsolved", datadir):
        families = [l for l in read_lines(path) if "*" in l and "{" not in l]
        if not families:
            continue
        lines = ["pmin=%d" % pmin_for(base)]
        for fam in families:
            start, middle, end = parse_simple(fam)
            lines.append(family_line(base, start, middle, end))
            lines.extend(str(e) for e in surviving_exponents(base, start, middle, end, n, m, tag))
        write_lines(file_for("sieve", base, tag, sievedir), lines)
        write_lines(file_for("sieve", base, tag, datadir), lines)


def parse_sieve(lines):
    """Sieve file lines -> (header, [(family, [exponents])])."""
    header, blocks = (lines[0] if lines else "pmin=31"), []
    for line in lines[1:]:
        if "*" in line:
            blocks.append((line, []))
        elif blocks:
            blocks[-1][1].append(int(line))
    return header, blocks


def format_sieve(header, blocks):
    out = [header]
    for fam, exps in blocks:
        out.append(fam)
        out.extend(str(e) for e in exps)
    return out


def merge(datadir="data", sievedir=SIEVE_DIR):
    """Keep families and exponents present in both copies (port of merge.c)."""
    for path, base, tag in data_files("sieve", datadir):
        work = file_for("sieve", base, tag, sievedir)
        if not os.path.exists(work):
            continue
        _, data_blocks = parse_sieve(read_lines(path))
        header, work_blocks = parse_sieve(read_lines(work))
        searched = {}
        for fam, exps in data_blocks:
            searched.setdefault(fam, set(exps))
        merged = [(fam, [e for e in exps if e in searched[fam]])
                  for fam, exps in work_blocks if fam in searched]
        lines = format_sieve(header, merged)
        write_lines(path, lines)
        write_lines(work, lines)


def platform_dir():
    """bin/<system>-<arch> folder for this computer, e.g. bin/windows-x64."""
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    machine = platform.machine().lower()
    arch = "x64" if machine in ("x86_64", "amd64") else machine
    system = {"win32": "windows", "darwin": "macos"}.get(sys.platform, sys.platform)
    return os.path.join(here, "bin", "%s-%s" % (system, arch))


def find_executable(names, env_var):
    """Look for a helper program (srsieve, LLR) under any of ``names``.

    Order: the environment variable, the bundled bin/<platform>/ folder,
    the current folder, then PATH. On Windows ".exe" is added to each name.
    A file that exists but is not executable is reported, not silently
    skipped (unzipping on Linux can drop the executable permission).
    """
    if isinstance(names, str):
        names = [names]
    suffix = ".exe" if os.name == "nt" else ""
    candidates = []
    if os.environ.get(env_var):
        candidates.append(os.environ[env_var])
    for folder in (platform_dir(), "."):
        candidates += [os.path.join(folder, n + suffix) for n in names]
    for c in candidates:
        if os.path.isfile(c):
            if os.access(c, os.X_OK):
                return os.path.abspath(c)
            print("found %s but it is not executable; run: chmod +x %s" % (c, c),
                  file=sys.stderr)
    for n in names:
        found = shutil.which(n)
        if found:
            return found
    return None


def run_sieve(base, tag="", pmax=None, srsieve=None, growth=4, datadir="data",
              sievedir=SIEVE_DIR, out=sys.stdout):
    """Run srsieve on one base in rounds, merging after each round.

    Each round sieves up to growth * (current pmin), so srsieve finishes and
    writes its file normally. This works the same on Windows and Linux (the
    C version stopped srsieve every 2 hours with the Unix ``timeout`` command).
    Stops at ``pmax`` if given, otherwise runs until interrupted (Ctrl-C).
    """
    srsieve = srsieve or find_executable("srsieve", "BRIGHT_SRSIEVE")
    if not srsieve:
        print("srsieve not found: build it (see README) or set BRIGHT_SRSIEVE", file=out)
        return 1
    work = file_for("sieve", base, tag, sievedir)
    if not os.path.exists(work):
        src = file_for("sieve", base, tag, datadir)
        if not os.path.exists(src):
            print("No sieve file for base %d!" % base, file=out)
            return 1
        write_lines(work, read_lines(src))
    try:
        while True:
            header = read_lines(work)[:1]
            current = int(header[0].split("=")[1]) if header and header[0].startswith("pmin=") else 31
            if pmax is not None and current >= pmax:
                break
            target = current * growth if pmax is None else min(current * growth, pmax)
            print("sieving base %d from p = %d to %d" % (base, current, target), file=out, flush=True)
            subprocess.run([srsieve, "-q", "-P", str(target), work, "-o", work], check=True)
            merge(datadir, sievedir)
    except KeyboardInterrupt:
        print("interrupted; merging", file=out)
        merge(datadir, sievedir)
    return 0
