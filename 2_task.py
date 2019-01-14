import sys
import math

#обновление 1
a = int(sys.argv[1])
b = int(sys.argv[2])
c = int(sys.argv[3])

if a is None:
    a = 0
    x1 = -c/b
    print(int(x1))
else:
    if b is None:
        b = 0

    if c is None:
        c = 0

    D = (b * b) - (4 * a * c)
    if D > 0:
        x1 = (-b + math.sqrt(D)) / (2 * a)
        x2 = (-b - math.sqrt(D)) / (2 * a)
        print(int(x2))
        print(int(x1))

    if D == 0:
        x1 = x2 = -b / (2 * a)
        print(int(x1))
        print(int(x2))

    if D < 0:
        print('Solve is exception')