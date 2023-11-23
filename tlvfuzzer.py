import os
import random


class TLVParser:
    def __init__(self):
        self.error_codes = []

    def parse_bytecode(self, bytecode):
        try:
            while len(bytecode) > 0:
                # Extract the next TLV structure
                print("INITIAL BYTECODE: ")
                print(bytecode)
                tag = bytecode[0:1]
                print("TAG: ")
                print(tag)
                bytecode = bytecode[1:]

                print("POST TAG BYTECODE: ")
                print(bytecode)

                if not bytecode:
                    # Error: Incomplete data (missing length and value)
                    self.error_codes.append("Incomplete data")
                    fuzzed_value = bytes(random.getrandbits(8) for _ in range(length))
                    print(f"Fuzzed Value: {fuzzed_value}")
                    break

                if len(bytecode) < 2:
                    # Error: Incomplete data (missing length bytes)
                    fuzzed_value = bytes(random.getrandbits(8) for _ in range(length))
                    print(f"Fuzzed Value: {fuzzed_value}")
                    self.error_codes.append("Incomplete data")
                    break

                length_bytes = bytecode[0:2]
                bytecode = bytecode[2:]
                length = length_bytes[0] * 256 + length_bytes[1]

                print("length bytes ")
                print((length_bytes))

                print("Length:")
                print(length)

                if len(bytecode) < length:
                    # Error: Incorrect byte length (length exceeds available data)
                    self.error_codes.append("Incorrect byte length")
                    print("Length - " + str(length))
                    fuzzed_value = bytes(random.getrandbits(8) for _ in range(length))
                    print(f"Fuzzed Value: {fuzzed_value}")
                    break

                if length == 0:
                    # Error: Missing size
                    self.error_codes.append("Missing size")
                    fuzzed_value = bytes(random.getrandbits(8) for _ in range(length))
                    print(f"Fuzzed Value: {fuzzed_value}")
                    break

                value = bytecode[0:length]
                bytecode = bytecode[length]

                # Process the tag, length, and value here

        except Exception as e:
            # Handle other exceptions and set an appropriate error code
            self.error_codes.append(f"Other error: {str(e)}")

    def get_error_codes(self):
        return self.error_codes


class Fuzzer:
    def __init__(self):
        self.generated_values = []

    def generate_values(self, error_codes):
        generated_values = []

        for code in error_codes:
            if code == "Incomplete data":
                # Generate value for incomplete data error
                generated_values.append("default_value_for_incomplete_data")
            elif code == "Missing size":
                # Generate value for missing size error
                generated_values.append("default_value_for_missing_size")
            elif code == "Incorrect byte length":
                # Generate value for incorrect byte length error
                generated_values.append("default_value_for_incorrect_byte_length")
            # Add more conditions for other error codes as needed ssss

        # Store the generated values in the instance variable
        self.generated_values = generated_values

    def get_generated_values(self):
        return self.generated_values

# # Example usage
# fuzzer = Fuzzer()
# error_codes = ["Incomplete data", "Missing size", "Incorrect byte length"]

# # Generate values based on error codes using the Fuzzer
# fuzzer.generate_values(error_codes)
# generated_values = fuzzer.get_generated_values()

# # Print the generated values to the console
# print("Generated Values IN fuzzer:")
# for value in generated_values:
#     print(value)



def file_read(filename):

    parser = TLVParser()

    #Hard Coding the string to test
    bytecodes = b'\x00\x01\x1d\x16\x00\n\x00\x00\x00\t\x1d\x17\x00\x1a'
    parser.parse_bytecode(bytecodes)
    error_codes = parser.get_error_codes()

    # with open(filename, 'rb') as bytecode_file:
    #     bytecodes = bytecode_file.read().splitlines()
    #     for bytecode in bytecodes:
    #         parser.parse_bytecode(bytecode)
    #         error_codes = parser.get_error_codes()

    #         if error_codes:
    #             # Handle errors based on the error codes
    #             for error_code in error_codes:
    #                 print(f"Error: {error_code}")
                
                # Generate values based on error codes using the Fuzzer
                # fuzzer = Fuzzer()
                # fuzzer.generate_values(error_codes)
                # generated_values = fuzzer.get_generated_values()

       


if __name__ == '__main__':

    file_read("sample_bytecode.txt")
