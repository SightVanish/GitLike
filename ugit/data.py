import os
import hashlib

GIT_DIR = '.ugit'

def init():
    """
    Init .ugit repository.
    """
    if os.path.exists(GIT_DIR):
        # we do not really reinitialize git repository here
        print('Reinitialized existing Git repository in %s' % os.path.join(os.getcwd(), GIT_DIR))
    else:
        os.makedirs(GIT_DIR)
        os.makedirs(os.path.join(os.getcwd(), GIT_DIR, 'objects'))
        print('Initialized empty ugit repository in %s' % os.path.join(os.getcwd(), GIT_DIR))

def hash_object(data):
    """
    Store object to a file named with its hash value(OID) in bytes.
    """
    oid = hashlib.sha1(data).hexdigest() # hash object and convert to binary presentation
    os.makedirs(os.path.join(os.getcwd(), GIT_DIR, 'objects', oid[:2]))
    with open(os.path.join(os.getcwd(), GIT_DIR, 'objects', oid[:2], oid[2:]), 'wb') as out:
        out.write(data)
    return oid

def get_object(oid):
    """
    Print object value based on its hash value(OID).
    """
    with open(os.path.join(os.getcwd(), GIT_DIR, 'objects', oid[:2], oid[2:]), 'rb') as f:
        return f.read()