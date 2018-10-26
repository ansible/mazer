import logging

from ansible_galaxy import exceptions

log = logging.getLogger(__name__)


def repo_url_to_repo_name(repo_url):
    # gets the role name out of a repo like
    # http://git.example.com/repos/repo.git" => "repo"

    if '://' not in repo_url and '@' not in repo_url:
        return repo_url
    trailing_path = repo_url.split('/')[-1]
    if trailing_path.endswith('.git'):
        trailing_path = trailing_path[:-4]
    if trailing_path.endswith('.tar.gz'):
        trailing_path = trailing_path[:-7]
    if ',' in trailing_path:
        trailing_path = trailing_path.split(',')[0]
    return trailing_path


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
