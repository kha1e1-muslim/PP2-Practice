import re

text = "Hello world MyName Test"

pattern = r"\b[A-Z][a-z]+\b"

matches = re.findall(pattern, text)
print(matches)