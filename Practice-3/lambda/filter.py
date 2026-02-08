# another great combo is lambda+filter we can filter out some values in the list. for example:
numbers = [1, 2, 3, 4, 5, 6, 7, 8]
odd_numbers = list(filter(lambda x: x % 2 != 0, numbers))
print(odd_numbers)
# here we kinda got rid of even numbers in our list

words = ["apple", "kiwi", "banana", "fig"]
long_words = list(filter(lambda w: len(w) > 4, words))
print(long_words)
# or we can filter strings by their size, outputs ['apple', 'banana']
# lambda+filter is very flexible, that's why it is useful
