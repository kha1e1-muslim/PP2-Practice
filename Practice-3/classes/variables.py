class Dog:
    def __init__(self, name, age):
        self.name = name  # instance variable
        self.age = age    # instance variable

dog1 = Dog("Buddy", 3)
dog2 = Dog("Max", 5)

print(dog1.name)  # Output: Buddy
print(dog2.name)  # Output: Max
