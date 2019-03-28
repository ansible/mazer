# Mazer

A new command-line tool for managing [Ansible](https://github.com/ansible/ansible) content.

**Note:** Mazer is most useful when used with a version of Ansible that understands mazer installed content.
Currently that means ansible 2.8 and later.

**Note:** By default, mazer currently defaults to using the "beta" Ansible Galaxy server at https://galaxy-qa.ansible.com.
https://galaxy-qa.ansible.com may have different data than the primary Ansible Galaxy server at https://galaxy.ansible.com

### Expect breaking changes!

Mazer is experimental, and currently only available for tech-preview. Use with lots of caution! It is not intended for use in
production environments, nor is it currently intended to replace the `ansible-galaxy` command-line tool.

If you're installing Ansible content in a production environment, or need assistance with Ansible, please visit the [Ansible project](https://github.com/ansible/ansible), or the [Ansible docs site](https://docs.ansible.com).

## Proposed Features

- Install content from Galaxy artifacts containing collections of Ansible roles, modules and plugins ('mazer install')
- Generate artifacts from local content that can then be published to the Galaxy server ('mazer build')
- Provide versioned management of installed content
- Integrate with popular testing tools like Ansible Lint and Molecule

## Docs

For additional documentation on mazer, view the [Mazer topic on Ansible Galaxy Docs](https://galaxy.ansible.com/docs/mazer/index.html)

## Examples

### Installing collection

To install the galaxy repo [testing.ansible_testing_content](https://galaxy-qa.ansible.com/testing/ansible_testing_content):

```
$ mazer install testing.ansible_testing_content
```

This will install the collection in the https://galaxy-qa.ansible.com/testing/ansible_testing_content
to ~/.ansible/collections/ansible_collections/testing/ansible_testing_content/

```
/home/adrian/.ansible/collections/ansible_collections
└── alikins
    ├── ansible_testing_content
    │   ├── FILES.json
    │   ├── galaxy.yml
    │   ├── galaxy.yml.new
    │   ├── __init__.py
    │   ├── LICENSE
    │   ├── MANIFEST.json
    │   ├── meta
    │   ├── plugins
    │   │   ├── action
    │   │   │   └── add_host.py
    │   │   ├── filter
    │   │   │   ├── json_query.py
    │   │   │   ├── mathstuff.py
    │   │   │   └── newfilter.py
    │   │   ├── lookup
    │   │   │   ├── fileglob.py
    │   │   │   ├── k8s.py
    │   │   │   ├── newlookup.py
    │   │   │   └── openshift.py
    │   │   ├── modules
    │   │   │   ├── elasticsearch_plugin.py
    │   │   │   ├── kibana_plugin.py
    │   │   │   ├── module_in_bash.sh
    │   │   │   ├── mysql_db.py
...
```

### Install a collection to a different content path

```
$ mazer install --content-path ~/my-ansible-content alikins.collection_inspect
```

This will install the alikins.collection_inspect role to ~/my-ansible-content/alikins/collection_inspect

### Installing collections in 'editable' mode for development

To enable development of collections, it is possible to install a
local checkout of a collection in 'editable' mode.

Instead of copying a collection into ~/.ansible/collections/ansible_collections, this mode will
create a symlink from ~/.ansible/collections/ansible_collections/my_namespace/my_colllection
to the directory where the collection being worked on lives.

ie, if ~/src/collections/my_new_collection is being worked on, to install
the collection in editable mode under the namespace 'my_namespace':

```
$ mazer install --namespace my_namespace --editable ~/src/collections/my_new_collection
```

This will result in 'my_namespace.my_new_collection' being "installed".
The above command symlinks ~/.ansble/collections/ansible_collections/my_namespace/my_new_collection to
~/src/collections/my_new_collection.

The install option **'--editable'** or the short **'-e'** can be used.

Note that **'--namespace'** option is required.

### Building ansible content collection artifacts with 'mazer build'

In the future, galaxy will support importing and ansible content collection
artifacts. The artifacts are collection archives with the addition of
a MANIFEST.json providing a manifest of the content (files) in the archive
as well as additional metadata.

For example, to build the test 'hello' collection included in mazer
source code in tests/ansible_galaxy/collection_examples/hello/

```
$ # From a source tree checkout of mazer
$ cd tests/ansible_galaxy/collection_examples/hello/
$ mazer build
```

### Migrating an existing traditional style role to a collection with 'mazer migrate_role'

```
$ mazer migrate_role --role roles/some_trad_role/ --output-dir collections/roles/some_trad_role --namespace some_ns --version=1.2.3
```

The above command will create an ansible content collection artifact
at tests/ansible_galaxy/collection_examples/hello/releases/v11.11.11.tar.gz

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

# When installing content like ansible collection globally (using the '-g/--global' flag),
# mazer will install into sub directories of this path.
#
# default: /usr/share/ansible/collections/ansible_collections
#
global_content_path: /usr/share/ansible/collections/ansible_collections

# When installing content like ansible roles, mazer will install into
# sub directories of this path.
#
# default: ~/.ansible/collections/ansible_collections
#
content_path: ~/.ansible/collections/ansible_collections

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

### Via pip (latest release)
```
pip install mazer
```

### Via pip (latest from git)
```
pip install -v git+ssh://git@github.com/ansible/mazer.git
```

### Verifying installed version of ansible supports mazer content

The versions of ansible that support mazer content have a config option for setting the content path.
If the install ansible has this config option, mazer content will work.

To verify that, run the command 'ansible-config list | grep COLLECTIONS_PATH'.
If 'COLLECTIONS_PATH' is found the correct branch of ansible is installed.

```
$ ansible-config list | grep COLLECTIONS_PATH
COLLECTIONS_PATH:
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

## Changelog

To keep up with the latest changes, view the [changelog](./CHANGELOG.rst).

## Getting help

Issues welcome! If you find a bug, or have a feature idea, please let us know by [opening an issue](https://github.com/ansible/mazer/issues).

You can also reach out to us on irc.freenode.net in the #ansible-galaxy channel.

## Origin of "Mazer"

The name Mazer comes from a character from Ender's Game, Mazer Rackham, that Wikipedia describes as "the half-Māori captain who singlehandedly stopped the Second Invasion by realizing that the Buggers are a hive mind. Due to his inability to pass on his knowledge, he was forced to spend fifty years at relativistic speeds (eight years to Rackham) so that he could train the next commander — Ender Wiggin."

A mazer is also a hardwood drinking vessel.

## License

[GNU General Public License v3.0](./LICENSE)


