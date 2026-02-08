# lambda is a mini function
# syntax is "lambda arguments : expression"
x = lambda a : a + 10
print(x(5))
# this code would output 5+10=15
# also we can have more than 1 parameter:
y = lambda a, b : a * b
print(y(5, 6))

z = lambda a, b, c : a + b + c
print(z(5, 6, 2))
