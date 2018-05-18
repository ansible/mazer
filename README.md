# galaxy-cli

ansible-galaxy-cli is a tool to manage ansible related content from https://galaxy.ansible.com

## Features

- More than just roles!
- Content types include modules, module utils, all plugin types.
- Content repos can contain multipe types of ansible content
  - repos can contain multiple roles
  - repos can also contain modules and plugins
- Supports installing modules and plugins from galaxy or directly from repos

## Examples

### Installing roles

To install https://galaxy.ansible.com/geerlingguy/nginx/ https://github.com/geerlingguy/ansible-role-nginx via galaxy:

```
$ ansible-galaxy-cli install geerlingguy.nginx
```

To install a specific version via galaxy:

```
$ ansible-galaxy-cli install geerlingguy.nginx,2.6.0
```

To install via github:

```
$ ansible-galaxy-cli install git+https://github.com/geerlingguy/ansible-role-nginx
```

### Installing repos with multiple types of content

To install https://github.com/alikins/ansible-testing-content (alikins.testing-content):

```
$ ansible-galaxy-cli install alikins.ansible-testing-content
```

This will install all of the content in the https://github.com/alikins/ansible-testing-content
repo, including various plugins, modules, module_utils, and roles to ~/.ansible/content

```
$ tree ~/.ansible/content
/home/ansible_user/.ansible/content/
├── action_plugins
│   └── add_host.py
├── filter_plugins
│   ├── json_query.py
├── library
│   ├── elasticsearch_plugin.py
│   ├── kibana_plugin.py
├── lookup_plugins
│   └── openshift.py
├── module_utils
│   ├── inventory.py
│   ├── raw.py
│   └── scale.py
├── roles
│   ├── test-role-a
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   └── main.yml
│   │   ├── tests
│   │   │   ├── inventory
│   │   │   └── test.yml
│   │   └── vars
│   │       └── main.yml
│   ├── test-role-b
│   │   ├── defaults
│   │   │   └── main.yml
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── meta
│   │   │   └── main.yml
│   │   ├── README.md
│   │   ├── tasks
│   │   │   └── main.yml
│   │   ├── tests
│   │   │   ├── inventory
│   │   │   └── test.yml
│   │   └── vars
│   │       └── main.yml
└── strategy_plugins
    ├── debug.py
    └── linear.py
```

### Installing just one type of content from a multi content repo

To install just the modules from https://github.com/alikins/ansible-testing-content:

```
$ ansible-galaxy-cli install -t modules alikins.ansible-testing-content
```

This will install only the modules from modules/ into ~/.ansible/content/library

```
$ tree ~/.ansible/content
/home/adrian/.ansible/content/
└── library
    ├── elasticsearch_plugin.py
    ├── kibana_plugin.py
    ├── mysql_db.py
    ├── mysql_replication.py
    ├── mysql_user.py
    ├── mysql_variables.py
    ├── redis.py
    └── riak.py

```

### Install just the strategy plugins

``` shell
# install just the strategy plugins from alikins.ansible-testing-content

ansible-galaxy-cli install -t strategy_plugin alikins.ansible-testing-content
tree ~/.ansible/content

# install just the modules

ansible-galaxy-cli install -t module alikins.ansible-testing-content
```

### Install a role to a different content path

```
$ ansible-galaxy-cli install --content-path ~/my-ansible-content geerlingguy.nginx
```

This will install the geerlingguy.nginx role to ~/my-ansible-content/roles/geerlingguy.nginx

## Installation of the ansible-galaxy-cli tool

### From source

```
$ git clone https://github.com/ansible/galaxy-cli.git
$ cd galaxy-cli
$ python setup.py install
```

Or install the requirements via pip:

```
$ pip install -r requirements.txt
```

### Via pip (from git)
```
pip install -v git+ssh://git@github.com/ansible/galaxy-cli.git
```

## Testing

### unit testing

galaxy-cli uses pytest for unit tests.

#### test requirements

To install test requirements, use pip to install the requirements in requirements_test.txt:

```
pip install -r requirements_test.txt
To run unit tests

via `tox` for default platforms (python 2.6, 2.7, 3.6):

```
$ tox
```

via 'pytest' directly

```
$ pytest tests/
```
