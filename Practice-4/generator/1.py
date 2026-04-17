import sys
import math

def squares(n):
    i=1
    while i<=n:
        yield i*i
        i+=1

n = int(input())
print(*squares(n), sep='\n')