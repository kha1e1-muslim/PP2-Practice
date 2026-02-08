class Animal:
    def __init__(self, name):
        self.name = name

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name)  # call parent __init__
        self.breed = breed

    def info(self):
        print(f"{self.name} is a {self.breed}.")

dog = Dog("Buddy", "Golden Retriever")
dog.info()  # Output: Buddy is a Golden Retriever

# super() allows a child class to call methods of its parent,
# often used in __init__ to keep parent initialization while adding new attributes.
# Example: Dog calls super().__init__(name) to set name from Animal while adding breed.