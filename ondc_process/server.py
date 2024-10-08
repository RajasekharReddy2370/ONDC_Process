import json
import time
import os
import base64
import datetime
import json
from nacl.bindings import crypto_sign_ed25519_sk_to_seed
import nacl.hash
from nacl.signing import SigningKey
from cryptography.hazmat.primitives import serialization
from Cryptodome.Cipher import AES
from Cryptodome.Util.Padding import unpad
from flask import Flask, request, render_template
import requests
import uuid
import multiprocessing
import threading
import pytz

# bapBaseUrl = os.getenv("BAP_BASE_URL")
bppBaseUrl = os.getenv("BPP_BASE_URL")
registry_url = os.getenv("REGISTRY_URL")
app_port = os.getenv("APP_PORT")
static_file_port = os.getenv("STATIC_FILE_PORT")
subscribers = None
subscribers_uniquekey_store = {}

# bapSubscribeBody = {
#     "context": {
#         "operation": {
#             "ops_no": 1
#         },
#     },
#     "message": {
#         "request_id": "",
#         "timestamp": "",
#         "entity": {
#             "gst": {
#                 "legal_entity_name": "...",
#                 "business_address": "...",
#                 "city_code": [
#                     "std:080"
#                 ],
#                 "gst_no": "..."
#             },
#             "pan": {
#                 "name_as_per_pan": "...",
#                 "pan_no": "...",
#                 "date_of_incorporation": "..."
#             },
#             "name_of_authorised_signatory": "...",
#             "email_id": "email@domain.in",
#             "mobile_no": ...,
#             "country": "IND",
#             "subscriber_id": "",
#             "unique_key_id": "",
#             "callback_url": "/",
#             "key_pair": {
#                 "signing_public_key": "",
#                 "encryption_public_key": "",
#                 "valid_from": "",
#                 "valid_until": "2030-06-19T11:57:54.101Z"
#             }
#         },
#         "network_participant": [
#             {
#                 "subscriber_url": "/",
#                 "domain": "ONDC:TRV10",
#                 "type": "buyerApp",
#                 "msn": False,
#                 "city_code": []
#             }
#         ]
#     }
# }

bppSubscribeBody = {
    "context": {
        "operation": {
            "ops_no": 2
        }
    },
    "message": {
        "request_id": "26c7c9af-d405-44da-b33d-98541de5084b",
        "timestamp": "",
        "entity": {
            "gst": {
                "legal_entity_name": "PGR Boom Techno India Private Limited",
                "business_address": "6/82/83 KRISHNA MAHA,YADAVS BAZAR Chilakaluripet Guntur AndhraPradesh India  522606",
                "city_code": [
                    "std:0861"
                ],
                "gst_no": ""
            },
            "pan": {
                "name_as_per_pan": "PGR BOOM TECHNO INDIA PRIVATE LIMITED",
                "pan_no": "AANCP9831C",
                "date_of_incorporation": "07/08/2023"
            },
            "name_of_authorised_signatory": "Gopiraj Chatti",
            "email_id": "info@createmystore.online",
            "mobile_no": 7989572128,
            "country": "IND",
            "subscriber_id": "createmystore.online",
            "unique_key_id": "429a9c6cfef0b15c49d396c51c7a8a408651db693c367503c406fb7c65e1ba639f888e522ec5e253a614514e8c90e059b4a2c2f63476f745acca438b773f4c0b",
            "callback_url": "/",
            "key_pair": {
                "signing_public_key": "oZKAYC6Tc95i04favGoUz5N1y6qAa0Xc8+gUWSh5Huc=",
                "encryption_public_key": "MCowBQYDK2VuAyEAmLhAvCH4OZ9T158wIVh3NV8WY51IjzqyCMe7gKWI8yE=",
                "valid_from": "2024-09-06T11:57:54.101Z",
                "valid_until": "2030-06-19T11:57:54.101Z"
            }
        },
        "network_participant": [
            {
                "subscriber_url": "https://ondc.createmystore.online/api",
                "domain": "nic2004:52110",
                "type": "sellerApp",
                "msn": False,
                "city_code": ["std:0861"]
            }
        ]
    }
}


def sign(signing_key, private_key):
    private_key64 = base64.b64decode(private_key)
    seed = crypto_sign_ed25519_sk_to_seed(private_key64)
    signer = SigningKey(seed)
    signed = signer.sign(bytes(signing_key, encoding='utf8'))
    signature = base64.b64encode(signed.signature).decode()
    return signature


def decrypt(enc_public_key, enc_private_key, cipherstring):
    private_key = serialization.load_der_private_key(
        base64.b64decode(enc_private_key),
        password=None
    )
    public_key = serialization.load_der_public_key(
        base64.b64decode(enc_public_key)
    )
    shared_key = private_key.exchange(public_key)
    cipher = AES.new(shared_key, AES.MODE_ECB)
    ciphertxt = base64.b64decode(cipherstring)
    return unpad(cipher.decrypt(ciphertxt), AES.block_size).decode('utf-8')


def createHtml(subscriber, subscriber_id):
    signature = sign(subscriber['requestId'], subscriber['signingPrivateKey'])
    htmlFile = f'''
    <html>
        <head>
            <meta name= "ondc-site-verification" content="{signature}" />
        </head>
        <body>
            ONDC Site Verification Page
        </body>
    </html>
    '''
    # if subscriber['type'] == "BAP":
    #     if not os.path.exists(f'templates/{subscriber_id[slice(len(bapBaseUrl) + 1, len(subscriber_id))]}'):
    #         os.makedirs(
    #             f'templates/{subscriber_id[slice(len(bapBaseUrl) + 1, len(subscriber_id))]}')
    #     with open(f"templates/{subscriber_id[slice(len(bapBaseUrl) + 1, len(subscriber_id))]}/ondc-site-verification.html", "w+") as file:
    #         file.write(htmlFile)
    if subscriber['type'] == "BPP":
        if not os.path.exists(f'templates/{subscriber_id[slice(len(bppBaseUrl) + 1, len(subscriber_id))]}'):
            os.makedirs(
                f'templates/{subscriber_id[slice(len(bppBaseUrl) + 1, len(subscriber_id))]}')
        with open(f"templates/{subscriber_id[slice(len(bppBaseUrl) + 1, len(subscriber_id))]}/ondc-site-verification.html", "w+") as file:
            file.write(htmlFile)


app = Flask(__name__)


@app.route('/on_subscribe', methods=['POST'])
def onsubscribe():
    data = request.get_json()
    print(f"/on_subscribe called :: Request -> {data}")
    subscriber_id = data['subscriber_id']
    unique_key_id = subscribers_uniquekey_store[subscriber_id]
    subscriber = subscribers[f"{subscriber_id} | {unique_key_id}"]
    print(subscriber)
    return {
        "answer": decrypt(subscriber['ondcPublicKey'], subscriber['encPrivateKey'], data['challenge'])
    }


def serve_file():
    os.system(
        f'python -m http.server {static_file_port} --directory ondc-verification')


def subscribe_helper():
    if subscribers != None:
        global subscribers_uniquekey_store
        for subscriber_uk_id, subscriber in subscribers.items():
            [subscriber_id, unique_key_id] = subscriber_uk_id.split(' | ')
            subscribers_uniquekey_store[subscriber_id] = unique_key_id
            request_id = str(uuid.uuid4())
            subscribers[subscriber_uk_id]['requestId'] = request_id
            createHtml(subscriber, subscriber_id)
        process = multiprocessing.Process(target=serve_file)
        process.start()
        time.sleep(5)
        for subscriber_uk_id, subscriber in subscribers.items():
            [subscriber_id, unique_key_id] = subscriber_uk_id.split(' | ')
            request_id = subscriber['requestId']
            current_datetime = datetime.datetime.now().astimezone(pytz.timezone('Asia/Kolkata'))
            current_datetime_iso8601 = current_datetime.strftime(
                "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

            # if subscriber['type'] == 'BAP':
            #     bapSubscribeBody['message']['request_id'] = request_id
            #     bapSubscribeBody['message']['timestamp'] = current_datetime_iso8601
            #     bapSubscribeBody['message']['entity']['subscriber_id'] = subscriber_id
            #     bapSubscribeBody['message']['entity']['unique_key_id'] = unique_key_id
            #     bapSubscribeBody['message']['entity']['key_pair']['signing_public_key'] = subscriber['signingPublicKey']
            #     bapSubscribeBody['message']['entity']['key_pair']['encryption_public_key'] = subscriber['encPublicKey']
            #     bapSubscribeBody['message']['entity']['key_pair']['valid_from'] = current_datetime_iso8601
            #     bapSubscribeBody['message']['network_participant'][0]['city_code'] = [
            #         subscriber['city']]
            #
            #     print(json.dumps(bapSubscribeBody))
            #
            #     response = requests.post(registry_url, json=bapSubscribeBody)
            #     if response.status_code == 200:
            #         print(
            #             f"/subscribe for {subscriber_uk_id} request successful :: {response.json()}")
            #     else:
            #         print(
            #             f"/subscribe for {subscriber_uk_id} request failed :: {response.json()}")
            if subscriber['type'] == 'BPP':
                bppSubscribeBody['message']['request_id'] = request_id
                bppSubscribeBody['message']['timestamp'] = current_datetime_iso8601
                bppSubscribeBody['message']['entity']['subscriber_id'] = subscriber_id
                bppSubscribeBody['message']['entity']['unique_key_id'] = unique_key_id
                bppSubscribeBody['message']['entity']['key_pair']['signing_public_key'] = subscriber['signingPublicKey']
                bppSubscribeBody['message']['entity']['key_pair']['encryption_public_key'] = subscriber['encPublicKey']
                bppSubscribeBody['message']['entity']['key_pair']['valid_from'] = current_datetime_iso8601
                bppSubscribeBody['message']['network_participant'][0]['city_code'] = [
                    subscriber['city']]

                print(json.dumps(bppSubscribeBody))

                response = requests.post(registry_url, json=bppSubscribeBody)
                if response.status_code == 200:
                    print(
                        f"/subscribe for {subscriber_uk_id} request successful :: {response.json()}")
                else:
                    print(
                        f"/subscribe for {subscriber_uk_id} request failed :: {response.json()}")
        time.sleep(300)
        process.terminate()
        process.join()


@app.route('/subscribe', methods=['POST'])
def subscribe():
    global subscribers
    subscribers = request.get_json()
    print(f"/subscribe called :: Request -> {subscribers}")
    thread1 = threading.Thread(target=subscribe_helper)
    thread1.start()
    return {"success": "ACK"}


@app.route('/ondc-site-verification.html', methods=['GET'])
def verify_html():
    return render_template('ondc-site-verification.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
# def start_flask_app():
#     app.run(port=app_port, host="0.0.0.0")
#
#
# if __name__ == '__main__':
#     start_flask_app()

# from flask import Flask, request, jsonify
#
# app = Flask(__name__)
#
# @app.route('/ondc_subscribe', methods=['POST'])
# def onsubscribe():
#     data = request.get_json()
#     print(f"/ondc_subscribe called :: Request -> {data}")
#     return jsonify({"message": "Received"}), 200
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8080)
