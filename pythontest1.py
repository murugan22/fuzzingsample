import dis
import random
import copy
import types
import sys
import marshal
def fuzz_opcode(instruction,codintst):
    print(instruction.co_names)
    # Fuzz the opcode of a single instruction
    new_opcode = random.randint(1, dis.opmap['RETURN_VALUE'])
    print('arg val',instruction.co_filename)
    
    return types.CodeType(
        instruction.co_argcount,
        instruction.co_posonlyargcount,
        instruction.co_kwonlyargcount,
        instruction.co_nlocals,
        instruction.co_stacksize,
        instruction.co_flags,
        instruction.co_code.replace(bytes([codintst.opcode]), bytes([new_opcode])),
        instruction.co_consts,
        instruction.co_names,
        instruction.co_varnames,
        'outtest.py',
        instruction.co_name,
        str(instruction.co_firstlineno),
        1,  # Correcting co_lnotab
        instruction.co_freevars,
        instruction.co_cellvars
    )

def fuzz_byte_code():
    random_data = bytes([random.randint(0, 255)])
    return random_data    
def execute_modified_bytecode_file(filename):
    try:
        # Open and execute the modified bytecode file
        with open(filename, 'rb') as bytecode_file:
            modified_bytecode = bytecode_file.read()
            exec(modified_bytecode, globals())

    except SystemExit:
        print("Caught SystemExit. Continuing execution.")
    except KeyboardInterrupt:
        print("Caught KeyboardInterrupt. Continuing execution.")
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

    return True
def execute_fuzzed_code(fuzzed_code):
    try:
        print("ki:",fuzzed_code)
        exec(fuzzed_code,globals())
    except Exception as e:
        print(f"Error during execution: {e}")

def main():
    filename = 'test.py'

    with open(filename, 'r') as file:
        original_code = file.read()
        #print("original code object:",marshal.load(file))

    def target_function():
        # This function is just a placeholder to get the code object
        pass

    # Compile the original code
    original_code_object = compile(original_code, filename, 'exec')
    #Getting bytecode
    print('data bugging:',dis.dis(original_code_object))
    # Get the bytecode instructions 
    
    instructions = list(dis.get_instructions(original_code_object))
    #print(instructions)
    for _ in range(2):  # Perform 10 fuzzing attempts
        for i, instruction in enumerate(instructions):
            try:
                #print('hi there:',instruction.opcode)
                # Create a new code object with the fuzzed opcode
                fuzzed_code = fuzz_opcode(original_code_object,instruction)
                #fuzzed_code = fuzz_byte_code()
                #print('Fuzzed code:', fuzzed_code)
                # Write the modified code to a new file
                with open('outtest.py', 'wb') as output:
                    #dis.dis(fuzzed_code, file=output)
                    #output.write(fuzzed_code)
                    
                    marshal.dump(fuzzed_code, output)
                    #output.write(fuzzed_code)
                    # Execute the modified code
                with open('outtest.py', 'rb') as f:
                    #metadata = f.read(header_size)  
                    code_obj = marshal.load(f)
                    #print('sir disassembling:',dis.dis(code_obj))
                    
                execute_modified_bytecode_file('outtest.py')        
                #execute_fuzzed_code(fuzzed_code)
            except Exception as e:
                print(f"Error during execution: {e}")

if __name__ == "__main__":
    main()
