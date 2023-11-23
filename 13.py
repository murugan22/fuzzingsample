import struct

def read_class_file(file_path):
    method_info_list = []

    with open(file_path, 'rb') as file:
        # Read the class file structure
        magic, minor_version, major_version = struct.unpack('>IHH', file.read(8))
        constant_pool_count = struct.unpack('>H', file.read(2))[0]

        # Read the constant pool
        constant_pool = [None]  # Index 0 is reserved
        for i in range(1, constant_pool_count):
            tag = struct.unpack('B', file.read(1))[0]
            if tag == 1:  # CONSTANT_Utf8
                length = struct.unpack('>H', file.read(2))[0]
                value = file.read(length)
                constant_pool.append(value)
            elif tag in (7, 8):  # CONSTANT_Class, CONSTANT_String
                file.read(2)
            else:
                file.read(4)

        access_flags, this_class, super_class, interfaces_count = struct.unpack('>HHHH', file.read(8))

        # Read the interfaces
        interfaces = struct.unpack('>' + 'H' * interfaces_count, file.read(2 * interfaces_count))

        fields_count = struct.unpack('>H', file.read(2))[0]
        # Skip reading fields

        methods_count = struct.unpack('>H', file.read(2))[0]
        print(methods_count)
        # Read method information
        for _ in range(methods_count):
            access_flags, name_index, descriptor_index, attributes_count = struct.unpack('>HHHH', file.read(8))
            method_name = constant_pool[name_index].decode('utf-8')
            method_start = file.tell()  # Start of the method
            method_info = (method_name, method_start, [])

            '''
            # Read attributes for the method
            for _ in range(attributes_count):
                attribute_name_index, attribute_length = struct.unpack('>H', file.read(2)), struct.unpack('>I', file.read(4))[0]
                #attribute_name = constant_pool[attribute_name_index].decode('utf-8')
                attribute_data = file.read(attribute_length)
                method_info[2].append((attribute_name_index, attribute_data))
            '''
            method_info_list.append(method_info)

        last_method_end = file.tell()  # Store the position before closing the file

    # Calculate the end index for each method
    for i in range(len(method_info_list) - 1):
        start = method_info_list[i][1]
        end = method_info_list[i + 1][1]
        method_info_list[i] = (method_info_list[i][0], start, end, method_info_list[i][2])

    # Calculate the end index for the last method using the stored position
    start = method_info_list[-1][1]
    method_info_list[-1] = (method_info_list[-1][0], start, last_method_end, method_info_list[-1][2])

    return method_info_list

# Replace 'YourClassName.class' with the path to your Java class file
class_file_path = './tests.class'
method_info_list = read_class_file(class_file_path)

# Print method names, their start and end indices, and attribute names and data
for method_name, start, end, attributes in method_info_list:
    print(f"Method: {method_name}, Start Index: {start}, End Index: {end}")
    for attribute_name, attribute_data in attributes:
        print(f"  Attribute: {attribute_name}")
        print(f"    Data: {attribute_data.hex()}")
