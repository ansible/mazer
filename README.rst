

=====
Mazer
=====

Ansible content manager

A new command-line tool for managing `Ansible <https://github.com/ansible/ansible>`__ content.

Expect breaking changes!
------------------------

Mazer is experimental, and currently only available for tech-preview. Use with lots of caution! It is not intended for use in
production environments, nor is it currently intended to replace the `ansible-galaxy` command-line tool.

If you're installing Ansible content in a production environment, or need assistance with Ansible, please visit the `Ansible Project <https://github.com/ansible/ansible>`__,
or the `Ansible docs site <https://docs.ansible.com>`__.

Proposed Features
-----------------

* Support repositories containing multiple roles. In other words, allow for multiple roles all in one repository.

Examples
--------

Installing roles
````````````````

To install `geerlingguy.nginx <https://galaxy.ansible.com/geerlingguy/nginx/>`__ via galaxy::

    $ mazer install geerlingguy.nginx

See `mazer github repo <https://github.com/ansible/mazer>`__ for more examples.

Installing Mazer
----------------

From source
```````````

The source code for mazer lives at `https://github.com/ansible/mazer <https://github.com/ansible/mazer>`__

    $ git clone https://github.com/ansible/mazer.git
    $ cd mazer
    $ python setup.py install

Or install the requirements via pip::

    $ pip install -r requirements.txt

Via pip (from git)
``````````````````

    pip install -v git+ssh://git@github.com/ansible/mazer.git

Testing
-------

unit testing
````````````

mazer uses pytest for unit tests.

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

To see what we're working on, and where we're headed, `view the roadmap <https://github.com/ansible/mazer/ROADMAP.md>`__.

Getting help
------------

Issues welcome! If you find a bug, or have a feature idea, please let us know by `opening an issue <https://github.com/ansible/mazer/issues>`__.

You can also reach out to us on irc.freenode.net in the #ansible-galaxy channel.

Origin of "Mazer"
-----------------

The name Mazer comes from a character from Ender's Game, Mazer Rackham, that Wikipedia describes as "the half-Māori captain who singlehandedly stopped the Second Invasion by realizing that the Buggers are a hive mind. Due to his inability to pass on his knowledge, he was forced to spend fifty years at relativistic speeds (eight years to Rackham) so that he could train the next commander — Ender Wiggin."

A mazer is also a hardwood drinking vessel.

License
-------

`GNU General Public License v3.0 <https://github.com/ansible/mazer/LICENSE>`__
