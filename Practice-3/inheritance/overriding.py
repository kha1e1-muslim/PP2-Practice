class Animal:
    def speak(self):
        print("Animal makes a sound.")

class Dog(Animal):
    def speak(self):  # override the parent method
        print("Dog barks!")

animal = Animal()
dog = Dog()

animal.speak()  # Output: Animal makes a sound.
dog.speak()     # Output: Dog barks!

# A child class can replace a parent’s method with its own version to change behavior.
# Example: Dog overrides speak() to bark instead of using the parent’s generic sound.