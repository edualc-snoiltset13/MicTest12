def hello_world():
    print("Hello World")


def greet(name):
    print(f"Hello, {name}!")


def add(a, b):
    return a + b


def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)


if __name__ == "__main__":
    hello_world()
    greet("Alice")
    print(f"2 + 3 = {add(2, 3)}")
    print(f"5! = {factorial(5)}")
