from collections import defaultdict

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

def diff_trees(t_from, t_to):
    """
    Compare two trees and output the path to the changed files 
    """
    output = ''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += 'changed: {0}\n'.format(path)
    return output
