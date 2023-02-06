import argparse
import os
import sys
import textwrap
from . import data
from . import base

def main():
    args = parse_args()
    args.func(args)

def parse_args():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command')
    commands.required = True

    # init
    init_parser = commands.add_parser('init')
    init_parser.set_defaults(func=init)

    # hash object and store the value
    hash_object_parser = commands.add_parser('hash-object')
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument('file')

    # take oid of an object and read its content
    cat_file_parser = commands.add_parser('cat-file')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object')

    # hash directory tree and store the tree
    write_tree_parser = commands.add_parser('write-tree')
    write_tree_parser.set_defaults(func=write_tree)

    # take oid of a directory tree and extract it to a working directory
    read_tree_parser = commands.add_parser('read-tree')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree')

    # commit, save a snapshot of working directory
    commit_parser = commands.add_parser('commit')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True)

    # walk the list of commits and print them
    log_parser = commands.add_parser('log')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', nargs='?') # nargs='?': if there is no such value, assign to default

    return parser.parse_args()


def init(args):
    data.init()
def hash_object(args):
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read())) # print hash code
def cat_file(args):
    sys.stdout.flush() # print the string in stream
    sys.stdout.buffer.write(data.get_object(args.object, expected=None)) # write string to stream, expected=None if we don't want to verify the type
def write_tree(args):
    base.write_tree()
def read_tree(args):
    base.read_tree(args.tree)
def commit(args):
    print(base.commit(args.message))
def log(args):
    oid = args.oid or data.get_HEAD()
    while oid != "None":
        commit = base.get_commit(oid)
        print("commit {0}".format(oid))
        print(commit.message)
        oid = commit.parent
