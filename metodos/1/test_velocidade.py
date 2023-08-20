from timeit import timeit

print(
    timeit("""
has_subtring = False
for i in ['a','b','c','d','e','f','g','h','i','j','k']:
    if i in "tkt":
        has_substring = True
        break
    """, number=10000000)
)

print(
    timeit("""
any([i in "tkt" for i in ['a','b','c','d','e','f','g','h','i','j','k']])
    """, number=10000000)
)

print(
    timeit("""
any(map("tkt".__contains__, ['a','b','c','d','e','f','g','h','i','j','k']))
    """, number=10000000)
)