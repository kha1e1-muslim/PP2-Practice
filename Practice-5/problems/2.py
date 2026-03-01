import re

pattern = r"ab{2,3}"

test_strings = ["abb", "abbb", "abbbb", "ab"]

for s in test_strings:
    if re.fullmatch(pattern, s):
        print(s, "-> Match")