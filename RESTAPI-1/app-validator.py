from flask import Flask, request, jsonify, send_file
import os
import xmltodict

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# Function to check if an XML file already exists
def xml_file_exists():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return next((file for file in files if file.endswith('.xml')), None)


# Function to parse XML content with xmltodict
def parse_xml(file_content):
    try:
        return xmltodict.parse(file_content)
    except Exception as e:
        raise ValueError(f"Error parsing XML: {e}")


# Function to extract AdminContractId elements from parsed XML using xmltodict
def extract_admin_contract_ids(xml_data):
    admin_contract_ids = []
    for item in xml_data.get('soapenv:Body', {}).get('port:searchPerson', {}).get('TCRMPersonSearchBObj', []):
        if isinstance(item, dict) and 'AdminContractId' in item:
            admin_contract_ids.append(item['AdminContractId'])
    return {"AdminContractIds": admin_contract_ids}


# Endpoint to handle XML file upload
@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    files = request.files.getlist('file')
    if len(files) > 1:
        return jsonify({"error": "Only one file can be uploaded at a time"}), 400

    file = files[0]
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.xml'):
        # Check if an XML file already exists
        if xml_file_exists():
            return jsonify({"error": "Only one file can be uploaded. A file already exists."}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        return jsonify({"message": "File successfully uploaded"}), 200
    else:
        return jsonify({"error": "Only XML files are allowed"}), 400


# Endpoint to get the uploaded XML file and extract AdminContractId elements
@app.route('/api/get_xml', methods=['GET'])
def get_xml():
    xml_file = xml_file_exists()
    if not xml_file:
        return jsonify({"error": "No XML file uploaded"}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], xml_file)

    try:
        # Read the XML file content
        with open(file_path, 'r') as file:
            file_content = file.read()

        # Parse XML content
        xml_data = parse_xml(file_content)
        # Extract AdminContractId elements
        admin_contract_ids = extract_admin_contract_ids(xml_data)

        # Return the XML file itself
        response = send_file(file_path, mimetype='application/xml')
        # Add extracted AdminContractIds as additional data
        response_data = {
            "AdminContractIds": admin_contract_ids["AdminContractIds"]
        }
        response_data.update({"file_url": request.url})

        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5001, debug=True)
