from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class TLVParser:
    def __init__(self):
        self.error_codes = []

    def parse_bytecode(self, bytecode):
        try:
            while len(bytecode) > 0:
                # Extract the next TLV structure
                tag = bytecode[0:1]
                bytecode = bytecode[1:]

                if not bytecode:
                    # Error: Incomplete data (missing length and value)
                    self.error_codes.append("Incomplete data")
                    break

                if len(bytecode) < 2:
                    # Error: Incomplete data (missing length bytes)
                    self.error_codes.append("Incomplete data")
                    break

                length_bytes = bytecode[0:2]
                bytecode = bytecode[2:]
                length = length_bytes[0] * 256 + length_bytes[1]

                if len(bytecode) < length:
                    # Error: Incorrect byte length (length exceeds available data)
                    self.error_codes.append("Incorrect byte length")
                    break

                if length == 0:
                    # Error: Missing size
                    self.error_codes.append("Missing size")
                    break

                value = bytecode[0:length]
                bytecode = bytecode[length]

                # Process the tag, length, and value here

        except Exception as e:
            # Handle other exceptions and set an appropriate error code
            self.error_codes.append(f"Other error: {str(e)}")

    def get_error_codes(self):
        return self.error_codes


def index():
    return render_template('upload.html')

@app.route('/')
@app.route('/test/incomplete')
def test_incomplete():
    # Test data for "Incomplete data"
    test_bytecode = b'\x01\x03'
    
    parser = TLVParser()
    parser.parse_bytecode(test_bytecode)
    error_codes = parser.get_error_codes()

    if error_codes:
        for error_code in error_codes:
            print(f"Error: {error_code}")

    return f'Test data {test_bytecode} parsed for "Incomplete data ".'

@app.route('/test/incorrect_length')
def test_incorrect_length():
    # Test data for "Incorrect byte length"
    test_bytecode = b'\x01\x03\x00\x07\x02\x03\x80\x01\x01\x00\x05\x03\x03\x01\x00'

    parser = TLVParser()
    parser.parse_bytecode(test_bytecode)
    error_codes = parser.get_error_codes()

    if error_codes:
        for error_code in error_codes:
            print(f"Error: {error_code}")

    return f'Test data {test_bytecode} parsed for "Incorrect byte length ".'

@app.route('/test/missing_size')
def test_missing_size():
    # Test data for "Missing size"
    test_bytecode = b'\x01\x00'

    parser = TLVParser()
    parser.parse_bytecode(test_bytecode)
    error_codes = parser.get_error_codes()

    if error_codes:
        for error_code in error_codes:
            print(f"Error: {error_code}")

    return f'Test data {test_bytecode} parsed for "Missing size ".'
    
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        parser = TLVParser()
        with open(filename, 'rb') as bytecode_file:
            bytecodes = bytecode_file.read().splitlines()
            for bytecode in bytecodes:
                parser.parse_bytecode(bytecode)
                error_codes = parser.get_error_codes()

                if error_codes:
                    # Handle errors based on the error codes
                    for error_code in error_codes:
                        print(f"Error: {error_code}")

            # Continue processing or generate values as needed

            # Example: Generate values (modify this as needed)
            generated_values = generate_values(bytecode)  # Replace with your value generation logic

            # Print the generated values
            print("Generated Values:")
            for value in generated_values:
                print(value)

    return 'File uploaded successfully!'

# Example value generation function (replace with your logic)
def generate_values(bytecode):
    # Implement your value generation logic here
    # For testing, you can return a list of sample values
    return ["Value1", "Value2", "Value3"]

if __name__ == '__main__':
    app.run(debug=True)
