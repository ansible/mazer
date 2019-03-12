Old School Role
=========

This role will be matriculated to a collection

Role Variables
--------------

old_school_level: plaid

Dependencies
------------

geerlingguy.repo-epel

Example Playbook
----------------

``` yaml
    - hosts: proxies
      roles:
         - { role: some_namespace.old_school_role, old_school_level: charlotte_hornets_starter_jacket }

License
-------

MIT

