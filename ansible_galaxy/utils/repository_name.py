import logging

from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


# TODO: test cases
def parse_repository_name(name):
    "split a full repository_name into namespace, repo_name, content_name"

    repo_name = None
    try:
        parts = name.split(".")
        user_name = parts[0]
        if len(parts) > 2:
            repo_name = parts[1]
            name = '.'.join(parts[2:])
        else:
            name = '.'.join(parts[1:])
    except Exception as e:
        log.exception(e)
        raise exceptions.GalaxyClientError("Invalid content name (%s). Specify content as format: username.contentname" % name)

    return (user_name, repo_name, name)
