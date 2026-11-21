#!/usr/bin/env bash
# run-class.sh - compute the minimal primes of a base in a residue class.
#
# Asks for the base, the class a mod m, a folder and the search ranges, then
# runs the whole pipeline in that folder:
#   minimal (or minimal resume), simple, organize, covering,
#   sieve-start, sieve, search, organize, covering
# Everything is logged to run.log in the folder. It can run in the background
# (with nohup), so it keeps going after the terminal is closed.
#
# Usage:  ./run-class.sh            (from anywhere; it finds the repository itself)

set -u

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PYTHONPATH="$REPO${PYTHONPATH:+:$PYTHONPATH}"
PY="$(command -v python3 || command -v python)"

# ---------------------------------------------------------------- the pipeline
run_pipeline() {
    # Uses: B A M DIR SIMPLE_MAX LO HI PMAX RESUME_ITER
    cd "$DIR" || exit 1
    local tag="$B.${A}mod$M"
    step() {
        echo
        echo "=== $(date '+%Y-%m-%d %H:%M:%S')  python -m bright $*"
        "$PY" -m bright "$@"
        local rc=$?
        [ $rc -ne 0 ] && echo "=== step exited with code $rc"
        return $rc
    }
    open_families() { [ -s "data/unsolved.$tag.txt" ] && grep -c . "data/unsolved.$tag.txt" || echo 0; }

    echo "=== Base $B, primes = $A mod $M, in $DIR"
    echo "=== Primality backend: $("$PY" -c 'import bright.primality as p; print(p.BACKEND)')"

    if [ -n "$RESUME_ITER" ]; then
        step minimal resume "$B" "$RESUME_ITER" --class "$A" "$M" || exit 1
    else
        step minimal "$B" --class "$A" "$M" || exit 1
    fi
    echo "=== minimal finished: $(open_families) open families"

    step simple 1 "$SIMPLE_MAX"
    step organize
    step covering
    if [ "$(open_families)" -gt 0 ]; then
        step sieve-start "$LO" "$HI"
        step sieve "$B" --class "$A" "$M" --pmax "$PMAX"
        step search "$LO" "$HI"
        step organize
        step covering
    fi

    local n; n=$(grep -c . "data/minimal.$tag.txt" 2>/dev/null || echo 0)
    local open; open=$(open_families)
    echo
    echo "=== $(date '+%Y-%m-%d %H:%M:%S')  done: $n minimal primes in data/minimal.$tag.txt"
    if [ "$open" -gt 0 ]; then
        echo "=== $open families still open (data/unsolved.$tag.txt). To search further:"
        echo "      PYTHONPATH=$REPO $PY -m bright sieve-start $((HI + 1)) $((HI + 10000))"
        echo "      PYTHONPATH=$REPO $PY -m bright sieve $B --class $A $M --pmax $PMAX"
        echo "      PYTHONPATH=$REPO $PY -m bright search -"
    else
        echo "=== complete: no open families."
    fi
}

# Background mode: the script calls itself with the answers in the environment.
if [ "${1:-}" = "--batch" ]; then
    run_pipeline
    exit $?
fi

# ------------------------------------------------------------------- questions
ask() {  # ask VAR "question" default
    local var=$1 q=$2 def=${3:-} ans
    if [ -n "$def" ]; then read -r -p "$q [$def]: " ans; else read -r -p "$q: " ans; fi
    printf -v "$var" '%s' "${ans:-$def}"
}
is_int() { [[ $1 =~ ^[0-9]+$ ]]; }
gcd() { local a=$1 b=$2; while [ "$b" -ne 0 ]; do local t=$((a % b)); a=$b; b=$t; done; echo "$a"; }

echo "Minimal primes in a residue class (mepn-python, $REPO)"
echo

ask B "Base (2-62)"
is_int "$B" && [ "$B" -ge 2 ] && [ "$B" -le 62 ] || { echo "The base must be a number from 2 to 62."; exit 1; }
ask M "Modulus m"
is_int "$M" && [ "$M" -ge 2 ] || { echo "The modulus must be a number of at least 2."; exit 1; }
ask A "Residue a (primes = a mod $M)"
is_int "$A" && [ "$A" -lt "$M" ] || { echo "The residue must be a number from 0 to $((M - 1))."; exit 1; }
if [ "$(gcd "$A" "$M")" -ne 1 ]; then
    echo "Note: gcd($A, $M) > 1, so this class contains at most one prime; the run will be quick."
fi

ask DIR "Folder for this run" "$PWD/$B.${A}mod$M"
mkdir -p "$DIR" || exit 1
DIR="$(cd "$DIR" && pwd)"

RESUME_ITER=""
ITER=$(ls "$DIR/iter" 2>/dev/null | sed -n "s/^unsolved-base$B\.${A}mod$M-iter\([0-9]*\)\.txt$/\1/p" | sort -n | tail -1)
if [ -n "$ITER" ] && [ -f "$DIR/iter/minimal-base$B.${A}mod$M-iter$ITER.txt" ]; then
    ask R "Found saved iteration $ITER of minimal in this folder. Resume from it? (y/n)" "y"
    [[ $R =~ ^[Yy] ]] && RESUME_ITER=$ITER
elif [ -f "$DIR/data/minimal.$B.${A}mod$M.txt" ]; then
    echo "Note: this folder already holds results for this class; they will be recomputed."
fi

ask SIMPLE_MAX "Lengths for simple: 1 to" "300"
ask LO "Search lengths from" "$SIMPLE_MAX"
ask HI "Search lengths to" "10000"
ask PMAX "Sieve primes up to (pmax)" "1e7"
for v in SIMPLE_MAX LO HI; do is_int "${!v}" || { echo "$v must be a whole number."; exit 1; }; done

ask BG "Run in the background, so it keeps going if you close the terminal? (y/n)" "y"

export B A M DIR SIMPLE_MAX LO HI PMAX RESUME_ITER PY REPO
if [[ $BG =~ ^[Yy] ]]; then
    nohup bash "${BASH_SOURCE[0]}" --batch >> "$DIR/run.log" 2>&1 &
    echo
    echo "Started in the background (process $!). Follow it with:"
    echo "    tail -f $DIR/run.log"
    echo "Stop it with:  kill $!"
else
    run_pipeline 2>&1 | tee -a "$DIR/run.log"
fi
