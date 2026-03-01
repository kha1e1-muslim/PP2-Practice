import re

text = "hello_world test_var Invalid_Test"

pattern = r"\b[a-z]+_[a-z]+\b"

matches = re.findall(pattern, text)
print(matches)