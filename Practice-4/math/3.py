import math

n = float(input("Number of sides:"))
a = float(input("Length of side:"))

# x = (n-2)*math.pi/(2*n)
# y = a/(2*math.cos(x))
# s = a*y*math.sin(x)*n/2

s = n * a * a /(4*math.tan(math.pi/n))

print(int(s))

