"""Search unsolved simple families for primes (port of mepn's simple.c).

For each length n from N to M, and each family ``x y* z`` in every
``data/unsolved.<b>.txt``, the candidate x y^n z is checked:

* if it contains a known minimal prime, the whole family is dropped (every
  longer member contains it too);
* if it is (probably) prime, it is added to ``data/minimal.<b>.txt`` and the
  family is dropped (later members contain it);
* otherwise the family stays unsolved.

Usage:  python -m bright simple N M
        python -m bright simple - M     continue each file from where it stopped

The last length finished for each file is kept in ``data/simple.<b>.txt``
(e.g. ``data/simple.10.3mod4.txt``). It records the highest L such that
every length up to L has been done, so a run that skips lengths does not
move it forward. ``minimal`` deletes it when it writes a new unsolved list.

Afterwards run ``python -m bright organize`` to sort the lists and remove any
entry that contains another.
"""

import sys
import time

from .digits import parser
from .common import (append_line, data_files, file_for, in_target_set, parse_simple,
                     read_lines, subword, write_lines)


class _KernelCheck:
    """Smallest number of repeated digits at which a family member contains
    a kernel prime. subword() does not depend on the length n, so each
    (family, prime) pair is matched only once, however many lengths are tried.
    """

    def __init__(self):
        self.seen = {}  # family line -> (kernel entries checked, smallest k or None)

    def min_k(self, line, start, middle, end, kernel):
        done, best = self.seen.get(line, (0, None))
        for p in kernel[done:]:
            found, k = subword(p, start, middle, end)
            if found and (best is None or k < best):
                best = k
        self.seen[line] = (len(kernel), best)
        return best


def read_progress(path):
    """Last length finished for an unsolved file, or None."""
    lines = read_lines(path)
    try:
        return int(lines[0]) if lines else None
    except ValueError:
        return None


def run_simple(n, m, datadir="data", out=sys.stdout):
    """Test lengths n..m. With n = None, each file continues after the last
    length recorded for it (or from length 1)."""
    files = data_files("unsolved", datadir)
    starts = {}
    for path, base, tag in files:
        done = read_progress(file_for("simple", base, tag, datadir))
        starts[path] = (done + 1 if done is not None else 1) if n is None else n
    if not files:
        print("No unsolved files in %s/" % datadir, file=out)
        return
    if n is None:
        for path, base, tag in files:
            print("base %d%s: continuing from length %d" % (base, tag, starts[path]),
                  file=out, flush=True)
    checks = {}
    for num in range(min(starts.values()), m + 1):
        begin = time.process_time()
        count = 0
        for path, base, tag in files:
            if num < starts[path]:
                count += sum(1 for _ in read_lines(path))
                continue
            kernel_path = file_for("minimal", base, tag, datadir)
            kernel = read_lines(kernel_path)
            check = checks.setdefault(path, _KernelCheck())
            if check.seen and len(kernel) < max(d for d, _ in check.seen.values()):
                check = checks[path] = _KernelCheck()  # file was edited externally
            remaining = []
            for line in read_lines(path):
                if "*" not in line or "{" in line:
                    # Not a simple family (the C program assumes these never
                    # occur); keep it untouched.
                    remaining.append(line)
                    count += 1
                    continue
                start, middle, end = parse_simple(line)
                k = check.min_k(line, start, middle, end, kernel)
                if k is not None and k <= num:
                    continue
                candidate = start + middle * num + end
                if in_target_set(parser(base)(candidate), tag):
                    print("%s%s^(%d)%s (base %d) probably prime" % (start, middle, num, end, base),
                          file=out, flush=True)
                    append_line(kernel_path, candidate)
                    kernel.append(candidate)
                else:
                    remaining.append(line)
                    count += 1
            write_lines(path, remaining)
            progress = file_for("simple", base, tag, datadir)
            done = read_progress(progress) or 0
            if num <= done + 1 and num > done:
                write_lines(progress, [str(num)])
        print("FINISHED LEVEL %d, COUNT REMAINING %d, TIME %f"
              % (num, count, time.process_time() - begin), file=out, flush=True)
        if count == 0:
            print("No unsolved families left; stopping", file=out, flush=True)
            break


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2:
        print("This program searches all unsolved simple families")
        print("for prime candidates between exponents n and m,")
        print("given on the command-line")
        print("Usage: python -m bright simple n m")
        print("       python -m bright simple - m   (continue each file from where it stopped)")
        return 0
    run_simple(None if argv[0] == "-" else int(argv[0]), int(argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
