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
        self.tag = 0
        self.info = None
    def from_reader(self, file):
        self.tag = struct.unpack(">B", file.read(1))[0]
        if self.tag in {1, 7}:  # CONSTANT_Utf8 or CONSTANT_Class
            self.info = struct.unpack(">H", file.read(2))[0]
        elif self.tag == 5:  # CONSTANT_Long
            self.info = struct.unpack(">Q", file.read(8))[0]
        elif self.tag == 6:  # CONSTANT_Double
            self.info = struct.unpack(">Q", file.read(8))[0]
        # Add cases for other CPInfo types as needed

    def __str__(self):
        return f"Tag: {self.tag}, Info: {self.info}"
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

    def main_finder(self, path: str) -> tuple:
        """
        Finds where main is located and returns the start point at which we
        need to modify the class file from (namely the length of the Code attribute) and
        the end point of the code. It also returns how long the attribute is without the
        code itself: important since the attribute itself needs a size in the classfile.

        Parameters:
            str path :: a path to the class file
        """
        f = open(path, "rb")

        magic = struct.unpack(">I", f.read(4))[0]
        minor_version = struct.unpack(">H", f.read(2))[0]
        major_version = struct.unpack(">H", f.read(2))[0]
        constant_pool_count = struct.unpack(">H", f.read(2))[0]
        print("cnst:",constant_pool_count)
        # Create a list to store the constant pool entries
        constant_pool = [None]  # The constant pool is 1-based, so we add a placeholder at index 0

        # Iterate through the constant pool entries
        i = 1
        while i < constant_pool_count:
            cp_info = CPInfo()
            print(cp_info)
            cp_info.from_reader(f)
            constant_pool.append(cp_info)
            if cp_info.tag in {5, 6}:  # Long and Double entries take two slots in the constant pool
                constant_pool.append(None)
                i += 2
            else:
                i += 1
            # Seeking past magic and classfile edition
            f.seek(8, 0)

        # Going through the constant pool now
        # Important to keep these since we need to keep track of the
        # constants to know when we hit the main method and code attribute
        const_count = struct.unpack("!H", f.read(2))[0]
        i = 1
        consts = list()
        while i < const_count:
            c = CPInfo().from_reader(f)
            consts.append(c)
            if c.tag == CPTag.DOUBLE:
                consts.append(CPInfo())
                i += 1

            i += 1

        # Seeking past access flags and class name indexes
        f.seek(6, 1)

        # Moving past the interfaces
        interface_count = struct.unpack("!H", f.read(2))[0]
        for i in range(interface_count):
            struct.unpack("!H", f.read(2))[0]

        # Moving past the fields
        fcnt = struct.unpack("!H", f.read(2))[0]
        for i in range(fcnt):
            fi = FieldInfo().from_reader(f)

        # At the methods section
        mcnt = struct.unpack("!H", f.read(2))[0]
        print("Method count:", mcnt)
        # Iterates through the methods until we find main
        for i in range(mcnt):
             # Read the attributes_count (u2 value)
            attributes_count = struct.unpack(">H", f.read(2))[0]

            # Variables to keep track of method start and end indices
            method_start_index = f.tell()
            method_end_index = 0

            # Iterate through the attributes associated with the method
            for _ in range(attributes_count):
                attribute_name_index = struct.unpack(">H", f.read(2))[0]
                attribute_length = struct.unpack(">I", f.read(4))[0]

                # Get the attribute name from the constant pool
                attribute_name = constant_pool[attribute_name_index - 1]
                if attribute_name["tag"] == 1 and attribute_name["bytes"] == "Code":
                    # This is the "Code" attribute, and you can read the bytecode
                    # Get the start of the bytecode
                    code_start_index = f.tell()

                    # Read the code_length (u4 value)
                    code_length = struct.unpack(">I", f.read(4))[0]

                    # Seek past the bytecode to find the end of the code
                    f.seek(code_length, 1)

                    # Update the method_end_index
                    method_end_index = f.tell()

                    # Now you can process the bytecode for the current method, which starts from code_start_index
                    # and ends at method_end_index

            # You can print or store the method indices as needed
            print(f"Method {method_name} starts at index {method_start_index} and ends at index {method_end_index}")
            '''
            print("count:",mi.access_flags)
            f.seek(2, 1)
            name_idx = struct.unpack("!H", f.read(2))[0]
            print("name of the method:",consts[name_idx - 1].string )
            f.seek(2, 1)
            attr_cnt = struct.unpack("!H", f.read(2))[0]

            # Iterate through the attributes of each method
       
        for j in range(attr_cnt):
            # Attempt to read 2 bytes from the file
            data = f.read(2)

            # Check if there are enough bytes to unpack
            if len(data) == 2:
                name_idx = struct.unpack("!H", data)[0]
            else:
                # Handle the case when there are not enough bytes
                print("Not enough bytes available to unpack.")
                break
            #name_idx = struct.unpack("!H", f.read(2))[0]
            print("Name of the method:",consts[name_idx - 1].string)
            # If the attribute is "Code," read the code and fuzz it
            if consts[name_idx - 1].string == "Code":
                start_idx = f.tell()
                length_attr = struct.unpack("!I", f.read(4))[0]
                max_stk = struct.unpack("!H", f.read(2))[0]
                max_lcls = struct.unpack("!H", f.read(2))[0]
                length_code = struct.unpack("!I", f.read(4))[0]
                code_attr_length = length_attr - length_code

                # Read the code
                code = f.read(length_code)

                # Fuzz the code here
                # Example: Randomly modify the code bytes
                fuzzed_code = bytearray(random.getrandbits(8) for _ in range(length_code))

                # Write the fuzzed code back
                f.seek(start_idx)
                f.write(fuzzed_code)

                # Seek to the end of the code attribute
                f.seek(code_attr_length, 1)
            else:
                # Attempt to read 2 bytes from the file
                data = f.read(4)

                # Check if there are enough bytes to unpack
                if len(data) == 4:
                    length = struct.unpack("!I", f.read(4))[0]
                else:
                    # Handle the case when there are not enough bytes
                    print("Not enough bytes available to unpack length field")
                    break
                
                f.seek(length, 1)
                '''
        f.close()

        return start_idx, end_idx, code_attr_length, max_lcls

    def get_valid(self, num: int, min_len: int, max_err: int) -> list:
        """
        Returns a list of complete sequences of instructions for the JVM.

        Params:
            int num :: the specified number of sequences to generate
            int min_len :: the minimum length for the sequences
            int max_err :: the maximum times we can attempt adding a new instruction before backtracking
        """

        start_idx, end_idx, code_attr_length, max_lcls = self.main_finder(
            "./testSmall.class"
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

        return valid


if __name__ == "__main__":
    valid = Fuzzer().get_valid(NUM_SEQ, MIN_LEN, MAX_ERR)
    print(*valid, sep="\n")
