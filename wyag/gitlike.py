import argparse
import collections
import configparser
import hashlib
from math import ceil
import os
import re
import sys
import zlib
import abc

class GitRepository(object):
    """
    Git repository.
    """
    def __init__(self, path, force=False):
        """
        force: create git path even if it already exists
        """
        self.worktree = path # this is your working path
        self.gitdir = os.path.join(path, ".gitlike") # this is your ".git" path

        # check path
        if not (force or os.path.isdir(self.gitdir)):
            raise Exception("Not a Git repository %s" % os.path.realpath(path))
        
        # read configuration in .git/config
        self.conf = configparser.ConfigParser()
        cf = repo_file(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception("Unsupported repositoryformatversion %s" % vers)

class GitObject():
    repo = None
    def __init__(self, repo, data=None):
        self.repo = repo
        if data != None:
            self.deserialize(data)
    @abc.abstractclassmethod
    def serialize(self):
        """Read self.data and convert it to meaningful representation."""
        raise Exception("Unimplemented!")
    @abc.abstractclassmethod
    def deserialize(self):
        raise Exception("Unimplemented!") 

class GitBlob(GitObject):
    """Blobs are user content: every file put in git is stored as blob."""
    fmt = b'blob'
    def serialize(self):
        return self.blobdata
    def deserialize(self, data):
        self.blobdata = data

argparser = argparse.ArgumentParser()
argsubparsers = argparser.add_subparsers(title='Commands', dest='command')
argsubparsers.required = True
# init
argsp = argsubparsers.add_parser("init", help="Initialize a new, empty repository")
argsp.add_argument("path",
                    metavar="directory",
                    nargs="?",
                    default="./",
                    help="Path to create the repository")
# cat-file
argsp = argsubparsers.add_parser("cat-file", help="Provide content of repository objects")
argsp.add_argument("type",
                    metavar="type",
                    choices=["blob", "commit", "tag", "tree"],
                    help="Specify the type")
argsp.add_argument("object",
                    metavar="object",
                    help="The object to display")

def main(args = sys.argv[1:]):
    args = argparser.parse_args(args)
    if   args.command == "init"       : cmd_init(args)
    elif args.command == "add"        : cmd_add(args)
    elif args.command == "commit"     : cmd_commit(args)
    elif args.command == "merge"      : cmd_merge(args)
    elif args.command == "cat-file"   : cmd_cat_file(args)
    elif args.command == "checkout"   : cmd_checkout(args)
    elif args.command == "hash-object": cmd_hash_object(args)
    elif args.command == "log"        : cmd_log(args)
    elif args.command == "ls-files"   : cmd_ls_files(args)
    elif args.command == "ls-tree"    : cmd_ls_tree(args)
    elif args.command == "rebase"     : cmd_rebase(args)
    elif args.command == "rev-parse"  : cmd_rev_parse(args)
    elif args.command == "rm"         : cmd_rm(args)
    elif args.command == "show-ref"   : cmd_show_ref(args)
    elif args.command == "tag"        : cmd_tag(args)


            
def cmd_init(args):
    repo_create(args.path)
def cmd_add():
    pass
def cmd_commit():
    pass
def cmd_merge():
    pass
def cmd_cat_file(args):
    repo = repo_find()
    obj = object_read(repo, object_find(repo, args.obj, fmt=args.type.encode()))
    sys.stdout.buffer.write(obj.serialize)
def cmd_checkout():
    pass
def cmd_hash_object():
    pass
def cmd_log():
    pass
def cmd_ls_files():
    pass
def cmd_ls_tree():
    pass
def cmd_rebase():
    pass
def cmd_rev_parse():
    pass
def cmd_rm():
    pass
def cmd_show_ref():
    pass
def cmd_tag():
    pass

def repo_path(repo: GitRepository, *path):
    """Compute path under repo's gitdir."""
    return os.path.join(repo.gitdir, *path)
def repo_file(repo: GitRepository, *path, mkdir=False):
    """Compute path under repo's gitdir and create "./.git/path[:-1]" if absent."""
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)
def repo_dir(repo: GitRepository, *path, mkdir=False):
    """Compute path under repo's gitdir and create *path if absent and mkdir"""
    path = repo_path(repo, *path)
    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise Exception("Not a directory %s" % os.path.realpath(path))
    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None

def repo_create(path):
    """Create a new repository"""
    repo = GitRepository(path, True)
    # make sure the path does not exist or is empty
    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception("%s is not a directory!" % os.path.realpath(path))
        if os.listdir(repo.worktree):
            raise Exception("%s is not empty" % os.path.realpath(path))
    else:
        os.makedirs(repo.worktree)
    print("Initialized empty Git repository in %s/" %os.path.realpath(repo.gitdir))
    assert(repo_dir(repo, "branches", mkdir=True))
    assert(repo_dir(repo, "objects", mkdir=True))
    assert(repo_dir(repo, "refs", "tags", mkdir=True))
    assert(repo_dir(repo, "refs", "heads", mkdir=True))

    #./gitlike/description
    with open(repo_file(repo, "description"), 'w') as f:
        f.write("Unnamed repository; edit this file 'description' to name this repository.\n")
    # ./gitlike/HEAD
    with open(repo_file(repo, "HEAD"), 'w') as f:
        f.write("ref: refs/heads/master\n")
    return repo
def repo_default_config():
    """
    repositoryformatversion: 0--initial version, 1--with extensions
    filemode: track the change of file mode
    bare: indicate that this repository has a work tree or not
    """
    ret = configparser.ConfigParser()
    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")
    return ret
def repo_find(path=".", required=True):
    """Find the root of current repository."""
    path = os.path.realpath(path)
    if os.path.isdir(os.path.join(path, ".gitlike")):
        return GitRepository(path)
    # if this is not current repository, recurse in parent
    parent = os.path.realpath(os.path.join(path, ".."))
    if parent == path:
        # bottom case
        if required:
            raise Exception("Not git directory")
        else:
            return None

    return repo_find(parent, required)

def object_read(repo: GitRepository, sha):
    """Read object_id from repo. Return GitObject depends on the object."""
    path = repo_file(repo, "objects", sha[0:2], sha[2:])
    with open(path, 'rb') as f:
        raw = zlib.decompress(f.read())
        # read object type
        x = raw.find(b' ')
        fmt = raw[0:x]

        # read and validate object size
        y = raw.find(b'\x00', x)
        size = int(raw[x:y].decode('ascii'))
        if size != len(raw) - y -1:
            raise Exception("Malformed object {0}: bad length".format(sha))
        
        # choose constructor
        if   fmt == b'commit': c = GitCommit
        elif fmt == b'tree'  : c = GitTree
        elif fmt == b'tag'   : c = GitTag
        elif fmt == b'blob'  : c == GitBlob
        else: 
            raise Exception("Unknown type {0} for object {1}".format(fmt.decode('ascii'), sha))
        
        # call constructor and return object
        return c(repo, raw[y+1:])

def object_find(repo: GitRepository, name, fmt=None, follow=True):
    return name

def object_write(obj: GitObject, actually_write=True):
    # serialize object data
    data = obj.serialize()
    # add header
    result = obj.fmt + b' ' + str(len(data)).encode() + b'\x00' + data
    # compute hash
    sha = hashlib.sha1(result).hexdigest()

    if actually_write:
        path = repo_file(obj.repo, "objects", sha[:2], sha[2:], mkdir=actually_write)
        with open(path, 'wb') as f:
            # compress and write
            f.write(zlib.compress(result))

