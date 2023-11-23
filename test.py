def add_numbers(num1, num2):
    # Adding two numbers
    sum_result = num1 + num2
    return sum_result

def subtract_numbers(num1, num2):
    # Subtracting the second number from the first
    difference_result = num1 - num2
    return difference_result

# Taking user input for two numbers
num1 = 1
num2 = 2

# Calling the functions with the input numbers
try:
    sum_result = add_numbers(num1, num2)
    difference_result = subtract_numbers(num1, num2)
except Exception as e:
        print(f"Error during execution: {e}")

# Printing the results
print(f"Sum: {sum_result}")
print(f"Difference: {difference_result}")
