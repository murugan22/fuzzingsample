import struct

class CPInfo:
    def __init__(self):
        self.tag = 0  # u1
        self.info = None  # Variable length data

    def from_reader(self, reader):
        self.tag = struct.unpack('!B', reader.read(1))[0]
        if self.tag in {10}:  # UTF8, Class, String
            length = struct.unpack('!H', reader.read(2))[0]
            self.info = reader.read(length)
            print("sire:",self.info)
        # Add more cases for other tag values

# Open the class file in binary mode
with open('./tests.class', 'rb') as f:
    # Skip the class file header and other metadata
    f.seek(8)

    constant_pool_count = struct.unpack('!H', f.read(2))[0]

    constant_pool = [None]  # CP index is 1-based
    for i in range(1, constant_pool_count):
        cp_info = CPInfo()
        cp_info.from_reader(f)
        constant_pool.append(cp_info)
        #print(cp_info.tag)
# Now, you have the constant pool entries in the 'constant_pool' list.
