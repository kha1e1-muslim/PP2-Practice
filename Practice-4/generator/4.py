import sys
import math

def squares(a, b):
    i=a
    while i<=b:
        yield i*i
        i+=1

a = list(map(int, input().split()))
print(*squares(a[0], a[1]), sep='\n')