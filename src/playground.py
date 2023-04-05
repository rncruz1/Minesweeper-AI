from itertools import permutations

squares = list([(1, 1), (2, 2), (3, 3)])
for perm in permutations(squares, 2):
    print(perm)
