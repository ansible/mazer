
import logging

from ansible_galaxy.models import content

log = logging.getLogger(__name__)


def test_content_type_dir_map():
    assert isinstance(content.CONTENT_TYPE_DIR_MAP, dict)


def test_content_type_dir_map_items():
    for content_type in content.CONTENT_TYPES:
        assert content_type in content.CONTENT_TYPE_DIR_MAP
        expected = '%ss' % content_type
        assert content.CONTENT_TYPE_DIR_MAP[content_type] == expected

    assert 'role' in content.CONTENT_TYPES
