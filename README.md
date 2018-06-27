# Mazer 

A new command-line tool for managing [Ansible](https://github.com/ansible/ansible) content.

### Expect breaking changes!

Mazer is experimental, and currently only available for tech-preview. Use with lots of caution! It is not intended for use in
production environments, nor is it currently intended to replace the `ansible-galaxy` command-line tool.

If you're installing Ansible content in a production environment, or need assistance with Ansible, please visit the [Ansible project](https://github.com/ansible/ansible), or the [Ansible docs site](https://docs.ansible.com).

## Proposed Features

- Support repositories containing multiple roles. In other words, allow
for multiple roles all in one repository.

## Examples

### Installing roles

To install the galaxy role [geerlingguy.nginx](https://galaxy.ansible.com/geerlingguy/nginx/) via galaxy:

```
$ mazer install geerlingguy.nginx
```

To install a specific version via galaxy:

```
$ mazer install geerlingguy.nginx,2.6.0
```

To install via github:

```
$ mazer install git+https://github.com/geerlingguy/ansible-role-nginx
```

### Installing repos with multiple roles

To install the galaxy repo [testing.ansible-testing-content](https://galaxy.ansible.com/testing/ansible-testing-content):

```
$ mazer install testing.ansible-testing-content
```

This will install all of the roles in the https://galaxy.ansible.com/testing/ansible-testing-content
to ~/.ansible/content/testing.ansible-testing-content/roles/

```
$ tree ~/.ansible/content/
/home/user/.ansible/content/
└── testing.ansible-testing-content
    └── roles
        ├── ansible-role-foobar
        │   ├── defaults
        │   │   └── main.yml
        │   ├── handlers
        │   │   └── main.yml
        │   ├── meta
        │   │   └── main.yml
        │   ├── README.md
        │   ├── tasks
        │   │   └── main.yml
        │   ├── tests
        │   │   ├── inventory
        │   │   └── test.yml
        │   └── vars
        │       └── main.yml
        ├── ansible-test-role-1
        │   ├── defaults
        │   │   └── main.yml
        │   ├── handlers
        │   │   └── main.yml
        │   ├── meta
        │   │   └── main.yml
        │   ├── README.md
        │   ├── tasks
        │   │   └── main.yml
        │   ├── tests
        │   │   ├── inventory
        │   │   └── test.yml
        │   └── vars
        │       └── main.yml
        ├── test-role-a
        │   ├── defaults
        │   │   └── main.yml
        │   ├── handlers
        │   │   └── main.yml
        │   ├── meta
        │   │   └── main.yml
        │   ├── tasks
        │   │   └── main.yml
        │   ├── tests
        │   │   ├── inventory
        │   │   └── test.yml
        │   └── vars
        │       └── main.yml
        ├── test-role-b
        │   ├── defaults
        │   │   └── main.yml
        │   ├── handlers
        │   │   └── main.yml
        │   ├── meta
        │   │   └── main.yml
        │   ├── README.md
        │   ├── tasks
        │   │   └── main.yml
        │   ├── tests
        │   │   ├── inventory
        │   │   └── test.yml
        │   └── vars
        │       └── main.yml
        ├── test-role-c
        │   ├── defaults
        │   │   └── main.yml
        │   ├── handlers
        │   │   └── main.yml
        │   ├── meta
        │   │   └── main.yml
        │   ├── README.md
        │   ├── tasks
        │   │   └── main.yml
        │   ├── tests
        │   │   ├── inventory
        │   │   └── test.yml
        │   └── vars
        │       └── main.yml
        └── test-role-d
            ├── defaults
            │   └── main.yml
            ├── handlers
            │   └── main.yml
            ├── meta
            │   └── main.yml
            ├── README.md
            ├── tasks
            │   └── main.yml
            ├── tests
            │   ├── inventory
            │   └── test.yml
            └── vars
                └── main.yml
```

### Install a role to a different content path

```
$ mazer install --content-path ~/my-ansible-content geerlingguy.nginx
```

This will install the geerlingguy.nginx role to ~/my-ansible-content/roles/geerlingguy.nginx


## Configuration

mazer is configured by a 'mazer.yml' config file in ~/.ansible.

``` yaml
# The galaxy rest api server mazer will communicate with.
server:
  # The http or https URL of the Galaxy server used by default.
  # REST requests will be made to https://galaxy-qa.ansible.com/api/v1
  # in this example.
  #
  # default: https://galaxy-qa.ansible.com
  #
  url: https://galaxy-qa.ansible.com

  # if ignore_certs is true, https requests will not verify the
  # https server certificate is signed a known CA.
  #
  # default: False (https connections do verify certificates)
  #
  ignore_certs: false

# When installing content like ansible roles, mazer will install into
# sub directories of this path.
#
# default: ~/.ansible/content
#
content_path: ~/.ansible/content

options:
  # A list of file glob patterns to ignore when
  # 'init' creates a role from a role skeleton.
  role_skeleton_ignore:
    - ^.git$
    - ^.*/.git_keep$

  # role_skeleton_path is a path to a directory of
  # custom role skeletons to use instead of the built
  # in skeletons.
  #
  # default: Relative to mazers installation, for example:
  #          ~/.local/lib/python2.7/site-packages/mazer-0.1.0-py3.6.egg/ansible_galaxy_cli/data/role_skeleton/
  #
  role_skeleton_path: null

# The version of the config file format.
# This should never need to be changed manually.
version: 1
```

## Installing Mazer

### From source

The source code for mazer lives at [https://github.com/ansible/mazer](https://github.com/ansible/mazer)

```
$ git clone https://github.com/ansible/mazer.git
$ cd mazer
$ python setup.py install
```

Or install the requirements via pip:

```
$ pip install -r requirements.txt
```

### Via pip (from git)
```
pip install -v git+ssh://git@github.com/ansible/mazer.git
```

## Testing

### Running from a source checkout

To run mazer from a source checkout, without installing, use the setup.py 'develop' command:

```
python setup.py develop
```

### Unit testing

mazer uses pytest for unit tests.

#### Test requirements

To install test requirements, use pip to install the requirements in requirements_test.txt:

```
pip install -r requirements_test.txt
To run unit tests

via `tox` for default platforms (python 2.6, 2.7, 3.6):
```

```
$ tox
```

via 'pytest' directly

```
$ pytest tests/
```

## Prerequisites

When installing content from an Ansible Galaxy server, requires Galaxy v3.0+.

## Roadmap

To see what we're working on, and where we're headed, [view the roadmap](./ROADMAP.md).

## Getting help

Issues welcome! If you find a bug, or have a feature idea, please let us know by [opening an issue](https://github.com/ansible/mazer/issues).

You can also reach out to us on irc.freenode.net in the #ansible-galaxy channel.

## Origin of "Mazer"

The name Mazer comes from a character from Ender's Game, Mazer Rackham, that Wikipedia describes as "the half-Māori captain who singlehandedly stopped the Second Invasion by realizing that the Buggers are a hive mind. Due to his inability to pass on his knowledge, he was forced to spend fifty years at relativistic speeds (eight years to Rackham) so that he could train the next commander — Ender Wiggin."

A mazer is also a hardwood drinking vessel.

## License

[GNU General Public License v3.0](./LICENSE)


