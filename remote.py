import os
from . import base
from . import data

REMOTE_REFS_BASE = 'refs/heads/'
LOCAL_REFS_BASE = 'refs/remote/'
def fetch(remote_path):
    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)

    for oid in base.iter_objects_in_commit(refs.values()):
        data.fetch_object_if_missing(oid, remote_path)

    for refname, value in refs.items():
        refname = os.path.relpath(remote_path, REMOTE_REFS_BASE)
        data.update_ref(f'{LOCAL_REFS_BASE}/{refname}', data.RefValue(symbolic = False, value = value))

def _get_remote_refs(remote_path, prefix = ''):
    with data.change_git_dir(remote_path):
        return {refname: ref.value for refname, ref in data.iter_refs(prefix)}

def push(remote_path, refname):
    remote_refs = _get_remote_refs(remote_path)
    remote_ref = remote_refs.get(refname)
    local_ref = data.get_ref(refname).value
    assert local_ref

    assert not remote_ref or base.is_ancestor_of(local_ref, remote_ref)

    known_remote_refs = filter(data.object_exists, remote_refs.value())
    remote_objects = set(base.iter_objects_in_commit(known_remote_refs))
    local_objects = set(base.iter_objects_in_commit({local_ref}))
    objects_to_push = local_objects - remote_objects

    for oid in objects_to_push:
        data.push_object(oid, remote_path)
    
    with data.change_git_dir(remote_path):
        data.update_ref(refname, data.RefValue(symbolic = False, value = local_ref))