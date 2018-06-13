
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
CONFIG_FILE = '~/.ansible/mazer.yml'
