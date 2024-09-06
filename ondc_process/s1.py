from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/ondc_subscribe', methods=['POST'])
def onsubscribe():
    data = request.get_json()
    print(f"/ondc_subscribe called :: Request -> {data}")
    return jsonify({"message": "Received"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
