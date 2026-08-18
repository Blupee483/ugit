import subprocess
import os

from collections import defaultdict
from tempfile import NamedTemporaryFile as Temp

from . import data

def iter_changed_files(t_from, t_to):
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if(o_from != o_to):
            action = ('new file' if not o_from else 'deleted' if not o_to else 'modified')
            yield path, action

def compare_trees(*trees):
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid

    for path, oids in entries.items():
        yield (path, *oids)

def diff_trees(t_from, t_to):
    output = b''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if(o_from != o_to):
            #output += f'changed: {path}\n'
            output += diff_blobs(o_from, o_to, path)
    return output

def diff_blobs(o_from, o_to, path = 'blob'):
    f_from = Temp(delete = False)
    f_to = Temp(delete = False)
    try:
        for oid, f in ((o_from, f_from), (o_to, f_to)):
            if(oid):
                f.write(data.get_object(oid))
                f.flush()

        f_from.close()
        f_to.close()

        diff_bin = r'C:\Program Files (x86)\GnuWin32\bin\diff.exe'

        with subprocess.Popen(
            [diff_bin, '--unified', '--show-c-function', 
            '--label', f'a/{path}', f_from.name, 
            '--label', f'b/{path}', f_to.name], 
            stdout = subprocess.PIPE, 
            stderr = subprocess.PIPE) as proc: 
            output, _ = proc.communicate()

        return output
    finally:
        for f in (f_from, f_to):
            if os.path.exists(f.name):
                os.unlink(f.name)

def merge_trees(t_base, t_HEAD, t_other):
    tree = {}
    for path, o_base, o_HEAD, o_other in compare_trees(t_base, t_HEAD, t_other):
        tree[path] = data.hash_object(merge_blobs(o_base, o_HEAD, t_HEAD))
    return tree

def merge_blobs(o_base, o_HEAD, o_other):
    f_base = Temp(delete = False)
    f_HEAD = Temp(delete = False)
    f_other = Temp(delete = False)

    try:
        for oid, f in ((o_base, f_base), (o_HEAD, f_HEAD), (o_other, f_other)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()

        f_base.close()
        f_HEAD.close()
        f_other.close()
            
        diff_bin = r'C:\Program Files (x86)\GnuWin32\bin\diff3.exe'
        with subprocess.Popen([diff_bin, '-m', '-L', 'HEAD', f_HEAD.name, '-L', 'base', f_base.name, '-L', 'MERGE_HEAD', f_other.name], stdout = subprocess.PIPE) as proc:
            output, _ = proc.communicate()
            assert proc.returncode in (0, 1)

        return output
    finally:
        for f in (f_base, f_HEAD, f_other):
            if os.path.exists(f.name):
                os.path.unlink(f.name)