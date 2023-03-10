import os
import hashlib
from collections import namedtuple

GIT_DIR = '.ugit'

RefValue = namedtuple('RefValue', ['symbolic', 'value'])

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

def update_ref(ref, value, deref=True):
    """
    Create or update a ref in .ugit/<ref>
    """
    # dereference ref if ref is a symbolic ref, we only update the real ref 
    ref = _get_ref_internal(ref, deref)[0] 
    if not value.value:
        raise TypeError('RefValue is empty: "{0}"'.format(value))
    if value.symbolic:
        # set value of a symbolic ref as 'ref: <pointed ref>'
        value = 'ref: {0}'.format(value.value)
    else:
        value = value.value

    ref_path = os.path.join(GIT_DIR, ref)
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(value)

def get_ref(ref, deref=True):
    """
    Read file content in .ugit/<ref>
    """
    return _get_ref_internal(ref, deref)[1]

def delete_ref(ref, deref=True):
    """
    Remove an existing ref
    """
    ref = _get_ref_internal(ref, deref)[0]
    os.remove(os.path.join(GIT_DIR, ref))

def _get_ref_internal(ref, deref):
    """
    If input is a symbolic ref, return the last ref pointed by it
    """
    ref_path = os.path.join(GIT_DIR, ref)
    if os.path.isfile(ref_path):
        with open(ref_path) as f:
            value = f.read().strip()
    else:
        value = None
    symbolic = bool(value) and value.startswith('ref:')
    if symbolic:
        # if this ref is a symbolic ref, dereference it recursively
        value = value.split(':', 1)[1].strip()
        if deref:
            return _get_ref_internal(value, deref=True)
    # return ref name, ref value
    return ref, RefValue(symbolic=symbolic, value=value)

def iter_refs(prefix='', deref=True):
    """
    Iterate all refs in .ugit/refs and 'HEAD'
    """
    refs = ['HEAD', 'Merged_HEAD']
    for root, _, file_names in os.walk(os.path.join(GIT_DIR, 'refs')):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(os.path.join(root, name) for name in file_names)
    for ref_name in refs:
        # only return refs starting with prefix
        if ref_name.startswith(prefix):
            ref = get_ref(ref_name, deref=deref)
            if ref.value:
                yield ref_name, ref

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
