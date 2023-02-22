import os
import itertools
import operator
from collections import deque, namedtuple
import string
from . import data

Commit = namedtuple('Commit', ['tree', 'parent', 'message']) # tree = Commit.tree

def init():
    """
    Set HEAD point to master
    """
    data.init()
    data.update_ref('HEAD', data.RefValue(symbolic=True, value='refs/heads/master'), deref=True)

def write_tree(directory='.'):
    """
    Scan and hash each file in directory; hash the directory and all subdirectories to ugit objects.
    """
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
    """
    Iterate each line in tree object
    """
    if not oid: # if oid is empty, return
        return
    tree = data.get_object(oid, 'tree')
    for entry in tree.decode().splitlines():
        obj_type, oid, name = entry.split(' ', 2)
        yield obj_type, oid, name
    
def get_tree(oid, base_path=''):
    """
    Retrive all oids and return {path: <oid of a file>}
    """
    result = {}
    for obj_type, oid, name in _iter_tree_entries(oid):
        if ('/' in name) or (name in ('..', '.') ):
            raise ValueError(f'path name is illegal: "{name}"')
        full_path = os.path.join(base_path, name)
        if obj_type == 'blob':
            result[full_path] = oid
        elif obj_type == 'tree':
            result.update(get_tree(oid, full_path))
        else:
            raise ValueError(f'object type is illegal: "{obj_type}"')
    return result
 
def _empty_current_directory():
    """
    Delete all files uder current directory.
    """
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
    """
    Retrive working directory committed in tree_oid
    Note: read_tree will lose all uncommitted changes
    """
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path='./').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data.get_object(oid))

def is_ignored(path):
    """
    Return True if the path should be ignored. (ignore '.ugit' by default)
    """
    # ignore '.ugit' directory
    return '.ugit' in path.split('/')

def commit(message):
    """
    Save current working directory and record parent of this commit.
    """
    commit = 'tree {0}\n'.format(write_tree())
    HEAD = data.get_ref('HEAD', deref=True).value
    if HEAD: # if this is not the first commit
        commit += 'parent {0}\n'.format(HEAD)
    commit += '\n{0}\n'.format(message)
    oid = data.hash_object(commit.encode(), 'commit')
    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid), deref=True)
    return oid

def get_commit(oid):
    """
    Read commit information
    """
    parent = None
    commit = data.get_object(oid, 'commit').decode()
    lines = iter(commit.splitlines())
    for line in itertools.takewhile(operator.truth, lines): # iter until the blank line
        key, value = line.split(' ', 1) # split once via ' '
        if key == 'tree':
            tree = value
        elif key == 'parent':
                parent = value
        else:
            raise ValueError("Unknown field {0}".format(key))
    message = '\n'.join(lines)
    return Commit(tree=tree, parent=parent, message=message)
        
def checkout(name):
    """
    Retrive the working directory of this commit
    """
    oid = get_oid(name)
    commit = get_commit(oid)
    read_tree(commit.tree)
    if is_branch(name):
        HEAD = data.RefValue(symbolic=True, value=f'refs/heads/{name}')
    else:
        HEAD = data.RefValue(symbolic=False, value=oid)
        print('Note: switching to "{0}".'.format(name))
        print('You are in "detached HEAD" state.')
    data.update_ref('HEAD', HEAD, deref=False)

def is_branch(branch):
    return data.get_ref(f'refs/heads/{branch}').value is not None

def create_tag(name, oid):
    """
    Create a tag in .ugit/tags/ as an alias to oid
    """
    data.update_ref(f'refs/tags/{name}', data.RefValue(symbolic=False, value=oid))

def create_branch(name, oid):
    """
    Create a branch in .ugit/refs/heads/
    """
    data.update_ref(f'refs/heads/{name}', data.RefValue(symbolic=False, value=oid))

def get_branch_name():
    """
    Return branch name
    """
    HEAD = data.get_ref('HEAD', deref=False)
    if HEAD.symbolic:
        return os.path.relpath(HEAD.value, 'refs/heads')
    else:
        # detached HEAD
        return None

def iter_branch_names():
    """
    Iterate all branches
    """
    for refname, _ in data.iter_refs(prefix='refs/heads'):
        yield os.path.relpath(refname, 'refs/heads/')

def get_oid(name):
    """
    Return oid with tag=name. If name='@', treat it as 'HEAD'
    """
    if name == '@': name = 'HEAD' # make '@' an alias for 'HEAD'
    # if name is ref
    refs_to_try = [
        f'{name}',
        f'refs/{name}',
        f'refs/tags/{name}',
        f'refs/heads/{name}'
    ] # we support searching different ref subdirectories
    for ref in refs_to_try:
        if data.get_ref(ref, deref=False).value:
            return data.get_ref(ref, deref=True).value
    
    # is ref is sha1
    is_hex = all(c in string.hexdigits for c in name)
    if len(name) == 40 and is_hex:
        return name
    raise ValueError("Unknown name: ".format(name))

def iter_commits_and_parents(oids):
    """
    Iterate all commits in this branch
    """
    oids = deque(oids)
    visited = set() # we only yield an OID once even if it's reached twice
    while oids:
        oid = oids.popleft()
        if not oid or oid in visited:
            continue
        visited.add(oid)
        yield oid
        commit = get_commit(oid)
        # return parent next
        oids.appendleft(commit.parent)

def reset(oid):
    """
    Move HEAD and branch to chosen commit
    """
    data.update_ref('HEAD', data.RefValue(symbolic=False, value=oid), deref=True)
