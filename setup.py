#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('CHANGELOG.rst') as changelog_file:
    changelog = changelog_file.read()

requirements = ['six',
                'PyYaml',
                'jinja2',
                'semantic_version',
                'yamlloader',
                # used for data classes
                # 18.1.0 introduces the 'factory' keyword
                'attrs>=18.1.0',
                ]

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest', ]

entry_points = {
    'console_scripts': ['mazer = ansible_galaxy_cli.__main__:main']
}

setup(
    entry_points=entry_points,
    install_requires=requirements,
    license="GPLv3",
    long_description=readme + '\n\n' + changelog,
    long_description_content_type='text/x-rst',
    include_package_data=True,
    keywords='mazer',
    packages=find_packages(include=['ansible_galaxy', 'ansible_galaxy_cli',
                                    'ansible_galaxy.*', 'ansible_galaxy_cli.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ansible/galaxy-cli',
    version='0.4.0',
    zip_safe=False,
)
