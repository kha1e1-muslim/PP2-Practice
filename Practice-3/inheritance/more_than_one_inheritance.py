class Mother:
    def skills(self):
        print("Cooking")

class Father:
    def skills(self):
        print("Gardening")

class Child(Mother, Father):
    def skills(self):
        Mother.skills(self)
        Father.skills(self)
        print("Child also learns coding")

c = Child()
c.skills()
# Output:
# Cooking
# Gardening
# Child also learns coding

# A class can inherit from more than one parent, combining behaviors, with Python following Method Resolution Order (MRO) to decide which parent’s method to use first.
# Example: Child(Mother, Father) inherits skills from both, but Mother’s method is used first by default.