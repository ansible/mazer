import os


def get_config_path():
    paths = [
        'mazer.yml',
        '~/.ansible/mazer.yml'
        '/etc/ansible/mazer.yml'
    ]
    for path in paths:
        if os.path.exists(os.path.expanduser(path)):
            return path
    return paths[1]


# a list of tuples that is fed to an OrderedDict
DEFAULTS = [
    ('server',
     {'url': 'https://galaxy-qa.ansible.com',
      'ignore_certs': False}
     ),

    # In order of priority
    ('content_path', '~/.ansible/content'),

    # runtime options
    ('options',
     {'role_skeleton_path': None,
      'role_skeleton_ignore': ["^.git$", "^.*/.git_keep$"]}
     ),
    ('version', 1),
]

# FIXME: replace with logging config
VERBOSITY = 0
CONFIG_FILE = get_config_path()
