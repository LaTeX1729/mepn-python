"""The Bright Algorithm: a Python translation of Curtis Bright's mepn."""

import sys

# Python 3.11+ refuses to convert digit strings longer than 4300 characters
# to integers (a guard against denial-of-service attacks). Minimal primes
# and candidates can have tens of thousands of digits, so lift the limit.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)
