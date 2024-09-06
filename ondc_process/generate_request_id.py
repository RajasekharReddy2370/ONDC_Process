import uuid
from cryptography.hazmat.primitives.asymmetric import ed25519
from base64 import b64decode

# Step 1: Generate a Unique Request ID
request_id = str(uuid.uuid4())  # Generates a UUID and converts it to a string
print("Request ID:", request_id)

# Step 2: Decode and Ensure the Private Key is 32 Bytes
signing_private_key_bytes = b64decode("mvXb2Ch8K+UPbfw/SffY9gr+xA0z3+0mticR1o8rczKhkoBgLpNz3mLTh9q8ahTPk3XLqoBrRdzz6BRZKHke5w==")

# Ensure the key is 32 bytes
if len(signing_private_key_bytes) != 32:
    signing_private_key_bytes = signing_private_key_bytes[:32]  # Extract the first 32 bytes

# Load the private key
signing_private_key = ed25519.Ed25519PrivateKey.from_private_bytes(signing_private_key_bytes)

# Step 3: Sign the Request ID
signature = signing_private_key.sign(request_id.encode('utf-8'))

# Convert the signature to a hex string for storage or transmission
signed_unique_req_id = signature.hex()
print("Signed Unique Request ID:", signed_unique_req_id)

# Step 4: Load the Public Key
signing_public_key_base64 = "oZKAYC6Tc95i04favGoUz5N1y6qAa0Xc8+gUWSh5Huc="
signing_public_key_bytes = b64decode(signing_public_key_base64)

# Load the public key
signing_public_key = ed25519.Ed25519PublicKey.from_public_bytes(signing_public_key_bytes)

# Step 5: Verify the Signature using the Public Key
try:
    signing_public_key.verify(signature, request_id.encode('utf-8'))
    print("Signature is valid.")
except Exception as e:
    print("Signature is invalid:", e)
