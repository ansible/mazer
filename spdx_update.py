#!/usr/bin/python

import argparse
import json
import logging
import sys

log = logging.getLogger(__name__)


def load_spdx(file_object):
    data = json.load(file_object)
    return data


def build_short_list(license_data):
    licenses = {}

    for lic in license_data['licenses']:
        lid = lic['licenseId']
        licenses[lid] = {'deprecated': lic['isDeprecatedLicenseId']}
    return licenses


def json_dumps_license_data(short_license_data):
    dict_buf = json.dumps(short_license_data,
                          indent=4,
                          sort_keys=True,
                          separators=(',', ':'))
    log.debug('dict_buf: %s', dict_buf)
    return dict_buf


def main(argv):
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument('input', help='The SPDX license json file input',
                        type=argparse.FileType())
    args = parser.parse_args(argv)

    log.debug('args: %s', args)

    data = load_spdx(args.input)
    short_data = build_short_list(data)

    buf = json_dumps_license_data(short_data)

    print(buf)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
