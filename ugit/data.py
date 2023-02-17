import os
import hashlib

GIT_DIR = '.ugit'

def init():
    """
    Init .ugit repository
    """
    if os.path.exists(GIT_DIR):
        # we do not really reinitialize git repository here
        print('Reinitialized existing Git repository in %s' % os.path.join(os.getcwd(), GIT_DIR))
    else:
        os.makedirs(GIT_DIR)
        os.makedirs(os.path.join(os.getcwd(), GIT_DIR, 'objects'))
        print('Initialized empty ugit repository in %s' % os.path.join(os.getcwd(), GIT_DIR))

def update_ref(ref, oid):
    """
    Write oid to a file in .ugit/<ref>
    """
    ref_path = os.path.join(GIT_DIR, ref)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(oid)

def get_ref(ref):
    """
    Read file content in .ugit/<ref>
    """
    ref_path = os.path.join(GIT_DIR, ref)
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            return f.read().strip()

def iter_refs():
    """
    Iterate all refs in .ugit/refs and 'HEAD'
    """
    refs = ['HEAD']
    for root, _, file_names in os.walk(os.path.join(GIT_DIR, 'refs')):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(os.path.join(root, name) for name in file_names)
    for ref_name in refs:
        yield ref_name, get_ref(ref_name)

def hash_object(data, type='blob'):
    """
    Store object to a file named with its hash value(OID) in bytes
    Parameters: type: 'blob': the default type, just a collections of bytes without any semantic meaning
    """
    obj = type.encode() + b'\x00' + data # type + null byte + data
    oid = hashlib.sha1(data).hexdigest() # hash object and convert to binary presentation
    # store the object to the folder named with the top two characters of its hash value
    dirs = os.path.join(os.getcwd(), GIT_DIR, 'objects', oid[:2])
    os.makedirs(dirs, exist_ok=True)
    with open(os.path.join(dirs, oid[2:]), 'wb') as out:
        out.write(obj)
    return oid

def get_object(oid, expected='blob'):
    """
    Print object content named by its hash value(OID)
    Parameters: oid: hash value of object; expected: expected object type
    """
    with open(os.path.join(os.getcwd(), GIT_DIR, 'objects', oid[:2], oid[2:]), 'rb') as f:
        obj = f.read()
    obj_type, _, content = obj.partition(b'\x00') # separate via a null byte
    obj_type = obj_type.decode()
    
    if expected is not None and obj_type != expected:
        raise ValueError("object type is {0}, expected {1}".format(obj_type, expected))
    return content
