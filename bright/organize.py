"""Sort the minimal prime lists and remove redundant entries (port of organize.c).

Each ``data/minimal.*.txt`` is sorted by length, then lexicographically, and
any entry that contains an earlier entry as a subsequence is removed.

Usage:  python -m bright organize
"""

import re
import sys

from .common import data_files, read_lines, write_lines


def _is_subsequence(q, p):
    it = iter(p)
    return all(c in it for c in q)


class _SubwordIndex:
    """Fast "does p contain any stored string as a subsequence" test."""

    CHUNK = 64

    def __init__(self):
        self.items, self.frozen, self.tail = [], [], None

    @staticmethod
    def _compile(qs):
        alts = ["".join("[^%s]*%s" % (re.escape(c), re.escape(c)) for c in q) for q in qs]
        return re.compile("(?:" + "|".join(alts) + ")").match

    def add(self, q):
        self.items.append(q)
        n = len(self.items)
        if n % self.CHUNK == 0:
            self.frozen.append(self._compile(self.items[n - self.CHUNK:]))
            self.tail = None
        else:
            self.tail = self._compile(self.items[n - n % self.CHUNK:])

    def contains_subword(self, p):
        return any(m(p) for m in self.frozen) or (self.tail is not None and self.tail(p) is not None)


def organize_file(path, base, out=sys.stdout):
    print("organizing base %d..." % base, file=out)
    lines = sorted(read_lines(path), key=lambda s: (len(s), s))
    kept = []
    index = _SubwordIndex()
    for i, line in enumerate(lines):
        # Testing against kept lines gives the same decision as testing
        # against all earlier lines (subsequence is transitive). For the
        # message, report the first earlier line, as the C program does.
        if index.contains_subword(line):
            first = next(lines[j] for j in range(i) if _is_subsequence(lines[j], line))
            print("%s has a subword %s" % (line, first), file=out)
        else:
            kept.append(line)
            index.add(line)
    write_lines(path, kept)
    return kept


def run_organize(datadir="data", out=sys.stdout):
    for path, base, _tag in data_files("minimal", datadir):
        organize_file(path, base, out)


def main(argv=None):
    run_organize()
    return 0


if __name__ == "__main__":
    sys.exit(main())
