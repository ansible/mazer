=======
History
=======

0.3.0 (2018-11-06)
------------------

* `155 Implement install of things with dep solving (for trad roles and collections) <https://github.com/ansible/mazer/issues/155>`_.
* `142 Add support for init of a collection, and make it the default <https://github.com/ansible/mazer/pull/142>`_.
* `139 Add 'editable' installs via 'install -e' (ala, 'python setup.py develop') <https://github.com/ansible/mazer/issues/139>`_.
* `138 Install role requirements <https://github.com/ansible/mazer/issues/138>`_.
* `136 Support global content install option <https://github.com/ansible/pull/136>`_.
* `135 For multi-content archive, install all content <https://github.com/ansible/mazer/pull/135>`_.
* `133 Add MAZER_CONFIG environment var for specifying config file location <https://github.com/ansible/mazer/pull/133>`_.
* `116 Add a 'mazer build' command to build collection artifacts <https://github.com/ansible/mazer/issues/116>`_.
* `151 Fix install of sdx_licenses.json <https://github.com/ansible/mazer/issues/151>`_.
* `132 Fix log directory creation before initializing logger. Support multiple locations for mazer.yml config <https://github.com/ansible/mazer/pull/132>`_.
* `127 Refactor ansible_galaxy.flat_rest_api.content <https://github.com/ansible/mazer/issues/127>`_.
* `126 Finish replacing core data objects with 'attrs' based classes <https://github.com/ansible/mazer/issues/126>`_.
* `124 Fix unneeded --roles-path option for init and install commands by removing it <https://github.com/ansible/mazer/pull/124>`_.
* `119 Fix "'mazer list' on multi-content repos looks for install_info in the wrong places" <https://github.com/ansible/mazer/issues/119>`_.

0.2.1 (2018-08-08)
------------------

* Add 'attrs' dep to setup.py. Update requirements.txt
  to use setup.py requires.
* Add the default logging config to Manifest.in so
  logging is setup correctly on pip install.
  Fixes https://github.com/ansible/mazer/issues/114
* Fix install if a role name is substring of another role.
  Fixes https://github.com/ansible/mazer/issues/112
* Create and send a X-Request-ID on http requests.

0.2.0 (2018-07-26)
------------------

* Support new
  ~/.ansible/content/namespace/reponame/content_type/content_name layout
* Create install receipts (.galaxy_install_info) on
  install of repos and roles.
* 'list' and 'info' commands updated.
* Now requires and uses 'attrs' python module >=18.1.0

0.1.0 (2018-04-18)
------------------

* First release on PyPI.
