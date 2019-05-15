=========
Changelog
=========

0.5.0 (2019-04-15)
------------------

* WARNING: Mazer now requires a Ansible Galaxy server that provides the 'v2' style REST API.
  At time of release, that includes galaxy-dev.ansible.com and galaxy-qa.ansible.com
* WARNING: Support for directly installing 'traditional' style roles from Ansible Galaxy
  is no longer supported. ie, 'mazer install geerlingguy.ntp' will no longer work.
  However, roles can still be installed if they are included in a collection
* WARNING: The config file items and cli options for specifying install paths
           have changed and may break existing configs and scripts.
* The cli option '--content-root' is now '--collections-path'
* The short cli option '-C' is now shorthand for '--collections-path' instead
  of '--content-root'
* The config item 'content_root' has been replaced with 'collections_path'
* The config item 'global_content_root' has been replaced with 'global_collections_path'
* The new 'collections_path' value no longer needs to end with 'ansible_collections'
* The new 'global_collections_path' value no longer needs to end with 'ansible_collections'
* The new 'collections_path' defaults to '~/.ansible/collections'.
  Note that this replaces the previous 'content_root' config item that
  defaulted to '~/.ansible/collections/ansible_collections'
* The new 'global_collections_path' defaults to '/usr/share/ansible/collections'.
  Note that this replaces the previous 'global_content_root' config item that
  defaulted to '/usr/share/ansible/collections/ansible_collections'
* 'mazer install' with default 'collections_path' ('~/.ansible/collections') will
  still install to '~/.ansible/collections/ansible_collections', but install
  will add the require trailing 'ansible_collections' automatically.
* 'mazer install --global' with default 'globale_collections_path'
  ('/usr/share/ansible/collections') will still install to
  '/usr/share/ansible/collections/ansible_collections', but
  'install --global' will add the require trailing
  'ansible_collections' automatically.
* The REST API client now uses 'requests' python module instead of the 'url' module bundle from ansible.
* Add cli '--config' option to specify a path to an alternative config file.
* Add support for 'MAZER_HOME' environment variable. MAZER_HOME defaults to ~/.ansible and
  specifies where mazer looks for it's config (mazer.yml and mazer-logging.yml)
* `216 Use Galaxy REST API v2 <https://github.com/ansible/mazer/issues/216>`_.
* `239 Rename content-root to collections-path to be consistent with ansible <https://github.com/ansible/mazer/issues/239>`_.
* `228 For envs w/no LANG/locale/text encoding, assume utf8 <https://github.com/ansible/mazer/issues/228>`_.
* `236 Partial fix for scm_url installs <https://github.com/ansible/mazer/issues/236>`_.


0.4.0 (2019-03-28)
------------------

* The default path for collections to be installed
  is now '~/.ansible/collections/ansible_collections'
  which is also the default place ansible 2.8 or higher will search
  for collections.
* Add the 'mazer publish' for publishing a collection artifact to Ansible Galaxy
* `186 Implement 'migrate_role' command to convert traditional roles to collections <https://github.com/ansible/mazer/issues/186>`_.
* galaxy.yml 'authors' field is now a list
* galaxy.yml 'dependencies' field is now a dict where the key is the
  collection and the value is a https://github.com/rbarrois/python-semanticversion version spec
* galaxy.yml 'tags' field (a list of tags) added
* galaxy.yml 'readme' field added. The value is the path to the README file.
* galaxy.yml optional new fields 'repository', 'documentation', 'homepage', 'issues'
* galaxy.yml optional field 'license_file' added. It's value is a path
  to a file containing additional license information
* collection artifacts file manifest info is now in the generated FILES.json
* MANIFEST.json now includes path and sha256sum of new generated FILES.json
* Dependency solving version matching now supports the python-semanticversion style version specs
* Fixes and improvements for install of local collection artifacts.
  ie. `mazer install my_namespace-my_collection-1.2.3.tar.gz`
* Updates to the use Galaxy REST v2 API
* Updates to how SPDX data is loaded and used.
* SPDX data updated to 3.4-59-ga68ef3c

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
