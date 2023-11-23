import struct

class JavaClassParser:
    def __init__(self, class_file_path):
        self.class_file_path = class_file_path

    def parse_class_file(self):
        with open(self.class_file_path, "rb") as file:
            # Read the class file header
            magic, minor_version, major_version = struct.unpack(">IHH", file.read(8))
            print(f"Magic: {hex(magic)}, Minor Version: {minor_version}, Major Version: {major_version}")

            # Extract other class file information
            constant_pool_count = struct.unpack(">H", file.read(2))[0]
            access_flags = struct.unpack(">H", file.read(2))[0]
            print("access_flags:", access_flags)
            # Skip interfaces, fields, and methods (you can parse them if needed)
            interfaces_count = struct.unpack(">H", file.read(2))[0]
            file.read(2 * interfaces_count)
            print("interface:", interfaces_count)
            fields_count = struct.unpack(">H", file.read(2))[0]
            file.read(8 * fields_count)
            print("fields count:", fields_count)
            methods_count = struct.unpack(">H", file.read(2))[0]
            file.read(8 * methods_count)
            print("methods count:", methods_count)
            # Parse the attributes to find checkpoints
            attributes_count = struct.unpack(">H", file.read(2))[0]
            print("attributes count:", attributes_count)
            for i in range(attributes_count):
                attribute_name_index = struct.unpack(">H", file.read(2))[0]
                attribute_length = struct.unpack(">I", file.read(4))[0]

                attribute_name = self.get_constant_pool_entry(constant_pool_count, attribute_name_index)
                print("attribute_name count:", attribute_length)
                if attribute_name == "CheckPoint":
                    # Handle CheckPoint attribute
                    # Now, you can parse the TLV structure and perform fuzzing
                    print(f"Found CheckPoint attribute with length: {attribute_length}")
                    self.parse_checkpoint(file, attribute_length)

    def parse_checkpoint(self, file, attribute_length):
        while attribute_length > 0:
            tag, length = struct.unpack(">BH", file.read(3))
            value = file.read(length)

            # Handle the TLV structure (fuzzing can be done here)
            print(f"Tag: {tag}, Length: {length}, Value: {value}")

            attribute_length -= 3 + length

    def get_constant_pool_entry(self, constant_pool_count, index):
        constant_pool = []

        # Read and store constant pool entries
        for i in range(constant_pool_count - 1):
            tag = struct.unpack(">B", file.read(1))[0]
            entry = None

            if tag == 1:  # Utf8 info
                length = struct.unpack(">H", file.read(2))[0]
                value = file.read(length).decode("utf-8")
                entry = f"Utf8: {value}"

            elif tag == 7:  # Class reference
                name_index = struct.unpack(">H", file.read(2))[0]
                entry = f"Class reference to pool index {name_index}"

            # Add more cases for other constant pool types as needed

            constant_pool.append(entry)

        # Return the entry at the specified index
        if 0 < index < constant_pool_count:
            return constant_pool[index - 1]  # Adjust index to match the constant pool array
        else:
            return None


if __name__ == "__main__":
    class_file_path = "testSmall.class"  # Replace with the path to your class file
    parser = JavaClassParser(class_file_path)
    parser.parse_class_file()
