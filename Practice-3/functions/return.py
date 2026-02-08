def my_function(x, y):
  return x + y

result = my_function(5, 3)
print(result)

# here we assigned a variable which will contain the return of function. and then printed it.

def my_2nd_function():
  return (10, 20)

x, y = my_2nd_function()
print("x:", x)
print("y:", y)

#  there is a pair as a return, so we assigned TWO variables for them.
# also we can assign LIST for a return of the function:
def my_3rd_function():
  return ["apple", "banana", "cherry"]

fruits = my_3rd_function()
print(fruits[0])
print(fruits[1])
print(fruits[2])