import argparse
import os
import sys
import textwrap
import subprocess
from . import data
from . import base
from . import diff

def main():
    args = parse_args()
    args.func(args)

def parse_args():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest='command')
    commands.required = True

    oid = base.get_oid # you can pass oid directly or use your tag

    init_parser = commands.add_parser('init')
    init_parser.set_defaults(func=init)

    hash_object_parser = commands.add_parser('hash-object')
    hash_object_parser.set_defaults(func=hash_object)
    hash_object_parser.add_argument('file')

    cat_file_parser = commands.add_parser('cat-file')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object', type=oid)

    write_tree_parser = commands.add_parser('write-tree')
    write_tree_parser.set_defaults(func=write_tree)

    read_tree_parser = commands.add_parser('read-tree')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree', type=oid)

    commit_parser = commands.add_parser('commit')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True)

    log_parser = commands.add_parser('log')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', default='@', type=oid, nargs='?') # nargs='?': if there is no such value, assign to default

    checkout_parser = commands.add_parser('checkout')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('commit')

    tag_parser = commands.add_parser('tag')
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument('name')
    tag_parser.add_argument('oid', default='@', type=oid, nargs='?')

    branch_parser = commands.add_parser('branch')
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument('name', nargs='?')
    branch_parser.add_argument('start_point', default='@', type=oid, nargs='?')

    k_parser = commands.add_parser('k')
    k_parser.set_defaults(func=k)

    status_parser = commands.add_parser('status')
    status_parser.set_defaults(func=status)

    reset_parser = commands.add_parser('reset')
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument('commit', type=oid)

    show_parser = commands.add_parser('show')
    show_parser.set_defaults(func=show)
    show_parser.add_argument('oid', default='@', type=oid, nargs='?')

    diff_parser = commands.add_parser('diff')
    diff_parser.set_defaults(func=_diff)
    diff_parser.add_argument('commit', default='@', type=oid, nargs='?')

    merge_parser = commands.add_parser('merge')
    merge_parser.set_defaults(func=merge)
    merge_parser.add_argument('commit', type=oid)

    return parser.parse_args()

def init(args):
    # init
    base.init()

def hash_object(args):
    # hash object and store the value
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read())) # print hash code
        
def cat_file(args):
    # take oid of an object and read its content
    sys.stdout.flush() # print the string in stream
    sys.stdout.buffer.write(data.get_object(args.object, expected=None)) # write string to stream, expected=None if we don't want to verify the type

def write_tree(args):
    # hash directory tree and store the tree
    base.write_tree()

def read_tree(args):
    # take oid of a directory tree and extract it to a working directory
    base.read_tree(args.tree)

def commit(args):
    # save a snapshot of working directory
    print(base.commit(args.message))

def log(args):
    refs = {}
    # get all tags and branches
    HEAD = data.get_ref('HEAD', deref=False).value
    for refname, ref in data.iter_refs('refs/heads/'):
        HEAD_ref = '\033[1;34;1mHEAD -> \033[0m' if HEAD == refname else '' # print in blue
        refname = HEAD_ref + '\033[1;32;1m{0}\033[0m'.format(refname.split('refs/heads/', 1)[1]) # print in green
        refs.setdefault(ref.value, []).append(refname)
    for refname, ref in data.iter_refs('refs/tags/'):   
        # print in hightlight yellow
        refname = '\033[1;33;1mtag: {0}\033[0m'.format(refname.split('refs/tags/', 1)[1])
        refs.setdefault(ref.value, []).append(refname)

    # walk the list of commits and print them
    for oid in base.iter_commits_and_parents({args.oid}):
        commit = base.get_commit(oid)
        _print_commit(oid, commit, refs.get(oid)) # refs.get(oid) will return None if oid not in refs

def checkout(args):
    # move to the commit
    base.checkout(args.commit)

def tag(args):
    # tag a customized name to a commit
    oid = args.oid or data.get_ref('HEAD')
    base.create_tag(args.name, oid)

def branch(args):
    # TODO: add delete branch
    if args.name:
        # create branch
        base.create_branch(args.name, args.start_point)
        print("Branch {0} created at {1}".format(args.name, args.start_point[:10]))
    else:
        # list all branchs
        current = base.get_branch_name()
        for branch in base.iter_branch_names():
            if branch == current:
                print('* \033[32m{0}\033[0m'.format(branch))
            else:
                print('  {0}'.format(branch))

def status(args):
    # print branch
    HEAD = base.get_oid('@')
    branch = base.get_branch_name()
    if branch:
        print('On branch {0}'.format(branch))
    else:
        print('\033[31mHEAD detached at\033[0m {0}'.format(HEAD[:10]))

    Merged_HEAD = data.get_ref('Merged_HEAD').value
    if Merged_HEAD:
        print('Merging with {0}'.format(Merged_HEAD[:10]))

    print('\nChanges to be committed:\n')
    HEAD_tree = HEAD and base.get_commit(HEAD).tree
    for path, action in diff.iter_changed_files(base.get_tree(HEAD_tree), base.get_working_tree()):
        print('    {0}: {1}'.format(action, path))

def reset(args):
    base.reset(args.commit)

def _print_commit(oid, commit, refs=None):
    ref_str = ('\033[1;33;1m (\033[0m' + '\033[1;33;1m, \033[0m'.join(refs) +'\033[1;33;1m)\033[0m') if refs else ''
    # print in heightlight yellow
    print("\033[1;33;1mcommit {0}\033[0m".format(oid) + ref_str)
    print("\n    {0}\n".format(commit.message))

def show(args):
    # show the difference between HEAD and previous commit
    if not args.oid:
        # no commit yet
        return
    commit = base.get_commit(args.oid)
    parent_tree = None
    if commit.parents:
        parent_tree = base.get_commit(commit.parents[0]).tree
    _print_commit(args.oid, commit)
    result = diff.diff_trees(
        base.get_tree(parent_tree), base.get_tree(commit.tree)
    )
    sys.stdout.flush()
    sys.stdout.buffer.write(result)

def _diff(args):
    # show the difference between working directory and specified commit
    tree = args.commit and base.get_commit(args.commit).tree # if commit return get_commit(commit).tree
    result = diff.diff_trees(base.get_tree(tree), base.get_working_tree())
    sys.stdout.flush()
    sys.stdout.buffer.write(result)

def merge(args):
    base.merge(args.commit)

def k(args):
    # visualize branchs, as gitk
    dot = 'digraph commits {\n'
    oids = set()
    for ref_name, ref in data.iter_refs(deref=False):
        dot += '"{0}" [shape=note]\n'.format(ref_name)
        dot += '"{0}" -> "{1}"'.format(ref_name, ref.value)
        if not ref.symbolic:
            oids.add(ref.value)
    for oid in base.iter_commits_and_parents(oids):
        commit = base.get_commit(oid)
        dot += '"{0}" [shape=box style=filled label="{1}"]\n'.format(oid, oid[:10])
        for parent in commit.parents:
            dot += '"{0}" -> "{1}"\n'.format(oid, parent)
    dot += '}'
    print(dot)
    # visulize dot with online tool: http://www.webgraphviz.com/; or install dot https://graphviz.org/download/
    # with subprocess.Popen(['dot', '-Tgtk', '/dev/stdin'], stdin=subprocess.PIPE) as proc:
    #     proc.communicate(dot.encode())
