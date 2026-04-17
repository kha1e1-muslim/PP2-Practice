class Car:
    def __init__(self, brand, color):
        self.brand = brand  
        self.color = color  
    
    # Method: a function that belongs to the class
    def drive(self):
        print(f"The {self.color} {self.brand} is driving!")
    
    def paint(self, new_color):
        self.color = new_color
        print(f"The car has been painted {self.color}.")

# methods define what an object of that class can do.
# Methods can use and modify the object’s attributes.
# it can be explained like this:
# Class = blueprint → Car
# Object = actual car → my_car
# Method = things the car can do → drive(), paint()


car1 = Car("Toyota", "red")
car2 = Car("Tesla", "blue")

car1.drive()  # Output: The red Toyota is driving!
car2.drive()  # Output: The blue Tesla is driving!

# Change the color of car1
car1.paint("green")  # Output: The car has been painted green.
car1.drive()          # Output: The green Toyota is driving!