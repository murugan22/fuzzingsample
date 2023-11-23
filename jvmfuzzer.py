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
                print("Error reporting:",err[1])
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
                print("reslt thambi:", result)
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

        # Iterates through the methods until we find main
        for i in range(mcnt):
            f.seek(2, 1)
            name_idx = struct.unpack("!H", f.read(2))[0]
            print("Name:",consts[name_idx - 1].string)
            if consts[name_idx - 1].string == "main":
                main = False
            else:
                main = True
            f.seek(2, 1)
            attr_cnt = struct.unpack("!H", f.read(2))[0]
            
            # Iterates through the attributes in main until we find the code attribute
            # If not main, simply keep iterating through the attributes until we get to the next
            # method
            for i in range(attr_cnt):
               
                if main:
                    name_idx = struct.unpack("!H", f.read(2))[0]
                    
                    # Once we find the code attribute we break since we know where it starts and ends
                    if consts[name_idx - 1].string == "Code":
                        start_idx = f.tell()
                        length_attr = struct.unpack("!I", f.read(4))[0]

                        # Seek past locals and max stack
                        max_stk = struct.unpack("!H", f.read(2))[0]
                        max_lcls = struct.unpack("!H", f.read(2))[0]

                        length_code = struct.unpack("!I", f.read(4))[0]
                        #print("length_code:",length_code )
                        code_attr_length = length_attr - length_code

                        f.seek(length_code, 1)
                        end_idx = f.tell()
                        break

                    # Not the code attribute so keep iterating
                    else:
                        length = struct.unpack("!I", f.read(4))[0]
                        f.seek(length, 1)

                else:
                    AttributeInfo().from_reader(f)

            # We've got main so no reason to keep looking through methods
            if main:
                break
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

        return valid


if __name__ == "__main__":
    valid = Fuzzer().get_valid(NUM_SEQ, MIN_LEN, MAX_ERR)
    print(*valid, sep="\n")
