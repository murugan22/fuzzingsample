import subprocess
import random
import os
import shutil
import struct

class JavaClassFuzzer:
    def __init__(self, class_file_path, output_dir):
        self.class_file_path = class_file_path
        self.output_dir = output_dir

    def fuzz_class_structure(self, start_pos, end_pos):
        with open(self.class_file_path, "r+b") as file:
            # Calculate lengths and positions for tag, length, and value
            tag_start = start_pos
            tag_end = start_pos + 1
            length_start = tag_end
            length_end = length_start + 2
            value_start = length_end
            value_end = end_pos

            # Fuzz the tag, length, and value
            fuzzed_tag = random.randint(0, 255).to_bytes(1, byteorder="big")
            fuzzed_length = random.randint(0, 65535).to_bytes(2, byteorder="big")
            fuzzed_value = struct.pack(">I", random.randint(0, 2**32 - 1))
            
            #file.seek(tag_start)
            #file.write(fuzzed_tag)
            #file.seek(length_start)
            #file.write(fuzzed_length)
            file.seek(start_pos)
            file.write(fuzzed_value)

    def execute_with_fuzz(self):
        # Create a separate directory for modified class files
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        while True:
            # Prepare the output file path
            output_file_path = os.path.join(self.output_dir, os.path.basename(self.class_file_path))

            # Fuzz the "magic" field
            start_pos = 0
            end_pos = 4  # Assuming "magic" field has tag, length, and value
            self.fuzz_class_structure(start_pos, end_pos)

            # Save the modified class file to the output directory
            shutil.copy(self.class_file_path, output_file_path)

            # Execute the modified class using the JVM
            try:
                subprocess.run(["java", "-cp", ".", "test"], check=True)
                print("Execution successful. Fuzzing completed.")
                break  # Exit the loop when execution is successful
            except subprocess.CalledProcessError as e:
                # Handle any errors or exceptions here
                print(f"Error while executing the modified class: {e}")

if __name__ == "__main__":
    class_file_path = "test.class"  # Replace with the path to your class file
    output_dir = "output"  # Directory to store modified class files
    fuzzer = JavaClassFuzzer(class_file_path, output_dir)
    fuzzer.execute_with_fuzz()
