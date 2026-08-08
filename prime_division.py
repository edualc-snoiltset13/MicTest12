def prime_factorization(n):
    """
    Realiza a fatoração em números primos de um número inteiro positivo.
    
    Args:
        n (int): Número a ser fatorado
        
    Returns:
        dict: Dicionário com fatores primos e suas potências
        
    Exemplo:
        >>> prime_factorization(60)
        {2: 2, 3: 1, 5: 1}  # 60 = 2² × 3 × 5
    """
    if n < 2:
        return {}
    
    factors = {}
    divisor = 2
    
    while n > 1:
        while n % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            n //= divisor
        divisor += 1
        
        if divisor * divisor > n and n > 1:
            factors[n] = factors.get(n, 0) + 1
            break
    
    return factors


def format_factorization(factors):
    """
    Formata a fatoração de forma legível.
    
    Args:
        factors (dict): Dicionário de fatores primos
        
    Returns:
        str: String formatada (ex: "2² × 3 × 5")
    """
    if not factors:
        return "1"
    
    terms = []
    for prime in sorted(factors.keys()):
        power = factors[prime]
        if power == 1:
            terms.append(str(prime))
        else:
            terms.append(f"{prime}^{power}")
    
    return " × ".join(terms)


def divide_by_primes(n, prime_list):
    """
    Divide um número sucessivamente pelos números primos fornecidos.
    
    Args:
        n (int): Número a ser dividido
        prime_list (list): Lista de números primos
        
    Returns:
        list: Tuplas (divisor, resultado, resto)
    """
    results = []
    current = n
    
    for prime in prime_list:
        if current == 0:
            break
        quotient, remainder = divmod(current, prime)
        results.append((prime, quotient, remainder))
        if remainder == 0:
            current = quotient
    
    return results


def get_primes_up_to(limit):
    """
    Gera todos os números primos até um limite usando Crivo de Eratóstenes.
    
    Args:
        limit (int): Limite superior
        
    Returns:
        list: Lista de números primos
    """
    if limit < 2:
        return []
    
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, limit + 1, i):
                sieve[j] = False
    
    return [i for i in range(2, limit + 1) if sieve[i]]


if __name__ == "__main__":
    # Exemplos de uso
    print("=== FATORAÇÃO EM NÚMEROS PRIMOS ===\n")
    
    test_numbers = [60, 100, 97, 256, 1000]
    
    for num in test_numbers:
        factors = prime_factorization(num)
        formatted = format_factorization(factors)
        print(f"{num} = {formatted}")
    
    print("\n=== DIVISÃO POR LISTA DE PRIMOS ===\n")
    
    primes = get_primes_up_to(20)
    print(f"Primos até 20: {primes}\n")
    
    num = 120
    divisions = divide_by_primes(num, primes)
    print(f"Dividindo {num} pelos primos:\n")
    for divisor, quotient, remainder in divisions:
        print(f"  {num} ÷ {divisor} = {quotient} (resto: {remainder})")
