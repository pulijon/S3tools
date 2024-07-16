from util import logcfg
import logging
import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from base64 import urlsafe_b64encode, urlsafe_b64decode
import os

CRYPT_EXTENSION = "s3c"

class S3Crypt():
        
    def __init__(self, env_key):
        if not env_key in os.environ:
            raise ValueError(f"{env_key} not in environment")
        self.password = os.environ[env_key].encode()
        self.backend = default_backend
        
        
    def generate_key(self, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend()
        )
        return kdf.derive(self.password)

    def encrypt_file(self, fname, output_fname):
        salt = os.urandom(16)
        key = self.generate_key(salt)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=self.backend())
        encryptor = cipher.encryptor()

        with open(fname, 'rb') as f:
            plaintext = f.read()

        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        with open(output_fname, 'wb') as f:
            f.write(salt + iv + ciphertext)

    def decrypt_file(self, fname , output_fname):
        with open(fname, 'rb') as f:
            salt = f.read(16)
            iv = f.read(16)
            ciphertext = f.read()

        key = self.generate_key(salt)
        cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=self.backend())
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        with open(output_fname, 'wb') as f:
            f.write(plaintext)

def main():
    pass

if __name__ == "__main__":
    logcfg(__file__)

    stime = datetime.datetime.now()
    main()
    etime = datetime.datetime.now()
    logging.info(f"Ejecución del programa ha tardado {etime - stime}")
    exit(0)


