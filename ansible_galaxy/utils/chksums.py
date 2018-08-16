import logging

import hashlib

log = logging.getLogger(__name__)


def sha256sum_from_path(filename):
    block_size = 65536
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as fo:
        for block in iter(lambda: fo.read(block_size), b''):
            sha256.update(block)
    return sha256.hexdigest()
