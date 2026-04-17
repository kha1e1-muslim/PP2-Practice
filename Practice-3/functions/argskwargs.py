def my_function(greeting, *names):
  for name in names:
    print(greeting, name)

my_function("Hello", "Emil", "Tobias", "Linus")

# The *args parameter allows a function to accept any number of positional arguments.
# here, Hello is a "greting" and rest of strings are names.
# code will output:
# Hello Emil 
# Hello Tobias
# Hello Linus


# while we use * to input a list or smth like that into a function, we can use ** to input a dictionary:
def my_2nd_function(**myvar):
  print("Type:", type(myvar))
  print("Name:", myvar["name"])
  print("Age:", myvar["age"])
  print("All data:", myvar)

my_2nd_function(name = "Tobias", age = 30, city = "Bergen")

# The **kwargs parameter allows a function to accept any number of keyword arguments.
# Inside the function, kwargs becomes a dictionary containing all the keyword arguments

