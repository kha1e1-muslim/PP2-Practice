import sys
import math

def countdown(n):
    i=n
    while i>=0:
        yield i
        i-=1

n = int(input())
print(*countdown(n), sep='\n')
