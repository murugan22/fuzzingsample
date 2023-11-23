import struct

class JavaClassParser:
    def __init__(self, class_file_path):
        self.class_file_path = class_file_path

    def parse_class_file(self):
        with open(self.class_file_path, "rb") as file:
            self.magic = struct.unpack(">I", file.read(4))[0]
            self.minor_version = struct.unpack(">H", file.read(2))[0]
            self.major_version = struct.unpack(">H", file.read(2))[0]
            self.constant_pool_count = struct.unpack(">H", file.read(2))[0]
            print(f"Magic: {hex(self.magic)}, Minor Version: {self.minor_version}, Major Version: {self.major_version}")

            # Skip reading the constant pool (you may implement get_constant_pool_entry)
            for _ in range(self.constant_pool_count - 1):
                tag = struct.unpack(">B", file.read(1))[0]
                if tag == 1:  # Utf8 info
                    length = struct.unpack(">H", file.read(2))[0]
                    file.read(length)
                elif tag == 7:  # Class reference
                    file.read(2)
                # Add more cases for other constant pool types as needed

            self.access_flags = struct.unpack(">H", file.read(2))[0]
            self.this_class = struct.unpack(">H", file.read(2))[0]
            self.super_class = struct.unpack(">H", file.read(2))[0]
            self.interfaces_count = struct.unpack(">H", file.read(2))[0]
            
            # Skip reading interfaces
            file.read(2 * self.interfaces_count)

            self.fields_count = struct.unpack(">H", file.read(2))[0]
            self.fields = self.parse_fields(file, self.fields_count)

            # Now you can access the fields outside the main method

    def parse_fields(self, file, fields_count):
        fields = []
        for _ in range(fields_count):
            access_flags = struct.unpack(">H", file.read(2))[0]
            name_index = struct.unpack(">H", file.read(2))[0]
            descriptor_index = struct.unpack(">H", file.read(2))[0]
            attributes_count = struct.unpack(">H", file.read(2))[0]

            field_info = {
                "access_flags": access_flags,
                "name_index": name_index,
                "descriptor_index": descriptor_index,
                "attributes_count": attributes_count,
                "attributes": self.parse_attributes(file, attributes_count),
            }

            fields.append(field_info)
        return fields

    def parse_attributes(self, file, attributes_count):
        attributes = []
        for _ in range(attributes_count):
            try:
                attribute_name_index = struct.unpack(">H", file.read(2))[0]
            except struct.error as e:
                # Handle the error gracefully, e.g., by displaying an error message
                #print("Error: Not enough bytes available for unpacking.")
                attribute_name_index = None  # Set a default value or raise a specific exception
            try:
                attribute_length = struct.unpack(">I", file.read(4))[0]
            except struct.error as e:
                # Handle the error gracefully, e.g., by displaying an error message
                #print("Error: Not enough bytes available for unpacking.")
                attribute_length = None  # Set a default value or raise a specific exception
            
            attribute_info = {
                "attribute_name_index": attribute_name_index,
                "attribute_length": attribute_length,
            }
            file.read(attribute_length)  # Skip attribute content for simplicity
            attributes.append(attribute_info)
        return attributes
if __name__ == "__main__":
    class_file_path = "test.class"  # Replace with the path to your class file
    parser = JavaClassParser(class_file_path)
    parser.parse_class_file()
