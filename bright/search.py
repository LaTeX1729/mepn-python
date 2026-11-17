"""Search sieved families for primes (port of mepn's search.c).

After ``sieve-start`` (and optionally ``sieve``), tests the remaining
exponents of each unsolved family in increasing order. The first prime found
in a family is added to ``data/minimal.<b>.txt`` and the family is removed.

Primality testing uses LLR (http://jpenne.free.fr) if it can be found, as
the C version does. LLR is much faster for numbers with thousands of digits.
Otherwise the built-in test is used (gmpy2 if installed, else pure Python).

Usage::

    python -m bright search N M            # exponents N..M, all bases
    python -m bright search N M B          # only base B
    python -m bright search N M B I        # only the I-th family of base B
    python -m bright search -              # everything left in the sieve files

Options: ``--llr PATH`` (or the BRIGHT_LLR environment variable),
``--no-llr`` to force the built-in test.
"""

import os
import subprocess
import sys
import tempfile

from .common import (append_line, class_of, data_files, family_sequence, file_for,
                     has_kernel_subword, in_target_set, parse_simple, read_lines, write_lines)
from .sieving import find_executable, format_sieve, parse_sieve

INF = 0x7FFFFFFF


def llr_test(llr, base, A, c, C, q, llr_arg=None):
    """Run LLR on (A * base^c + C) / q. Returns 'PRP', 'composite' or None."""
    fd, path = tempfile.mkstemp(prefix="llr-", suffix=".txt", dir=".")
    with os.fdopen(fd, "w", newline="\n") as fh:
        fh.write("ABC ($a*$b^$c$d)/$e\n")
        fh.write("%d %d %d %+d %d\n" % (A, base, c, C, q))
    cmd = [llr, path, "-d"] + (["-a" + llr_arg] if llr_arg else [])
    print(" ".join(cmd), flush=True)
    try:
        output = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace").stdout
    finally:
        os.remove(path)
    if "(Factored" in output:
        output = output[: output.index("(Factored")]
    print(output, end="", flush=True)
    if "PRP" in output:
        return "PRP"
    if "not prime" in output:
        return "composite"
    return None


def _remove_family(datadir, path, family, base, tag, sieve_path, sieve_family):
    write_lines(path, [l for l in read_lines(path) if l != family])
    header, blocks = parse_sieve(read_lines(sieve_path))
    write_lines(sieve_path, format_sieve(header, [b for b in blocks if b[0] != sieve_family]))


def run_search(n, m=None, only_base=None, only_family=None, llr=None, llr_arg=None,
               datadir="data"):
    everything = m is None
    i = n if n is not None else 0
    while everything or i <= m:
        numsleft = False
        minexpfound = INF
        for path, base, tag in data_files("unsolved", datadir):
            if only_base is not None and base != only_base:
                continue
            sieve_path = file_for("sieve", base, tag, datadir)
            kernel_path = file_for("minimal", base, tag, datadir)
            for countfam, family in enumerate(read_lines(path), start=1):
                if only_family is not None and countfam != only_family:
                    continue
                if "*" not in family or "{" in family:
                    continue
                start, middle, end = parse_simple(family)
                K, C, q, A, zlen = family_sequence(base, start, middle, end)
                sieve_family = "%d*%d^n%+d" % (K, base, C)

                # First remaining exponent >= i (as in search.c).
                num = -1
                _, blocks = parse_sieve(read_lines(sieve_path))
                for fam, exps in blocks:
                    if fam == sieve_family:
                        for e in exps:
                            num = e
                            if num >= i:
                                break
                        break
                if num != -1:
                    minexpfound = min(minexpfound, num)
                    numsleft = True
                if num == -1 or num != i:
                    continue

                candidate = start + middle * num + end
                kernel = read_lines(kernel_path)
                print("Checking %s(%s^%d)%s (base %d)..." % (start, middle, num, end, base), flush=True)
                p = has_kernel_subword(kernel, start, middle, end, num)
                if p is not None:
                    print("%s(%s^%d)%s (base %d) has a minimal subword %s"
                          % (start, middle, num, end, base, p), flush=True)
                    _remove_family(datadir, path, family, base, tag, sieve_path, sieve_family)
                    continue

                cls = class_of(tag)
                value = (A * base ** (num + zlen) + C) // q
                if cls is not None and value % cls[1] != cls[0]:
                    result = "composite"  # outside the class: not a candidate
                elif llr:
                    result = llr_test(llr, base, A, num + zlen, C, q, llr_arg)
                else:
                    result = "PRP" if in_target_set(value, tag) else "composite"
                    print("%s(%s^%d)%s (base %d) is %s" % (
                        start, middle, num, end, base,
                        "a probable prime" if result == "PRP" else "not prime"), flush=True)

                if result is None:
                    print("LLR gave no result for %s(%s^%d)%s (base %d); stopping"
                          % (start, middle, num, end, base), flush=True)
                    return 1
                if result == "PRP":
                    _remove_family(datadir, path, family, base, tag, sieve_path, sieve_family)
                    append_line(kernel_path, candidate)
                elif result == "composite":
                    header, blocks = parse_sieve(read_lines(sieve_path))
                    blocks = [(f, [e for e in exps if not (f == sieve_family and e == num)])
                              for f, exps in blocks]
                    write_lines(sieve_path, format_sieve(header, blocks))
        if everything and not numsleft:
            break
        i = minexpfound
        if not everything and i == INF:
            break
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    llr, use_llr = None, True
    if "--no-llr" in argv:
        argv.remove("--no-llr")
        use_llr = False
    if "--llr" in argv:
        k = argv.index("--llr")
        llr = argv[k + 1]
        del argv[k:k + 2]
    if not argv or (len(argv) == 1 and argv[0] != "-"):
        print(__doc__)
        return 0
    if use_llr and llr is None:
        llr = find_executable("llr", "BRIGHT_LLR") or find_executable("cllr64", "BRIGHT_LLR")
    if not use_llr:
        llr = None
    print("primality test: %s" % (llr or "built-in"), flush=True)
    if argv[0] == "-":
        return run_search(0, None, llr=llr)
    n, m = int(argv[0]), int(argv[1])
    only_base = int(argv[2]) if len(argv) > 2 else None
    only_family = int(argv[3]) if len(argv) > 3 and argv[3] != "-" else None
    llr_arg = argv[4] if len(argv) > 4 else None
    return run_search(n, m, only_base, only_family, llr, llr_arg)


if __name__ == "__main__":
    sys.exit(main())
