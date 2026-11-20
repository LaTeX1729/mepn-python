"""The Bright Algorithm command line.

    python -m bright minimal BASES [--class a m | --class m]
                                                 minimal primes; BASES is "L H",
                                                 a list like 2-10,16, or a list
                                                 comprehension; --class m runs
                                                 every a with gcd(a, m) = 1
    python -m bright simple N M                  test unsolved families at lengths N..M
    python -m bright simple - M                  continue each file up to length M
    python -m bright organize                    sort lists, drop redundant entries
    python -m bright sieve-start N M             make sieve files for lengths N..M
    python -m bright sieve BASES [--class a m | --class m] [--pmax P]
                                                 run srsieve on the given bases
    python -m bright merge                       merge sieve and search progress
    python -m bright search N M [B [I]]          test sieved candidates (LLR if found)

A typical run:

    python -m bright minimal 2 20
    python -m bright simple 1 1000
    python -m bright organize
    python -m bright sieve-start 1000 20000
    python -m bright sieve 17 --pmax 1e9
    python -m bright search 1000 20000
    python -m bright organize

For a residue class, add --class a m to minimal and to sieve; the other
commands pick up the tagged files in data/ by themselves.
"""

import os
import sys


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    if cmd == "minimal":
        from .minimal import main as run
        return run(rest)
    if cmd == "simple":
        from .simple import main as run
        return run(rest)
    if cmd == "organize":
        from .organize import main as run
        return run(rest)
    if cmd == "search":
        from .search import main as run
        return run(rest)
    if cmd in ("sieve-start", "sieve", "merge"):
        from . import sieving
        if cmd == "merge":
            sieving.merge()
            return 0
        if cmd == "sieve-start":
            if len(rest) < 2:
                print("Usage: python -m bright sieve-start N M")
                return 0
            sieving.start_sieve(int(rest[0]), int(rest[1]))
            return 0
        if not rest:
            print("Usage: python -m bright sieve BASES [--class a m | --class m] [--pmax P] [--srsieve PATH]")
            return 0
        from .minimal import coprime_residues, parse_bases
        opts = {"--pmax": None, "--srsieve": None}
        tags = [""]
        base_args = []
        i = 0
        while i < len(rest):
            if rest[i] in opts:
                opts[rest[i]] = rest[i + 1]
                i += 2
            elif rest[i] == "--class":
                nums = []
                for a in rest[i + 1:i + 3]:
                    if a.lstrip("-").isdigit():
                        nums.append(int(a))
                    else:
                        break
                if len(nums) == 2:
                    tags = [".%dmod%d" % (nums[0] % nums[1], nums[1])]
                elif nums:
                    # --class m: every coprime class that has a sieve file
                    tags = [".%dmod%d" % (a, nums[0]) for a in coprime_residues(nums[0])]
                else:
                    print("--class needs a m, or just m")
                    return 2
                i += 1 + len(nums)
            else:
                base_args.append(rest[i])
                i += 1
        try:
            bases = parse_bases(base_args)
        except ValueError as e:
            print(e)
            return 2
        pmax = int(float(opts["--pmax"])) if opts["--pmax"] else None
        status = 0
        for base in bases:
            for tag in tags:
                if len(tags) > 1 and not os.path.exists(
                        sieving.file_for("sieve", base, tag, "data")):
                    continue
                status |= sieving.run_sieve(base, tag, pmax=pmax, srsieve=opts["--srsieve"])
        return status
    print("Unknown command %r. Try: python -m bright --help" % cmd)
    return 2


if __name__ == "__main__":
    sys.exit(main())
