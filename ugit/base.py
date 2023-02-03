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
                obj_type = 'blob'
                with open(full_path, 'rb') as f:
                    oid = data.hash_object(f.read())
            elif entry.is_dir() and not entry.is_symlink():
                # recursively scan this directory
                obj_type = 'tree'
                oid = write_tree(full_path)
            entries.append((entry.name, oid, obj_type))
    tree = ''.join(f'{obj_type} {oid} {name}\n' for name, oid, obj_type in sorted(entries))
    return data.hash_object(tree.encode(), 'tree')

def _iter_tree_entries(oid):
    if oid is None:
        return
    tree = data.get_object(oid, 'tree')
    for entry in tree.decode().splitlines():
        obj_type, oid, name = entry.split(' ', 2)
        yield obj_type, oid, name
    
def get_tree(oid, base_path=''):
    result = {}
    for obj_type, oid, name in _iter_tree_entries(oid):
        if ('/' in name) or (name in ('..', '.') ):
            raise ValueError(f"path name is illegal: '{name}'")
        full_path = os.path.join(base_path, name)
        if obj_type == 'blob':
            result[full_path] = oid
        elif obj_type == 'tree':
            result.update(get_tree(oid, full_path))
        else:
            raise ValueError(f"object type is illegal: '{obj_type}'")
    return result
 
def _empty_current_directory():
    for root, dirnames, filenames in os.walk('.', topdown=False):
        for filename in filenames:
            path = os.path.relpath(os.path.join(root, filename))
            if is_ignored(path) or not os.path.isfile(path):
                continue
            os.remove(path)
        for dirname in dirnames:
            path = os.path.relpath(os.path.join(root, dirname))
            if is_ignored(path):
                continue
            if len(os.listdir(path)) == 0:
                # do not delete if the directory contains ignored files
                os.rmdir(path)

def read_tree(tree_oid):
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path='./').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data.get_object(oid))

def is_ignored(path):
    # ignore '.ugit' directory
    return '.ugit' in path.split('/')

def commit(message):
    commit = 'tree {0}\nparent {1}\n\n{2}\n'.format(write_tree(), data.get_HEAD(), message)
    oid = data.hash_object(commit.encode(), 'commit')
    data.set_HEAD(oid)
    return oid