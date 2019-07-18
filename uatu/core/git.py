from typing import List, Union
from os import getcwd
from os.path import dirname, join, exists, getsize
import git
from git import Repo
from git.refs.log import RefLog
from .utils import get_relative_path
import click

# TODO: review git functions

def get_repo(repo_dir: str = getcwd()) -> Repo:
    return Repo.init(repo_dir)


def get_tracked_files(repo: Repo) -> List[str]:
    return repo.git.ls_files().split()


def get_changed_files(repo: Repo) -> List[str]:
    # FIXME: reconsider what kind of files should be exposed
    file_list = repo.git.status('-s').split('\n')
    changed_files = []
    for status_file in file_list:
        status, path = status_file.split()
        if status in ['MM', 'M', 'A']:
            changed_files.append(path)
    return changed_files


def need_commit(repo: Repo) -> bool:
    file_list = repo.git.status('-s').split('\n')
    for status_file in file_list:
        status, _ = status_file.split()
        if status == 'A':
            return True
    return False


def create_ignore_file(repo_dir: str) -> str:
    ignore_file = join(repo_dir, '.gitignore')
    if not exists(ignore_file):
        f = open(ignore_file, 'w')
        f.close()

    return ignore_file


def get_last_commit(repo: Repo, file_path: str='') -> Union[str, None]:
    if file_path:
        file_path = get_relative_path(file_path, repo.working_dir)
    try:
        commit_id = str(next(repo.iter_commits(paths=file_path)))
    except StopIteration:
        commit_id = None
    return commit_id


def add_file(repo: Repo, file_path: str, limited_size=1000000) -> bool:
    file_path = get_relative_path(file_path, repo.working_dir)
    changed_files = get_changed_files(repo)
    if file_path in changed_files:
        file_size = getsize(file_path)
        if file_size >= limited_size:
            repo.git.execute(['git', 'lfs', 'track', file_path])
            repo.git.execute(['git', 'add', file_path])
        else:
            repo.git.execute(['git', 'add', file_path])
        return True
    else:
        return False


def add_git_ignore(ignore_file: str, path: str):
    with open(ignore_file) as f:
        lines = [line.strip() for line in f]
    if path not in lines:
        with open(ignore_file, 'a') as f:
            f.write(path + '\n')


def check_git_initialized(repo_dir: str = getcwd()) -> bool:
    git_dir = join(repo_dir, '.git')
    if not exists(git_dir):
        click.echo('Dir .git not exists')
        return False
    if not exists(join(repo_dir, '.gitignore')):
        click.echo('File .gitignore not exists')
        return False
    if not exists(join(repo_dir, '.gitattributes')):
        click.echo('File .gitattributes not exists')
        return False
    return True


def initialize_git(repo_dir: str = getcwd()) -> Repo:
    repo = get_repo(repo_dir)
    ignore_file = create_ignore_file(repo_dir)
    add_git_ignore(ignore_file, '.uatu/')

    attributes_file = join(repo_dir, '.gitattributes')
    if not exists(attributes_file):
        f = open(attributes_file, 'w')
        f.close()
    add_file(repo, ignore_file)
    add_file(repo, attributes_file)
    repo.commit('Initialize uatu')

    return repo