class JavaClassParser:
    def __init__(self, class_file_path):
        self.class_file_path = class_file_path

    def read_u2(self, file):
        return int.from_bytes(file.read(2), byteorder='big')

    def parse_class_file(self):
        methods_info = []
        with open(self.class_file_path, 'rb') as file:
            # Skip the class file header (magic, minor_version, major_version)
            file.seek(8)

            constant_pool_count = self.read_u2(file)
            print("cnt:",constant_pool_count)
            # Skip the constant pool (you can implement parsing it if needed)
            
            constant_pool_tags = [0]  # Initialize with an unsupported tag
            for _ in range(constant_pool_count - 1):
                tag = self.read_u2(file)
                if tag in (1, 7, 8, 19, 20):
                    # These constant pool entries have variable sizes, skip accordingly
                    entry_size = 3 if tag in (7, 8, 19, 20) else 5
                    file.seek(entry_size - 2, 1)
                else:
                    # Other types are not supported, skip and remember the tag
                    file.seek(-2, 1)
                    constant_pool_tags.append(tag)
            
            # Read access flags, this_class, and super_class
            access_flags = self.read_u2(file)
            this_class = self.read_u2(file)
            super_class = self.read_u2(file)

            interfaces_count = self.read_u2(file)
            print("interface cnt:",interfaces_count)
            # Skip the interfaces
            file.seek(2 * interfaces_count, 1)

            fields_count = self.read_u2(file)
            print("fields counts:",fields_count)
            # Skip the fields
            for _ in range(fields_count):
                file.seek(6, 1)

            methods_count = self.read_u2(file)
            print("methods counts:",methods_count)
            # Iterate through methods
            for _ in range(methods_count):
                access_flags = self.read_u2(file)
                name_index = self.read_u2(file)
                descriptor_index = self.read_u2(file)
                attributes_count = self.read_u2(file)
                method_info = {
                    "access_flags": access_flags,
                    "name_index": name_index,
                    "descriptor_index": descriptor_index,
                    "attributes_count": attributes_count,
                }

                # Iterate through method attributes
                for _ in range(attributes_count):
                    attribute_name_index = self.read_u2(file)
                    attribute_length = self.read_u4(file)
                    if attribute_name_index == 3:
                        # This is the "Code" attribute
                        max_stack = self.read_u2(file)
                        max_locals = self.read_u2(file)
                        code_length = self.read_u4(file)
                        code_start_position = file.tell()
                        file.seek(code_length, 1)
                        code_end_position = file.tell()
                        method_info["code_length"] = code_length
                        method_info["code_start_position"] = code_start_position
                        method_info["code_end_position"] = code_end_position
                    else:
                        # Skip other attributes
                        file.seek(attribute_length, 1)

                methods_info.append(method_info)

            # You now have a list of method information including code length and positions
            return methods_info

# Example usage:
parser = JavaClassParser('testSmall.class')
methods_info = parser.parse_class_file()
for method in methods_info:
    print("Method Access Flags:", method["access_flags"])
    print("Method Name Index:", method["name_index"])
    print("Method Descriptor Index:", method["descriptor_index"])
    if "code_length" in method:
        print("Code Length:", method["code_length"])
        print("Code Start Position:", method["code_start_position"])
        print("Code End Position:", method["code_end_position"])
    print()
