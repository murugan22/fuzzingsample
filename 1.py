import subprocess
import random
import struct
import os
from pyjvm.CPInfo import CPInfo, CPTag
from pyjvm.FieldInfo import FieldInfo
from pyjvm.AttributeInfo import AttributeInfo
import binascii
from uttlv import TLV
# Whether to print Debug messages or not
DEBUG = True

# Whether to perform backtracking
BACKTRACK = True

# Parameters for the program
NUM_SEQ = 1
MIN_LEN = 1200
MAX_ERR = 30
import io
import jawa
class JavaClassParser:
    
    

    def __init__(self, class_file_path):
        self.class_file_path = class_file_path
        self.num_created = 0
        self.error_codes = []
    
    
    def parse_bytecode(self, bytecode):
        try:
            while len(bytecode) > 0:
                # Extract the next TLV structure
                #print("INITIAL BYTECODE: ")
                #print(bytecode)
                tag = bytecode[0:1]
                #print("TAG: ")
                #print(tag)
                bytecode = bytecode[1:]

                #print("POST TAG BYTECODE: ")
                #print(bytecode)

                if not bytecode:
                    # Error: Incomplete data (missing length and value)
                    self.error_codes.append("Incomplete data")
                    fuzzed_value = bytes(random.getrandbits(8) for _ in range(length))
                    
                    #print(f"Fuzzed Value: {fuzzed_value}")
                    break

                if len(bytecode) < 2:
                    # Error: Incomplete data (missing length bytes)
                    fuzzed_value = bytes(random.getrandbits(8) for _ in range(length))
                    #print(f"Fuzzed Value: {fuzzed_value}")
                    self.error_codes.append("Incomplete data")
                    break

                length_bytes = bytecode[0:2]
                bytecode = bytecode[2:]
                length = length_bytes[0] * 256 + length_bytes[1]

                #print("length bytes ")
                #print((length_bytes))

                #print("Length:")
                #print(length)

                if len(bytecode) < length:
                    # Error: Incorrect byte length (length exceeds available data)
                    self.error_codes.append("Incorrect byte length")
                    #print("Length - " + str(length))
                    fuzzed_value = bytes(random.getrandbits(8) for _ in range(length))
                    #print(f"Fuzzed Value: {fuzzed_value}")
                    break

                if length == 0:
                    # Error: Missing size
                    self.error_codes.append("Missing size")
                    fuzzed_value = bytes(random.getrandbits(8) for _ in range(length))
                    #print(f"Fuzzed Value: {fuzzed_value}")
                    break
                print(length)
                value = bytecode[0:length]
                bytecode = bytecode[length]

                # Process the tag, length, and value here

        except Exception as e:
            # Handle other exceptions and set an appropriate error code
            self.error_codes.append(f"Other error: {str(e)}")

    def get_error_codes(self):
        return self.error_codes

    def read_u1(self, file):
        # Read and return an unsigned 8-bit integer (u1) from the file
        data = file.read(1)
        return int.from_bytes(data, byteorder="big")

    def read_u2(self, file):
        # Read and return an unsigned 16-bit integer (u2) from the file
        # Assuming the data is big-endian
        data = file.read(2)
        return int.from_bytes(data, byteorder="big")

    def read_u4(self, file):
        # Read and return an unsigned 32-bit integer (u4) from the file
        # Assuming the data is big-endian
        data = file.read(4)
        return int.from_bytes(data, byteorder="big")

    def read_cp_info(self, file):
        # Read and return a cp_info structure
        tag = self.read_u1(file)
        if tag == 1:  # CONSTANT_Utf8
            length = self.read_u2(file)
            utf8_bytes = file.read(length)
            return {"tag": tag, "length": length, "bytes": utf8_bytes.decode("utf-8")}
        elif tag == 7:  # CONSTANT_Class
            name_index = self.read_u2(file)
            return {"tag": tag, "name_index": name_index}
        # You'll need to add cases for other tags based on your class file format
        else:
            # Handle other tag types if needed
            return {"tag": tag}

    def parse_fields(self, file):
        fields_count = self.read_u2(file)
        fields = []
        for _ in range(fields_count):
            field_info = {
                'access_flags': self.read_u2(file),
                'name_index': self.read_u2(file),
                'descriptor_index': self.read_u2(file),
                'attributes_count': self.read_u2(file),
                'attributes': self.parse_attributes(file)
            }
            fields.append(field_info)
        return fields

    def parse_methods(self, file):
        methods_count = self.read_u2(file)
        methods = []
        for _ in range(methods_count):
            method_info = {
                'access_flags': self.read_u2(file),
                'name_index': self.read_u2(file),
                'descriptor_index': self.read_u2(file),
                'attributes_count': self.read_u2(file),
                'attributes': self.parse_attributes(file)
            }
            methods.append(method_info)
        return methods

    def parse_attributes(self, file):
        attributes_count = self.read_u2(file)
        attributes = []
        for _ in range(attributes_count):
            attribute_name_index = self.read_u2(file)
            attribute_length = self.read_u4(file)
            info = file.read(attribute_length)
            attribute_info = {
                'attribute_name_index': attribute_name_index,
                'attribute_length': attribute_length,
                'info': info
            }
            attributes.append(attribute_info)
        return attributes

    def parse_class_file(self):
        with open(self.class_file_path, "rb") as file:
            magic = self.read_u4(file)
            minor_version = self.read_u2(file)
            major_version = self.read_u2(file)
            constant_pool_count = self.read_u2(file)
            constant_pool = [self.read_cp_info(file) for _ in range(constant_pool_count - 1)]
            access_flags = self.read_u2(file)
            this_class = self.read_u2(file)
            super_class = self.read_u2(file)
            interfaces_count = self.read_u2(file)
            interfaces = [self.read_u2(file) for _ in range(interfaces_count)]
            fields_count = self.read_u2(file)
            fields = self.parse_fields(file)
            methods_count = self.read_u2(file)
            methods = self.parse_methods(file)
            attributes_count = self.read_u2(file)  # Define attributes_count here
            attributes = self.parse_attributes(file)
        '''
        return {
            "magic": hex(magic),
            "minor_version": minor_version,
            "major_version": major_version,
            "constant_pool_count": constant_pool_count,
            "constant_pool": constant_pool,
            "access_flags": access_flags,
            "this_class": this_class,
            "super_class": super_class,
            "interfaces_count": interfaces_count,
            "interfaces": interfaces,
            "fields_count": fields_count,
            "fields": fields,
            "methods_count": methods_count,
            "methods": methods,
            "attributes_count": attributes_count,
            "attributes": attributes,
        }
        '''
        
        return {
            
            "fields": fields,
            
        }
    

def parse_tlv(data):
    tlv_list = []
    i = 0

    while i < len(data):
        tag = data[i]
        length = int.from_bytes(data[i + 1:i + 3], byteorder="big")
        value = data[i:i + 3 + length]  # Includes tag, length, and value
        tlv_list.append(value)
        i += 3 + length

    return tlv_list
# Example usage
parser = JavaClassParser("test.class")
parsed_class = parser.parse_class_file()
#print(parsed_class)
'''for info in info_values:
    print(info)'''
# Iterate through the object and print the key-value pairs
for key, value in parsed_class.items():
    print('key')
    for info in value:
        #print('info[attributes]')
        info_values = [item['info'] for info in value for item in info['attributes'] if 'info' in item]

        #print(len(info_values))
        if len(info_values)>0:
            bytecodes = info_values
            val = b'abcde2'
            #print(info_values)
            # Extract the first byte string in the list
            byte_string = bytecodes[0]
            print("java:",byte_string)
            # Create a Bytecode instance from the data
            
            # Check if the byte string has at least two bytes
            if len(byte_string) >= 2:
                new_byte_string = byte_string[1:-1]
                t = TLV()
                t.parse_array(new_byte_string)
                itemlen = 0
                itemlen2 = 0
                for key,value in t._items.items():
                    print(value)
                    parser.parse_bytecode(value)
                itemlen2 += 1
                #TLV parser library in python
                print("total tlvs Library:",itemlen2)            
                tlv_list = parse_tlv(new_byte_string)
                for tlv in tlv_list:
                    print(tlv)
                    itemlen += 1
                #native code to parse tlv items
                print("total tlvs:",itemlen)   
                    #print(binascii.hexlify(tlv).decode('utf-8'))
                 #   parser.parse_bytecode(tlv)
                    
                    #error_codes = parser.get_error_codes()
                    #print(error_codes)
            else:
                # Handle the case where the byte string has fewer than two bytes
                print("Byte string is too short to remove first and last characters.")
            error_codes = parser.get_error_codes() 
            print(error_codes)
             #print(f"{key}: {value}")
            # Extract 'info' values
    