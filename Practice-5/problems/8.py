import re

text = "SplitThisString"

result = re.findall(r"[A-Z][^A-Z]*", text)

print(result)