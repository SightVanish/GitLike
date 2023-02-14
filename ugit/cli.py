import argparse
import os
import sys
import textwrap
import subprocess
from . import data
from . import base

def main():
    args = parse_args()
    args.func(args)

def parse_args():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command')
    commands.required = True

    oid = base.get_oid # you can pass oid directly or use your tag

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
    cat_file_parser.add_argument('object', type=oid)

    # hash directory tree and store the tree
    write_tree_parser = commands.add_parser('write-tree')
    write_tree_parser.set_defaults(func=write_tree)

    # take oid of a directory tree and extract it to a working directory
    read_tree_parser = commands.add_parser('read-tree')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree', type=oid)

    # commit, save a snapshot of working directory
    commit_parser = commands.add_parser('commit')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True)

    # walk the list of commits and print them
    log_parser = commands.add_parser('log')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', default='@' ,type=oid, nargs='?') # nargs='?': if there is no such value, assign to default

    # move to given commit
    checkout_parser = commands.add_parser('checkout')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('oid', type=oid)

    # tag customized name to a commit
    tag_parser = commands.add_parser('tag')
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument('name')
    tag_parser.add_argument('oid', default='@', type=oid, nargs='?')

    k_parser = commands.add_parser('k')
    k_parser.set_defaults(func=k)

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
    oid = args.oid or data.get_ref('HEAD')
    while oid:
        commit = base.get_commit(oid)
        print("\033[1;33;1mcommit {0}\n\033[0m".format(oid)) # pring commit oid in highlight yellow
        print("    {0}\n".format(commit.message))
        oid = commit.parent
def checkout(args):
    base.checkout(args.oid)
def tag(args):
    oid = args.oid or data.get_ref('HEAD')
    base.create_tag(args.name, oid)
def k(args):
    dot = 'digraph commits {\n'
    oids = set()
    for ref_name, ref in data.iter_refs():
        dot += '"{0}" [shape=note]\n'.format(ref_name)
        dot += '"{0}" -> "{1}"'.format(ref_name, ref)
        oids.add(ref)
    for oid in base.iter_commits_and_parents(oids):
        commit = base.get_commit(oid)
        dot += '"{0}" [shape=box style=filled label="{1}"]\n'.format(oid, oid[:10])
        if commit.parent:
            dot += '"{0}" -> "{1}"\n'.format(oid, commit.parent)
    dot += '}'
    print(dot)

    # visulize dot with online tool: http://www.webgraphviz.com/; or install dot first https://graphviz.org/download/
    # with subprocess.Popen(['dot', '-Tgtk', '/dev/stdin'], stdin=subprocess.PIPE) as proc:
    #     proc.communicate(dot.encode())
