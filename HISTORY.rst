=======
History
=======

0.2.1 (2018-08-08)
------------------

* Add 'attrs' dep to setup.py. Update requirements.txt
  to use setup.py requires.
* Add the default logging config to Manifest.in so
  logging is setup correctly on pip install.
  Fixes https://github.com/ansible/mazer/issues/114
* Fix install if a role name is substring of another role
  Fixes https://github.com/ansible/mazer/issues/112
* Create and send a X-Request-ID on http requests.

0.2.0 (2018-07-26)
------------------

* Support new
  ~/.ansible/content/namespace/reponame/content_type/content_name layout
* Create install receipts (.galaxy_install_info) on
  install of repos and roles
* 'list' and 'info' commands updated
* Now requires and uses 'attrs' python module >=18.1.0

0.1.0 (2018-04-18)
------------------

* First release on PyPI.
