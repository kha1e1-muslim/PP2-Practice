#  we can also use it use sort() function:
numbers = [5, -2, 9, -7, 0]
numbers.sort(key=lambda x: abs(x))
print(numbers)
#  for example in the code above, we sorted our values in numbers by their absolute value.

#  i think it is very useful to sort pair by their first or second element. liek this:
data = [(1, 3), (2, 1), (4, 2)]
data.sort(key=lambda x: x[1])
print(data)
#  it will output [(2, 1), (4, 2), (1, 3)]