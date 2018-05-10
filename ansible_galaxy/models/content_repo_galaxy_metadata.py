

# TODO: model for the data in a ansible-galaxy.yml in a galaxy content repo
# ie, the object(s) build from a yaml like:

_sample = '''
---
# meta_version: ‘0.1’  # metadata format version
meta_version: '0.1'  # metadata format version
modules:
 - path: playbooks/modules/*
 - path: modules/galaxyfile_sample_module.py
   dependencies:
    - src: module_utils/*
 - path: modules/module_c.py
   dependencies:
    - src: git+https://github.com/maxamillion/test-galaxy-content
      type: module_utils
'''


class ContentRepoGalaxyMetadata(object):
    pass
