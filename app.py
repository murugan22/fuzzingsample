from flask import Flask, render_template, request, redirect, url_for
import os
import random

app = Flask(__name__)

# Define the directory where uploaded files will be stored
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class TLVParser:
    def __init__(self):
        self.error_codes = []

    def parse_bytecode(self, bytecode):
        try:
            while len(bytecode) > 0:
                tag = bytecode[0]
                bytecode = bytecode[1:]

                if not bytecode:
                    # Error: Incomplete data (missing length and value)
                    self.error_codes.append("Incomplete data")
                    return

                length_bytes = bytecode[:2]
                bytecode = bytecode[2:]
                length = ord(length_bytes[0]) * 256 + ord(length_bytes[1])

                if len(bytecode) < length:
                    # Error: Incomplete data (insufficient value bytes)
                    self.error_codes.append("Incomplete data")
                    return

                value = bytecode[:length]
                bytecode = bytecode[length:]

                # Process the tag, length, and value here

                # Check for missing size
                if length == 0:
                    self.error_codes.append("Missing size")

                # Check for incorrect byte length
                if len(value) != length:
                    self.error_codes.append("Incorrect byte length")

        except Exception as e:
            # Handle other exceptions and set an appropriate error code
            self.error_codes.append("Other error")

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
            # Add more conditions for other error codes as needed

        # Store the generated values in the instance variable
        self.generated_values = generated_values

    def get_generated_values(self):
        return self.generated_values

# Example usage
fuzzer = Fuzzer()
error_codes = ["Incomplete data", "Missing size", "Incorrect byte length"]

# Generate values based on error codes using the Fuzzer
fuzzer.generate_values(error_codes)
generated_values = fuzzer.get_generated_values()

# Print the generated values to the console
print("Generated Values IN fuzzer:")
for value in generated_values:
    print(value)



@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    # If the user submits an empty form, handle it gracefully
    if file.filename == '':
        return redirect(request.url)

    # Save the uploaded file to the upload directory
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # Process the uploaded file using TLVParser
        parser = TLVParser()
        with open(filename, 'rb') as bytecode_file:
            bytecode = bytecode_file.read()
            parser.parse_bytecode(bytecode)
            error_codes = parser.get_error_codes()

        # Generate values based on error codes using the Fuzzer
        fuzzer = Fuzzer()
        fuzzer.generate_values(error_codes)
        generated_values = fuzzer.get_generated_values()

       

    return 'File uploaded successfully!'

if __name__ == '__main__':
    app.run(debug=True)
