import re

pattern = r"ab*"

test_strings = ["a", "ab", "abb", "ac"]

for s in test_strings:
    if re.fullmatch(pattern, s):
        print(s, "-> Match")