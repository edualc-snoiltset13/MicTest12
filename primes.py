def primes_up_to(limit):
    if limit < 2:
        return []
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit + 1, i):
                sieve[j] = False
    return [n for n, is_prime in enumerate(sieve) if is_prime]


if __name__ == "__main__":
    print(primes_up_to(100))
