import dis
import random
import types
import marshal
import struct
import os
import subprocess
import shutil
import sys
DEBUG = True

# Whether to perform backtracking
BACKTRACK = True

# Parameters for the program
NUM_SEQ = 1
MIN_LEN = 1#1200
MAX_ERR = 30
num_created = 0
class Fuzzer:
    def __init__(self):
        self.num_created = 0
        
    def fuzz_opcode(self,original_code, instruction):
        # Fuzz the opcode of a single instruction
        new_opcode = random.randint(1, dis.opmap['RETURN_VALUE'])
        
        return types.CodeType(
            original_code.co_argcount,
            original_code.co_posonlyargcount,
            original_code.co_kwonlyargcount,
            original_code.co_nlocals,
            original_code.co_stacksize,
            original_code.co_flags,
            original_code.co_code.replace(bytes([instruction.opcode]), bytes([new_opcode])),
            original_code.co_consts,
            original_code.co_names,
            original_code.co_varnames,
            'outtest.py',
            original_code.co_name,
            original_code.co_firstlineno,
            b'',  # Correcting co_lnotab
            original_code.co_freevars,
            original_code.co_cellvars
        )

    def execute_modified_bytecode_file(self,filename):
        try:
            # Open and execute the modified bytecode file
            with open(filename, 'rb') as bytecode_file:
                modified_bytecode = marshal.load(bytecode_file)
                exec(modified_bytecode, globals())

        except SystemExit:
            print("Caught SystemExit. Continuing execution.")
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt. Continuing execution.")
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

        return True
    def get_python_magic_number(self):
        version_info = sys.version_info

        # Check the major version for Python 3
        if version_info.major == 3:
            # Use the little-endian format for the version
            version_bytes = version_info.minor.to_bytes(2, byteorder='little')
            
            # Constant value for Python 3
            magic_number = version_bytes + b'\x0d'
            return magic_number
        else:
            # Handle Python 2 or other versions
            raise NotImplementedError("Unsupported Python version")
    def execute_binary(self) -> str:
            """
            Runs a subprocess which invokes the PVM on the input written to the temp file in
            the call to generate()

            No parameters

            Returns one of the following strings: "Complete", "Incomplete", "Incorrect" or "Error",
                indicating whether the sequence was complete, incomplete, incorrect (i.e. invalid instruction) or
                any other type of error (these are both incorrect states but we need some way to differentiate)
            """

            args = []
            for i in range(1000):
                args.append(hex(i))
            #command = ["python", f"python output_classes/test{self.num_created}/testpython.pyc"]
            #print("final file to run:", command)
            
            try:
                print(f"output_classes/test{self.num_created}")
                testdir = f"output_classes/test{self.num_created}"
                
                result = subprocess.run(
                    ["python", f"output_classes/test{self.num_created}","tests", *args],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=2,
                )
                
                #result = subprocess.run(f"python output_classes/test{self.num_created}/testpython.pyc", check=True, capture_output=True, text=True)
                print("result after executing", result)
            except subprocess.TimeoutExpired:
                return "Error"

            stderr = result.stderr.decode("utf-8")

            if DEBUG:
                print(result.stdout.decode("utf-8"))
                print(stderr)

            if len(stderr) != 0:
                err = stderr.strip().split("\n")
                
                
                if "Invalid" not in err[0]:
                    return "Complete"

                if "Invalid pc" in err[0] or "Control flow" in err[0]:
                    return "Incomplete"
                elif "Bad instruction" in err[0]:
                    if err[0].strip().split(": ")[-1] != "Bad instruction":
                        if int(err[0].strip().split(": ")[-1], 16) >= 0xC9:
                            return "Error"

                    if (
                        err[4].strip().split()[-1] == "<illegal>"
                        or err[4].strip().split()[-1][:5] == "fast_"
                    ):
                        return "Error"
                    else:
                        return "Bad"
                else:
                    return "Error"

            # no exceptions
            return "Complete"

    def generate(
                self,
                min_len: int,
                max_err: int,
                start: str,
                end: str,
                code_attr_len: int,
                max_lcls: int,
            ) -> bytes:
                """
                Returns a sequence of complete instructions for the JVM as TLV-encoded bytes.

                Params:
                    int min_len :: the minimum length for the sequences
                    int max_err :: the maximum times we can attempt adding a new instruction before backtracking
                    str start :: the starting prefix for the class file
                    str end :: the ending suffix for the class file
                    code_attr_len :: the length of the code attribute itself without any code
                """
                # Skip magic number
                #start += 4
                #end += 4
                #Setting max stack to 512 and number of locals to 7
                pre = b"\x20\x00" + max_lcls.to_bytes(2, byteorder="big")
                input = b""
                err_cnt = 0

                while True:

                    num = random.randrange(0, 255)
                    while num == 0xaa or num == 0xab or num == 0xc4 or num == 0xa9 or num == 0xa8 or num == 0xc9 or num == 0x0a0d0d0a:
                        num = random.randrange(0, 255)

                    '''
                    while hex(num) == "0xaa" or hex(num) == "0xab" or hex(num) == "0xc4" or hex(num) == "0xab" or hex(num) == "0xa9" or hex(num) == "0xa8" \
                        or hex(num) == "0xc9":
                        num = random.randrange(0, 255)
                    '''    
                    print("Number is:", num)
                    #Backtrack
                    if BACKTRACK and err_cnt > max_err:
                        input = input[:-1]
                        total =  self.get_python_magic_number() +  (code_attr_len + len(input)).to_bytes(4, byteorder="big") + pre + len(input).to_bytes(4, byteorder="big") + input

                        if DEBUG:
                            print(total)

                        f = open(f"output_classes/test{self.num_created}/testpython.pyc", "wb")
                        f.write(start)
                        f.write(total)
                        f.write(end)
                        f.close()  
                        result = self.execute_binary()

                        while result == "Bad":
                            input = input[:-1]
                            total = self.get_python_magic_number() + (code_attr_len + len(input)).to_bytes(4, byteorder="big") + pre + len(input).to_bytes(4, byteorder="big") + input

                            if DEBUG:
                                print(total)

                            f = open(f"output_classes/test{self.num_created}/testpython.pyc", "wb")
                            f.write(start)
                            f.write(total)
                            f.write(end)
                            f.close()  
                            result = self.execute_binary()
                        
                        err_cnt = 0
                        continue
                    

                    input += num.to_bytes(1, byteorder="big")
                    
                    try:
                        if code_attr_len >= 0:
                            print("p")
                            #Need to write the input to a temp file, can't pass through the subprocess since 0x00 is a valid instruction
                            #   but will cause the subprocess to run into the wrong null terminator
                            total = self.get_python_magic_number() + (code_attr_len + len(input)).to_bytes(4, byteorder="big") + pre + len(input).to_bytes(4, byteorder="big") + input
                            
                            if DEBUG:
                                print(total)

                            f = open(f"output_classes/test{num_created}/testpython.pyc", "wb")
                            print("start:", start)
                            print("end:", total)
                            f.write(start)
                            f.write(total)
                            f.write(end)
                            f.close()  
                            
                            #Want to figure out if the sequence so far is complete, incomplete or incorrect
                            result = self.execute_binary()
                            #print("result prinintg sir:",result)
                            if DEBUG:
                                print(result)
                                print("\n--------------------------------------------------\n")

                            if result == "Complete":

                                
                                #Want to disregard this and see if we can keep going
                                if len(input) < min_len:
                                    #input = input[:-1]
                                    continue
                                    
                                return input
                                
                            elif result == "Error":
                                input = input[:-1]
                                err_cnt += 1
                                continue
                            elif result == "Incomplete":
                                err_cnt = 0
                                pass
                            elif result == "Bad":
                                if BACKTRACK:
                                    err_cnt = 0
                                else:
                                    input = input[:-1]
                                    err_cnt += 1
                            else:
                                continue
                        else:
                            print("negative",code_attr_len)
                            input = input[:-1]
                            return input        
                    except OverflowError as e:
                        # Handle the OverflowError, e.g., print a message or log the error
                        print(f"OverflowError: {e}")
                        # Continue to the next iteration of the loop
                        continue
                    

    def pyFuzzer(self):
        filename = './test.py'
        with open(filename, 'rb') as file:
            original_code = file.read()

        # Compile the original code
        original_code_object = compile(original_code, filename, 'exec')
        bytecode = original_code_object.co_code
        length_attr = struct.unpack("!I", bytecode[:4])[0]
        instructions = list(dis.get_instructions(original_code_object))
        
          
        max_locals = 0
        for i, instruction in enumerate(instructions):
            print(instruction)
            opcode_bytes = instruction.opcode.to_bytes(2, byteorder='little')
            print(f"Opcode: {opcode_bytes}, Instruction: {instruction}")
            start_index = instruction.positions.col_offset
            end_index = instruction.positions.end_col_offset
            if end_index == None or start_index == None :
                continue
            print("end index:", end_index)
            locals_used = instruction.arg
            instruction_length = end_index - instruction.offset
            if locals_used is not None:
                max_locals = max(max_locals, locals_used)
        
            #print(f"Maximum number of local variables used by any instruction: {max_locals}")
            #start_index = instruction.offset
            #end_index = start_index + 2  # Assuming a 2-byte opcode, adjust as needed
            print(f"Instruction: {instruction.opname}, instruction Start Index: {start_index}, Instruction End Index: {end_index}")
            valid = list()
            f = open("./test.pyc", "rb")
            #f.tell()
            f.seek(0)
            
            start_idx = f.read(16)
            print("sri:",start_idx)
            f.seek(end_index)
            end = f.read(end_index)
            f.close()
            while len(valid) < NUM_SEQ:
                if not os.path.exists(f"output_classes/test{self.num_created}"):
                    os.mkdir(f"output_classes/test{self.num_created}")
                #shutil.copyfile("test.pyc", f"output_classes/test{self.num_created}/testpython.pyc")
                
                valid.append(
                    self.generate(MIN_LEN, MAX_ERR,start_index.to_bytes(1, byteorder='big'), end_index.to_bytes(1, byteorder='big'),  instruction_length, max_locals)
                )
                
                self.num_created += 1
            for i in range(len(valid)):
                tmp = valid[i]
                valid[i] = list()
                for j in range(len(tmp)):
                    valid[i].append(tmp[j])
            print("method name")
            
                



if __name__ == "__main__":
    Fuzzer().pyFuzzer()