import subprocess
import random
import struct
import os
from pyjvm.CPInfo import CPInfo, CPTag
from pyjvm.FieldInfo import FieldInfo
from pyjvm.AttributeInfo import AttributeInfo

# Whether to print Debug messages or not
DEBUG = True

# Whether to perform backtracking
BACKTRACK = True

# Parameters for the program
NUM_SEQ = 1
MIN_LEN = 1200
MAX_ERR = 30



class Fuzzer:
    def __init__(self):
        self.num_created = 0
        

    def execute_binary(self) -> str:
        """
        Runs a subprocess which invokes the JVM on the input written to the temp file in
        the call to generate()

        No parameters

        Returns one of the following strings: "Complete", "Incomplete", "Incorrect" or "Error",
            indicating whether the sequence was complete, incomplete, incorrect (i.e. invalid instruction) or
            any other type of error (these are both incorrect states but we need some way to differentiate)
        """

        args = []
        for i in range(1000):
            args.append(hex(i))

        try:
            testdir = f"output_classes/test{self.num_created}"
            result = subprocess.run(
                ["java", "-cp", testdir, "tests", *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=2,
            )
        except subprocess.TimeoutExpired:
            return "Error"

        stderr = result.stderr.decode("utf-8")

        if DEBUG:
            print(result.stdout.decode("utf-8"))
            print(stderr)

        if len(stderr) != 0:
            err = stderr.strip().split("\n")

            if "java.lang.VerifyError" not in err[1]:
                return "Complete"

            if "Invalid pc" in err[1] or "Control flow" in err[1]:
                return "Incomplete"
            elif "Bad instruction" in err[1]:
                if err[1].strip().split(": ")[-1] != "Bad instruction":
                    if int(err[1].strip().split(": ")[-1], 16) >= 0xC9:
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

        # Setting max stack to 512 and number of locals to 7
        pre = b"\x20\x00" + max_lcls.to_bytes(2, byteorder="big")
        instructions = b""
        err_cnt = 0

        while True:
            num = random.randrange(0, 255)

            while (
                hex(num) == "0xaa"
                or hex(num) == "0xab"
                or hex(num) == "0xc4"
                or hex(num) == "0xab"
                or hex(num) == "0xa9"
                or hex(num) == "0xa8"
                or hex(num) == "0xc9"
            ):
                num = random.randrange(0, 255)

            # Backtrack
            if BACKTRACK and err_cnt > max_err:
                instructions = instructions[:-1]
                total = (
                    (code_attr_len + len(instructions)).to_bytes(4, byteorder="big")
                    + pre
                    + len(instructions).to_bytes(4, byteorder="big")
                    + instructions
                )

                if DEBUG:
                    print(total)

                f = open(f"output_classes/test{self.num_created}/tests.class", "wb")
                f.write(start)
                f.write(total)
                f.write(end)
                f.close()
                result = self.execute_binary()

                while result == "Bad":
                    instructions = instructions[:-1]
                    total = (
                        (code_attr_len + len(instructions)).to_bytes(4, byteorder="big")
                        + pre
                        + len(instructions).to_bytes(4, byteorder="big")
                        + instructions
                    )

                    if DEBUG:
                        print(total)

                    f = open(f"output_classes/test{self.num_created}/tests.class", "wb")
                    f.write(start)
                    f.write(total)
                    f.write(end)
                    f.close()
                    result = self.execute_binary()

                err_cnt = 0
                continue

            if DEBUG:
                print(len(instructions), num)

            # # TLV encoding: Type (1 byte), Length (1 byte), Value (1 byte)
            # instruction = bytes([0x01, 0x01, num])
            # instructions += instruction

            # Need to write the input to a temp file, can't pass through the subprocess since 0x00 is a valid instruction
            #   but will cause the subprocess to run into the wrong null terminator
            total = (
                (code_attr_len + len(instructions)).to_bytes(4, byteorder="big")
                + pre
                + len(instructions).to_bytes(4, byteorder="big")
                + instructions
            )

            if DEBUG:
                print(total)

            f = open(f"output_classes/test{self.num_created}/tests.class", "wb")
            f.write(start)
            f.write(total)
            f.write(end)
            f.close()

            # Want to figure out if the sequence so far is complete, incomplete, or incorrect
            result = self.execute_binary()

            if DEBUG:
                print(result)
                print("\n--------------------------------------------------\n")

            if result == "Complete":
                # Want to disregard this and see if we can keep going
                if len(instructions) < min_len:
                    instructions = instructions[:-1]
                    continue
                return instructions

            elif result == "Error":
                instructions = instructions[:-1]
                err_cnt += 1
                continue
            elif result == "Incomplete":
                err_cnt = 0
                pass
            elif result == "Bad":
                if BACKTRACK:
                    err_cnt = 0
                else:
                    instructions = instructions[:-1]
                    err_cnt += 1
            else:
                continue
    
    def main_finder(self, path: str) -> list:
        f = open(path, "rb")

        # Seek past the class file header
        f.seek(8)

        # Read the constant pool
        const_count = struct.unpack("!H", f.read(2))[0]
        i = 1
        consts = list()

        # Add a flag to track if we're inside a method
        inside_method = False

        while i < const_count:
            c = CPInfo().from_reader(f)
            #print("Tag:", c.tag.value)
            if c.tag.value != 1:
                print("Tag:", c.tag.value)
            #if c.tag == CPTag.METHODREF or c.tag == CPTag.FIELDREF:    
            consts.append(c)
            '''
            if inside_method:
                consts.append(c)
                #print("checking:",c.tag)

            if c.tag == CPTag.METHODREF:
                # We've entered a new method or field, so set the flag accordingly
                inside_method = True
                #print("consts:",c.tag.name)
            '''
            i += 1

        # Seek past access flags and class name indexes
        f.seek(6, 1)

        # Move past the interfaces
        interface_count = struct.unpack("!H", f.read(2))[0]
        f.seek(interface_count * 2, 1)

        # Move past the fields
        fcnt = struct.unpack("!H", f.read(2))[0]
        totalfieldCount = 0
        for i in range(fcnt):
            fi = FieldInfo().from_reader(f)
            totalfieldCount +=1
        #all_methods = pyjvm.methods(f)
        # Find the methods section
        mcnt = struct.unpack("!H", f.read(2))[0]
        fcnt -=7
        print("Method Count:", totalfieldCount)

        method_info_list = []  # Store method information
        #const_count = const_count-2
        for i in range(const_count):
            print("Method count:updating",mcnt)
            try:
                f.seek(2, 1)
                name_idx = struct.unpack("!H", f.read(2))[0]
            except:
                readLen = f.read(4)
                #Not the "Code" attribute, so keep iterating
                if len(readLen) > 0:
                    length = struct.unpack("!H", readLen)[0]
                    print("exiting")
                    mcnt += 2
                #continue
                
            if(name_idx !=1):
                #name_idx = struct.unpack("!H",dataRead)[0]
                #print("Length:",len(dataRead))
                #print("f.read(2):",struct.unpack("!H",dataRead)[0])
                #name_idx = struct.unpack("!H",dataRead)[0]#struct.unpack("!H", f.read(2))[0]
               
                try:
                    if 0 <= name_idx - 1 < len(consts):
                        name = consts[name_idx - 1].string
                        
                        try:
                            f.seek(2, 1)
                            attr_cnt = struct.unpack("!H", f.read(2))[0]
                        except:
                            print("exiting1")
                            readLen = f.read(4)
                            if len(readLen) > 0:
                                length = struct.unpack("!H", readLen)[0]
                            #mcnt += 2
                            #continue
                        #f.seek(2, 1)
                        #attr_cnt = struct.unpack("!H", f.read(2))[0]
                        method_indexes = []  # Store indexes for each method
                        print("attr_count:", attr_cnt,"method count:",i)
                        
                        # Iterates through the attributes in the method
                        for j in range(attr_cnt):
                            try:
                                #f.seek(2, 1)
                                attribute_name_index = struct.unpack("!H", f.read(2))[0]
                            except:
                                readLen = f.read(4)
                                #Not the "Code" attribute, so keep iterating
                                if len(readLen) > 0:
                                    length = struct.unpack("!H", readLen)[0]
                                #mcnt += 2
                                print("exiting2")
                                #continue
                            #attribute_name_index = struct.unpack("!H", f.read(2))[0]
                            if 0 <= attribute_name_index - 1 < len(consts):
                                attribute_name = consts[attribute_name_index - 1].string
                                #attribute_name = consts[attribute_name_index - 1].string
                                print("Attribute Name:", attribute_name)    
                        
                            # Check if the attribute is "Code"
                            if (attribute_name == "Code") :
                                #print("code is present",struct.unpack('!H', f.read(2))[0])
                                method_indexes.append(f.tell())  # Store the index
                                start_idx = f.tell()
                                length_attr = struct.unpack("!I", f.read(4))[0]

                                # Seek past locals and max stack
                                max_stk = struct.unpack("!H", f.read(2))[0]
                                max_lcls = struct.unpack("!H", f.read(2))[0]

                                length_code = struct.unpack("!I", f.read(4))[0]
                                code_attr_length = length_attr - length_code

                                f.seek(length_code, 1)
                                end_idx = f.tell()
                                print("New name:", name)
                                method_info = {
                                    "name": name,
                                    "start_idx": start_idx,
                                    "end_idx": end_idx,
                                    "code_attr_length": code_attr_length,
                                    "max_lcls": max_lcls,
                                    "indexes": method_indexes  # Store the indexes for this method
                                }

                                method_info_list.append(method_info)
                                #print("Method Info Name:", method_info_list)
                            else:
                                print("else")
                                readLen = f.read(4)
                                #Not the "Code" attribute, so keep iterating
                                if len(readLen) > 0:
                                    length = struct.unpack("!H", readLen)[0]
                                const_count -=1
                                #mcnt += 2
                                #f.seek(length, 1)
                        print("Finished processing method:", name)
                    else:
                        #length = struct.unpack("!I", f.read(4))[0]
                        print("Error: Index out of range for index", name_idx - 1)
                        #mcnt += 2
                except AttributeError:
                    #length = struct.unpack("!I", f.read(4))[0]
                    print("Error: 'CPInfo' object has no attribute 'string' for index", name_idx - 1)
                    #mcnt += 2
            else:
                const_count -=1
                readLen = f.read(4)
                if len(readLen) > 0:
                    length = struct.unpack("!I", readLen)[0]
                    print("Data read is empty:")
                #mcnt += 1
                #mcnt = mcnt+1
                #continue
                #length = struct.unpack("!H", f.read(2))
                #f.seek(length, 1)
        f.close()
        print(method_info_list)
        return method_info_list
    
       
    def main_finder1(self, path: str) -> list:
        f = open(path, "rb")

        # Seek past the class file header
        f.seek(8)

        # Read the constant pool
        const_count = struct.unpack("!H", f.read(2))[0]
        i = 1
        consts = list()

        # Add a flag to track if we're inside a method
        inside_method = False

        while i < const_count:
            c = CPInfo().from_reader(f)

            if c.tag.value != 1:
                print("Tag:", c.tag.value)

            if inside_method:
                consts.append(c)

            if c.tag == CPTag.METHODREF:
                # We've entered a new method or field, so set the flag accordingly
                inside_method = True
              
            i += 1
        print("consts sir:",constants) 
        # Seek past access flags and class name indexes
        f.seek(6, 1)

        # Move past the interfaces
        interface_count = struct.unpack("!H", f.read(2))[0]
        f.seek(interface_count * 2, 1)

        # Move past the fields
        fcnt = struct.unpack("!H", f.read(2))[0]
        for i in range(fcnt):
            fi = FieldInfo().from_reader(f)

        # Find the methods section
        mcnt = struct.unpack("!H", f.read(2))[0]

        print("Method Count:", mcnt)

        method_info_list = []  # Store method information

        for i in range(mcnt):
            f.seek(2, 1)
            name_idx = struct.unpack("!H", f.read(2))[0]

            try:
                if 0 <= name_idx - 1 < len(consts):
                    name = consts[name_idx - 1].string
                    print("Method Name sir:", name)
                    f.seek(2, 1)
                    attr_cnt = struct.unpack("!H", f.read(2))[0]
                    method_indexes = []  # Store indexes for each method
                    print("attr_count:", attr_cnt)

                    # Iterates through the attributes in the method
                    for i in range(attr_cnt):
                        attribute_name_index = struct.unpack("!H", f.read(2))[0]
                        attribute_name = consts[attribute_name_index - 1].string
                        print("Attribute Name:", attribute_name)    
                      
                        # Check if the attribute is "Code"
                        if (attribute_name == "code") :
                            print("code is present")
                            method_indexes.append(f.tell())  # Store the index
                            start_idx = f.tell()
                            length_attr = struct.unpack("!I", f.read(4))[0]

                            # Seek past locals and max stack
                            max_stk = struct.unpack("!H", f.read(2))[0]
                            max_lcls = struct.unpack("!H", f.read(2))[0]

                            length_code = struct.unpack("!I", f.read(4))[0]
                            code_attr_length = length_attr - length_code

                            f.seek(length_code, 1)
                            end_idx = f.tell()
                            print("New name:", name)
                            method_info = {
                                "name": name,
                                "start_idx": start_idx,
                                "end_idx": end_idx,
                                "code_attr_length": code_attr_length,
                                "max_lcls": max_lcls,
                                "indexes": method_indexes  # Store the indexes for this method
                            }

                            method_info_list.append(method_info)
                            #print("Method Info Name:", method_info_list)
                        else:
                            # Not the "Code" attribute, so keep iterating
                            length = struct.unpack("!I", f.read(4))[0]
                            f.seek(length, 1)
                    print("Finished processing method:", name)
                else:
                    print("Error: Index out of range for index", name_idx - 1)
            except AttributeError:
                print("Error: 'CPInfo' object has no attribute 'string' for index", name_idx - 1)

        f.close()
        print(method_info_list)
        return method_info_list
    def get_valid(self, num: int, min_len: int, max_err: int) -> list:
        """
        Returns a list of complete sequences of instructions for the JVM.

        Params:
            int num :: the specified number of sequences to generate
            int min_len :: the minimum length for the sequences
            int max_err :: the maximum times we can attempt adding a new instruction before backtracking
        """
        valid = list()
        main_methods = self.main_finder(
            "./testmain.class"
        )
        
        for main_method in main_methods:
            #print(main_method["start_idx"])
            f = open("./testmain.class", "rb")
            start = f.read(main_method["start_idx"])
            f.seek(main_method["end_idx"])
            end = f.read(-1)
            f.close()

            valid = list()
            while len(valid) < num:
                if not os.path.exists(f"output_classes/test{self.num_created}"):
                    os.mkdir(f"output_classes/test{self.num_created}")
                valid.append(
                    self.generate(min_len, max_err,start, end,  main_method["code_attr_length"], main_method["max_lcls"])
                )
                self.num_created += 1
            for i in range(len(valid)):
                tmp = valid[i]
                valid[i] = list()
                for j in range(len(tmp)):
                    valid[i].append(tmp[j])
                
        '''
        start_idx, end_idx, code_attr_length, max_lcls = self.main_finder(
            "./tests.class"
        )
        print("FROM FIND MAIN:")
        print("start index of main " + str(start_idx))
        print("end index of main " + str(end_idx))
        print("Code attr length " + str(code_attr_length))
        print("max lcls " + str(max_lcls))


        f = open("./tests.class", "rb")
        start = f.read(start_idx)
        f.seek(end_idx)
        end = f.read(-1)
        f.close()

        valid = list()
        while len(valid) < num:
            if not os.path.exists(f"output_classes/test{self.num_created}"):
                os.mkdir(f"output_classes/test{self.num_created}")
            valid.append(
                self.generate(min_len, max_err, start, end, code_attr_length, max_lcls)
            )
            self.num_created += 1

        # Converting the byte string into a list of the numeric values of each byte
        #   e.g. b"\x08" becomes [8]
        for i in range(len(valid)):
            tmp = valid[i]
            valid[i] = list()
            for j in range(len(tmp)):
                valid[i].append(tmp[j])
        '''
        return valid


if __name__ == "__main__":
    valid = Fuzzer().get_valid(NUM_SEQ, MIN_LEN, MAX_ERR)
    print(*valid, sep="\n")