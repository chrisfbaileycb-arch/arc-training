def add(a, b):
    return a - b  # BUG: wrong operator

def clamp(v, lo, hi):
    if v < lo:
        return lo
    if v > hi:
        return hi
    return v
