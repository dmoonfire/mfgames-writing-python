"""Top-level module for writing utilities."""


import hashlib


DOCBOOK_NAMESPACE = "xmlns='http://docbook.org/ns/docbook'"
MFGAMES_NAMESPACE = "xmlns:mw='urn:mfgames:writing:docbook,0'"


def get_file_hash(filename, block_size = 2**20):
    """Retrieves the SHA-256 hash of the given filename."""
    
    stream = open(filename, 'r')
    file_hash = hashlib.sha256()
    
    while True:
        data = stream.read(block_size)
        
        if not data:
            break
        
        file_hash.update(data)
        
    stream.close()
        
    return file_hash.hexdigest()
    
