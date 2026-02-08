class Car:
    # The __init__ method runs when a new Car is created
    def __init__(self, brand, color):
        self.brand = brand  # Attribute: brand of the car
        self.color = color  # Attribute: color of the car
# What __init__ is:
# __init__ is a special method in Python classes.
# It runs automatically when you create a new object (instance) of the class.
# Its job is to initialize the object’s attributes 
# give it its properties right when it’s created.


# Without __init__, you would have to set each attribute manually:
class Dog:
    pass
my_dog = Dog()
my_dog.name = "Buddy"
my_dog.age = 3
# with init, all of that would be automatic:
my_dog = Dog("Buddy", 3)