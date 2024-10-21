import uuid
import base64

# Function to convert UUID to Base64 (removing padding)
def uuid_to_base64(u):
    # Convert UUID to bytes
    u_bytes = u.bytes
    # Encode the bytes to Base64, then decode to string and strip padding
    return base64.urlsafe_b64encode(u_bytes).decode('utf-8').rstrip('=')

# Function to convert Base64 back to UUID
def base64_to_uuid(b64_str):
    # Add padding back
    b64_str += '=' * (4 - len(b64_str) % 4)
    # Decode Base64 to bytes
    u_bytes = base64.urlsafe_b64decode(b64_str)
    # Convert bytes back to UUID
    return uuid.UUID(bytes=u_bytes)