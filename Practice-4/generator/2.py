import sys

def solve():
    n = int(sys.stdin.readline())
    if n >= 0:
        sys.stdout.write('0')
        for i in range(2, n+1, 2):
            sys.stdout.write(',' + str(i))

if __name__ == "__main__":
    solve()