
class Foo:
    def __getattr__(self, key):
        if not 'name' in self.__dir__():
            self.name = 'unknown'
        return self.__getattribute__(key)

f = Foo()

name = f.name
print(f" name = {name} ")

age = f.age
print(f" age = {age} ")



