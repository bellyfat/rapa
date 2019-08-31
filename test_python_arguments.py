

def func1(*args, **kwargs):
    print(args)
    print(kwargs)
    print(*args)

print("Call first time")
func1("asd", something="123")
print("Call second time")
func1("qwe", 123, 456)