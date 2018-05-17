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


def repo_name_to_content_name(repo_name):
    '''For a repo name like 'ansible-role-mystuff', return "mystuff"

    For a repo name like 'mystuff', return 'mystuff'.

    aka, strip the 'ansible-role-' prefix.'''

    if repo_name.startswith('ansible-role-'):
        return repo_name[len('ansible-role-'):]

    return repo_name


# TODO: test cases
# TODO: class/type for a content spec
def parse_content_name(content_name):
    "split a full content_name into username, repo_name, content_name"

    repo_name = None
    try:
        parts = content_name.split(".")
        user_name = parts[0]
        if len(parts) > 2:
            repo_name = parts[1]
            content_name = '.'.join(parts[2:])
        else:
            content_name = '.'.join(parts[1:])
    except Exception as e:
        log.exception(e)
        raise exceptions.GalaxyClientError("Invalid content name (%s). Specify content as format: username.contentname" % content_name)

    return (user_name, repo_name, content_name)
