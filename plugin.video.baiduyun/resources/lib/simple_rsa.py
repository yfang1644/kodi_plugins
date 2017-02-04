#!/usr/bin/python
# -*- coding: utf-8 -*-
import random
from binascii import b2a_base64, b2a_hex, a2b_hex


def bytes_to_long(s):
    return long(b2a_hex(s), 16)


def long_to_bytes(l):
    hexstr = '%x' % l
    if len(hexstr) % 2:
        hexstr = '0' + hexstr
    return a2b_hex(hexstr)


def get_public_key(cert):
    from x509_pem import parse
    cert_dict = parse(cert)

    return cert_dict['modulus'], cert_dict['publicExponent']


def create_rsa_from_cert(cert):
    n, e = get_public_key(cert)
    return RSA(n, e)


class RSA:

    def __init__(self, n, e, d=None):
        self._n = n
        self._e = e
        self._d = d
        self._key_bytes = -(-len('%x' % n) // 2)

    def _encrypt(self, msg, k=None):
        assert msg < self._n, 'msg too large'

        return pow(msg, k or self._e, self._n)

    def encrypt(self, msg):
        assert len(msg) <= self._key_bytes - 11, 'msg text too long'

        random_str = ''.join(chr(random.randrange(256))
                             for i in xrange(self._key_bytes - len(msg) - 3))
        newmsg = '\x00\x02' + random_str + '\x00' + msg

        c = self._encrypt(bytes_to_long(newmsg))

        return b2a_base64(long_to_bytes(c))
