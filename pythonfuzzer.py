import dis
import io
import sys
import random


def get_instruction_length(filename):
    with open(filename, 'r') as file:
        code = compile(file.read(), filename, 'exec')

        # Get the bytecode instructions
        instructions = list(dis.get_instructions(code))

        # Calculate and print the length of each instruction
        for instruction in instructions:
            opcode_length = 1  # Opcode itself
            if instruction.opcode >= dis.HAVE_ARGUMENT:
                # Instruction has an argument, add its length
                opcode_length += 2 if instruction.opcode >= dis.HAVE_ARGUMENT else 0  # For Python 3.6+
                opcode_length += 2 if instruction.is_jump_target else 0  # For Python 3.6+

            print(f"Opcode: {instruction.opname}, Length: {opcode_length}")

def get_bytecode_instructions(filename):
    try:
        with open(filename, 'r') as file:
            code = compile(file.read(), filename, 'exec')
        print(code.co_code)
        # Disassemble the code object and get the bytecode instructions
        bytecode_instructions = dis.Bytecode(code)

        # Extract and print the bytecode instructions
        for instruction in bytecode_instructions:
            print(instruction)

    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def modify_bytecode_instructions(filename, output_file):
    try:
        with open(filename, 'r') as file:
            code = compile(file.read(), filename, 'exec')

        # Disassemble the code object and get the bytecode instructions
        bytecode_instructions = list(dis.Bytecode(code))

        # Read the original bytecode from the file
        with open(filename, 'rb') as bytecode_file:
            original_bytecode = bytecode_file.read()
        print("dai")
        # Open the output file for writing
        with open(output_file, 'wb') as output:
            index = 0
            for instruction in bytecode_instructions:
                opcode = instruction.opcode  # Get the opcode
                print(instruction)
                # Generate and write random data at the opcode position
                random_data = bytes([random.randint(0, 255)])

                # Modify only if it's a valid opcode (between 1 and 255)
                if 1 <= opcode <= 255:
                    output.write(random_data)
                else:
                    output.write(original_bytecode[index:index + 3])

                index += 3

            # Write any remaining original bytecode (if any)
            output.write(original_bytecode[index:])

    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def execute_modified_bytecode(filename):
    try:
        # Open and execute the modified bytecode file
        with open(filename, 'rb') as bytecode_file:
            bytecode = bytecode_file.read()
            exec(bytecode, globals())

    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    return True

if __name__ == "__main__":
    python_file = "test.py"  # Replace with the path to your Python file
    output_file = "modified_bytecode.py"  # Replace with the desired output file name

    success = False
    attempt_count = 0
    #get_instruction_length(python_file)

    #get_bytecode_instructions(python_file)
    
    while not success:
        print(f"Attempt {attempt_count + 1}:")
        
        # Step 1: Get the original bytecode instructions
        get_bytecode_instructions(python_file)
        
        # Step 2: Modify the bytecode instructions and create the modified bytecode file
        modify_bytecode_instructions(python_file, output_file)

        # Step 3: Execute the modified bytecode
        success = execute_modified_bytecode(output_file)

        attempt_count += 1
    
    print(f"Execution successful after {attempt_count} attempts.")
