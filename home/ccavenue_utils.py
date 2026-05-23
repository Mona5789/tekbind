from Crypto.Cipher import AES
import base64
import hashlib

from Crypto.Cipher import AES
import hashlib
import binascii

BLOCK_SIZE = 16


def pad(data):
    length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + (chr(length) * length)


def unpad(data):
    return data[:-ord(data[-1:])]


def encrypt(plainText, workingKey):
    iv = bytes.fromhex('000102030405060708090a0b0c0d0e0f')

    key = hashlib.md5(workingKey.encode('utf-8')).digest()

    plainText = pad(plainText)

    cipher = AES.new(key, AES.MODE_CBC, iv)

    encrypted = cipher.encrypt(plainText.encode('utf-8'))

    return binascii.hexlify(encrypted).decode('utf-8')


def decrypt(encText, workingKey):
    iv = bytes.fromhex('000102030405060708090a0b0c0d0e0f')

    key = hashlib.md5(workingKey.encode('utf-8')).digest()

    encryptedText = binascii.unhexlify(encText)

    cipher = AES.new(key, AES.MODE_CBC, iv)

    decrypted = cipher.decrypt(encryptedText).decode('utf-8')

    return unpad(decrypted)