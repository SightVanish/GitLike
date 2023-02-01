import os
from . import data

def write_tree(directory='.'):
    entries = []
    with os.scandir(directory) as it:
        for entry in it:
            full_path = os.path.join(directory, entry.name)
            if is_ignored(full_path):
                continue
            if entry.is_file() and not entry.is_symlink():
                objType = 'bolb'
                with open(full_path, 'rb') as f:
                    oid = data.hash_object(f.read())
            elif entry.is_dir() and not entry.is_symlink():
                # recursively scan this directory
                objType = 'tree'
                oid = write_tree(full_path)
            entries.append((entry.name, oid, objType))
    tree = ''.join(f'{objType} {oid} {name}\n' for name, oid, objType in sorted(entries))
    return data.hash_object(tree.encode(), objType)
    
def is_ignored(path):
    # ignore '.ugit' directory
    return '.ugit' in path.split('/')

