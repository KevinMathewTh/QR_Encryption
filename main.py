import base64
import hashlib
import qrcode
from PIL import Image
from AES import AESCipher

class AES_Object(object):
    def __init__(self, aes_key,filename):
        self.aes_key = aes_key
        self.filename= filename

    def return_aes_encrypt(self):
        ac = AESCipher(self.aes_key)
        encode_string = encodetheimage(self.filename)
        aes_encrypt = ac.encrypt(encode_string)
        return aes_encrypt

def encodetheimage(filename):
    with open(filename, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
        encoded_string = encoded_string.decode("utf-8")
        return encoded_string








