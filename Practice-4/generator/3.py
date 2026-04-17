import sys

def solve():
    n = int(sys.stdin.readline())
    if n >= 0:
        for i in range(0, n+1, 12):
            sys.stdout.write(str(i) + ' ')

if __name__ == "__main__":
    solve()