# Parent class
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        print(f"{self.name} makes a sound.")

# Child class
class Dog(Animal):
    pass  # Inherits everything from Animal

dog = Dog("Buddy")
dog.speak()  # Output: Buddy makes a sound.

# inheritance lets a child class reuse attributes and methods from a parent class, so you don’t have to rewrite code.
# Example   Dog inherits speak() from Animal without defining it.