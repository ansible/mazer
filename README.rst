

=====
Mazer
=====

Ansible content manager

A new command-line tool for managing [Ansible](https://github.com/ansible/ansible) content.

Expect breaking changes!
------------------------

Mazer is experimental, and currently only available for tech-preview. Use with lots of caution! It is not intended for use in
production environments, nor is it currently intended to replace the `ansible-galaxy` command-line tool.

If you're installing Ansible content in a production environment, or need assistance with Ansible, please visit the [Ansible project](https://github.com/ansible/ansible), or the [Ansible docs site](https://docs.ansible.com).

Proposed Features
-----------------

* More than just roles!
* Support all the content types, including: roles, modules, module utils, all types of plugins.
* Support repositories containing multipe types of each content. In other words, allow for mulitple modules, multiple plugins, and multiple roles all in one repository.
* Support installing modules and plugins from [Ansible Galaxy](https://galaxy.ansible.com), or directly from a source repository.

Examples
--------

Installing roles
````````````````

To install https://galaxy.ansible.com/geerlingguy/nginx/ https://github.com/geerlingguy/ansible-role-nginx via galaxy::

    $ mazer install geerlingguy.nginx

To install a specific version via galaxy::


    $ mazer install geerlingguy.nginx,2.6.0


To install via github::


    $ mazer install git+https://github.com/geerlingguy/ansible-role-nginx


Installing repos with multiple types of content
```````````````````````````````````````````````

To install https://github.com/alikins/ansible-testing-content (alikins.testing-content)::

    $ mazer install alikins.ansible-testing-content

This will install all of the content in the https://github.com/alikins/ansible-testing-content
repo, including various plugins, modules, module_utils, and roles to ~/.ansible/content

For example::

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


Install a role to a different content path
``````````````````````````````````````````

    $ mazer install --content-path ~/my-ansible-content geerlingguy.nginx

This will install the geerlingguy.nginx role to ~/my-ansible-content/roles/geerlingguy.nginx

Installing Mazer
----------------

From source
```````````
    $ git clone https://github.com/ansible/galaxy-cli.git
    $ cd galaxy-cli
    $ python setup.py install

Or install the requirements via pip::

    $ pip install -r requirements.txt

Via pip (from git)
``````````````````

    pip install -v git+ssh://git@github.com/ansible/galaxy-cli.git

Testing
-------

unit testing
````````````

galaxy-cli uses pytest for unit tests.

test requirements
~~~~~~~~~~~~~~~~~

To install test requirements, use pip to install the requirements in requirements_test.txt::

    pip install -r requirements_test.txt

To run unit tests via `tox` for default platforms (python 2.6, 2.7, 3.6)::

    $ tox

via 'pytest' directly::

    $ pytest tests/

Prerequisites
-------------

When installing content from an Ansible Galaxy server, requires Galaxy v3.0+.

Roadmap
-------

To see what we're working on, and where we're headed, [view the roadmap](./ROADMAP.md).

Getting help
------------

Issues welcome! If you find a bug, or have a feature idea, please let us know by [opening an issue](https://github.com/ansible/mazer/issues).

You can also reach out to us on irc.freenode.net in the #ansible-galaxy channel.

Origin of "Mazer"
-----------------

The name Mazer comes from a character from Ender's Game, Mazer Rackham, that Wikipedia describes as "the half-Māori captain who singlehandedly stopped the Second Invasion by realizing that the Buggers are a hive mind. Due to his inability to pass on his knowledge, he was forced to spend fifty years at relativistic speeds (eight years to Rackham) so that he could train the next commander — Ender Wiggin."

A mazer is also a hardwood drinking vessel.

License
-------

[GNU General Public License v3.0](./LICENSE)
