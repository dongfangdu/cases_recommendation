def outer(a):
    b =10
    def inner():
        print(a+b)
    return inner

if __name__ == "__main__":
    demo = outer(5)
    demo()