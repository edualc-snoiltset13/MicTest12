def primes_up_to(limit):
    primes = []
    for n in range(2, limit + 1):
        if all(n % p != 0 for p in primes if p * p <= n):
            primes.append(n)
    return primes


if __name__ == "__main__":
    print(primes_up_to(100))
