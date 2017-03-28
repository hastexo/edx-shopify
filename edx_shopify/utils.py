import hashlib, base64, hmac

def hmac_is_valid(key, msg, hmac_to_verify):
    hash = hmac.new(key, msg, hashlib.sha256)
    hmac_calculated = base64.b64encode(hash.digest())
    return hmac_calculated == hmac_to_verify
