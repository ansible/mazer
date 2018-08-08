#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['six',
                'PyYaml',
                'jinja2',
                'semver',
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
    author="Red Hat, Inc.",
    author_email='info@ansible.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
    description="Ansible content manager",
    entry_points=entry_points,
    install_requires=requirements,
    license="GPLv3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='mazer',
    name='mazer',
    packages=find_packages(include=['ansible_galaxy', 'ansible_galaxy_cli',
                                    'ansible_galaxy.*', 'ansible_galaxy_cli.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/ansible/galaxy-cli',
    version='0.2.1',
    zip_safe=False,
)
