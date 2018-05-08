import os
import shutil
import subprocess
import tempfile

from ansible_galaxy import exceptions


# TODO: split hg and git impls into sep methods, kind of a strategy pattern
def scm_archive_content(src, scm='git', name=None, version='HEAD'):
    """
    Archive a Galaxy Content SCM repo locally

    Implementation originally adopted from the Ansible RoleRequirement
    """
    if scm not in ['hg', 'git']:
        raise exceptions.GalaxyClientError("- scm %s is not currently supported" % scm)

    tempdir = tempfile.mkdtemp()
    clone_cmd = [scm, 'clone', src, name]

    with open('/dev/null', 'w') as devnull:
        try:
            popen = subprocess.Popen(clone_cmd, cwd=tempdir, stdout=devnull, stderr=devnull)
        except Exception as e:
            raise exceptions.GalaxyClientError('error executing: "%s": %s' % (" ".join(clone_cmd), e))
        rc = popen.wait()
    if rc != 0:
        raise exceptions.GalaxyClientError("- command %s failed in directory %s (rc=%s)" % (' '.join(clone_cmd), tempdir, rc))

    if scm == 'git' and version:
        checkout_cmd = [scm, 'checkout', version]
        with open('/dev/null', 'w') as devnull:
            try:
                popen = subprocess.Popen(checkout_cmd, cwd=os.path.join(tempdir, name), stdout=devnull, stderr=devnull)
            except (IOError, OSError):
                raise exceptions.GalaxyClientError("error executing: %s" % " ".join(checkout_cmd))
            rc = popen.wait()
        if rc != 0:
            raise exceptions.GalaxyClientError("- command %s failed in directory %s (rc=%s)" % (' '.join(checkout_cmd), tempdir, rc))

    temp_file = tempfile.NamedTemporaryFile(delete=False,
                                            prefix='tmp-ansible-galaxy-content-archive-',
                                            suffix='.tar')
    if scm == 'hg':
        archive_cmd = ['hg', 'archive', '--prefix', "%s/" % name]
        if version:
            archive_cmd.extend(['-r', version])
        archive_cmd.append(temp_file.name)
    if scm == 'git':
        archive_cmd = ['git', 'archive', '--prefix=%s/' % name, '--output=%s' % temp_file.name]
        if version:
            archive_cmd.append(version)
        else:
            archive_cmd.append('HEAD')

    with open('/dev/null', 'w') as devnull:
        popen = subprocess.Popen(archive_cmd, cwd=os.path.join(tempdir, name),
                                 stderr=devnull, stdout=devnull)
        rc = popen.wait()
    if rc != 0:
        raise exceptions.GalaxyClientError("- command %s failed in directory %s (rc=%s)" % (' '.join(archive_cmd), tempdir, rc))

    shutil.rmtree(tempdir, ignore_errors=True)
    return temp_file.name
