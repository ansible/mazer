import logging

from ansible_galaxy.models import migrate_role_context

log = logging.getLogger(__name__)


def test_init():
    role_path = "/dev/null/faux_role_path"
    output_path = "/dev/null/faux_output_path"
    mrc = migrate_role_context.MigrateRoleContext(role_path=role_path,
                                                  output_path=output_path)
    assert isinstance(mrc, migrate_role_context.MigrateRoleContext)
    assert mrc.role_path == role_path
    assert mrc.output_path == output_path


def test_repr():
    role_path = "/dev/null/faux_role_path"
    output_path = "/dev/null/faux_output_path"
    mrc = migrate_role_context.MigrateRoleContext(role_path=role_path,
                                                  output_path=output_path)

    r_mrc = repr(mrc)
    assert role_path in r_mrc
    assert output_path in r_mrc
