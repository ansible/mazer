import logging
import os
import re
import shutil

from jinja2 import Environment, FileSystemLoader

log = logging.getLogger(__name__)


def init(role_name,
         init_path,
         role_path,
         force,
         role_skeleton_path,
         skeleton_ignore_expressions,
         role_type,
         display_callback=None):

    # FIXME(akl): role_skeleton stuff should probably be a module or two and a few classes instead of inline here
    # role_skeleton ends mostly being a list of file paths to copy
    inject_data = dict(
        role_name=role_name,
    )

    import pprint
    log.debug('inject_data: %s', pprint.pformat(inject_data))

    if not os.path.exists(role_path):
        os.makedirs(role_path)

    role_skeleton = os.path.expanduser(role_skeleton_path)

    log.debug('role_skeleton: %s', role_skeleton)
    skeleton_ignore_re = [re.compile(x) for x in skeleton_ignore_expressions]

    template_env = Environment(loader=FileSystemLoader(role_skeleton))

    for root, dirs, files in os.walk(role_skeleton, topdown=True):
        rel_root = os.path.relpath(root, role_skeleton)
        in_templates_dir = rel_root.split(os.sep, 1)[0] == 'templates'
        dirs[:] = [d for d in dirs if not any(r.match(d) for r in skeleton_ignore_re)]

        for f in files:
            filename, ext = os.path.splitext(f)
            if any(r.match(os.path.join(rel_root, f)) for r in skeleton_ignore_re):
                continue
            elif ext == ".j2" and not in_templates_dir:
                src_template = os.path.join(rel_root, f)
                dest_file = os.path.join(role_path, rel_root, filename)
                template_env.get_template(src_template).stream(inject_data).dump(dest_file)
            else:
                f_rel_path = os.path.relpath(os.path.join(root, f), role_skeleton)
                log.debug('copying %s to %s',
                          os.path.join(root, f), os.path.join(role_path, f_rel_path))
                shutil.copyfile(os.path.join(root, f), os.path.join(role_path, f_rel_path))

        for d in dirs:
            dir_path = os.path.join(role_path, rel_root, d)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

    display_callback("- %s was created successfully" % role_name)

    return 0
