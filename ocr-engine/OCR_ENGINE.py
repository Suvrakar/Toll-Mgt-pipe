from flask import Flask, request, jsonify, render_template
import os
import pytesseract
from PIL import Image
import requests

app = Flask(__name__)

# OCR function


def perform_ocr(image_path):
    # Use pytesseract to perform OCR on the image
    text = pytesseract.image_to_string(Image.open(image_path))
    return text

# Route to render the HTML form


@app.route('/')
def index():
    return render_template('index.html')

# Route to handle OCR requests


@app.route('/ocr', methods=['POST'])
def ocr():
    try:
        # Check if an image file is present in the request
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400

        image_file = request.files['image']

        # Save the image temporarily
        temp_image_path = 'temp_image.png'
        image_file.save(temp_image_path)

        # Perform OCR on the image
        ocr_result = perform_ocr(temp_image_path)

        print(ocr_result)

        # Send the OCR result to a separate backend server
        # backend_url = 'http://backend-server-url/api/process_ocr'
        backend_url = 'http://localhost:3000/api/process_ocr'
        payload = {'text': ocr_result}

        response = requests.post(backend_url, json=payload)
        response.raise_for_status()

        response_data = response.json()
        return jsonify(response_data)
    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    finally:
        # Clean up the temporary image file
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
