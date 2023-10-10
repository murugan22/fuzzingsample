from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class TLVParser:
    def __init__(self):
        self.error_code = None

    def parse_bytecode(self, bytecode):
        try:
            while len(bytecode) > 0:
                tag = bytecode[0:1]
                bytecode = bytecode[1:]

                if not bytecode:
                    # Error: Incomplete data (missing length and value)
                    self.error_code = "Incomplete data"
                    return

                length_bytes = bytecode[0:2]
                bytecode = bytecode[2:]
                length = length_bytes[0] * 256 + length_bytes[1]

                if len(bytecode) < length:
                    # Error: Incomplete data (insufficient value bytes)
                    self.error_code = "Incomplete data"
                    return

                value = bytecode[0:length]
                bytecode = bytecode[length:]

                # Process the tag, length, and value here

                # Check for missing size
                if length == 0:
                    self.error_code = "Missing size"
                    return

                # Check for incorrect byte length
                if len(value) != length:
                    self.error_code = "Incorrect byte length"
                    return

        except Exception as e:
            # Handle other exceptions and set an appropriate error code
            self.error_code = f"Other error: {str(e)}"

    def get_error_code(self):
        return self.error_code

@app.route('/')
def index():
    return render_template('upload.html')

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
            bytecode = bytecode_file.read()
            parser.parse_bytecode(bytecode)
            error_code = parser.get_error_code()

            if error_code:
                # Handle errors based on the error code
                return f"Error: {error_code}"

            # If no errors, continue processing or generate values as needed

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
    print(self.generated_values)
    def get_generated_values(self):
        return self.generated_values

if __name__ == '__main__':
    app.run(debug=True)
