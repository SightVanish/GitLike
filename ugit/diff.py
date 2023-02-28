import subprocess
from collections import defaultdict
from tempfile import NamedTemporaryFile as Temp
import difflib
from . import data

def compare_trees(*trees):
    """
    Take a list of trees and return them grouped by filename
    """
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid
    for path, oids in entries.items():
        yield(path, *oids)

def iter_changed_files(t_from, t_to):
    """
    Iterate all files in two trees and return the unmatched files
    """
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            action = ('new file' if not o_from else
                      'deleted' if not o_to else
                      'modified')
            yield path, action

def diff_trees(t_from, t_to):
    """
    Compare two trees and output the path to the changed files 
    """
    output = b''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            # output += 'changed: {0}\n'.format(path)
            output += diff_blobs(o_from, o_to, path)
    return output

def diff_blobs(o_from, o_to, path='blob'):
    """
    Compare two files and return the unmatched lines
    """
    with Temp() as f_from, Temp() as f_to:
        for oid, f in ((o_from, f_from), (o_to, f_to)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()
        with subprocess.Popen(
            ['diff', '--unified', '--show-c-function',
            '--label', f'a/{path}', f_from.name,
            '--label', f'b/{path}', f_to.name],
            stdout=subprocess.PIPE
        ) as proc:
            output, _ = proc.communicate()
        return output

def merge_tree(t_HEAD, t_other):
    """
    Merge each file in two trees and return merged tree
    """
    tree = {}
    for path, o_HEAD, o_other in compare_trees(t_HEAD, t_other):
        tree[path] = merge_blobs(o_HEAD, o_other)
    return tree

def merge_blobs(o_HEAD, o_other):
    """
    Merge two files and return merged content
    """
    with Temp() as f_HEAD, Temp() as f_other:
        for oid, f in ((o_HEAD, f_HEAD), (o_other, f_other)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()
        with subprocess.Popen(
            ['diff', '-DHEAD', f_HEAD.name, f_other.name],
            stdout=subprocess.PIPE
        ) as proc:
            output, _ = proc.communicate()
        return output
