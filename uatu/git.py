from os import getcwd
from os.path import dirname, join, exists, getsize
from git import Repo
from git.refs.log import RefLog
from .utils import get_relative_path
import click



def get_tracked_files(repo: Repo) -> list:
    return repo.git.ls_files().split()


def git_add(repo: Repo, file_path: str, limited_size=1000000):
    tracked_files = get_tracked_files(repo)
    if file_path in tracked_files:
        print(f'{file_path} has already been added to git repo')
    else:
        file_size = getsize(file_path)
        if file_size >= limited_size:
            repo.git.execute(['git', 'lfs', 'track', file_path])
            repo.git.execute(['git', 'add', file_path])
        else:
            repo.git.execute(['git', 'add', file_path])


def get_ignore_file(repo_dir) -> str:
    ignore_file = join(repo_dir, '.gitignore')
    if not exists(ignore_file):
        f = open(ignore_file, 'w')
        f.close()

    return ignore_file


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
    repo = Repo.init(repo_dir)
    ignore_file = get_ignore_file(repo_dir)
    add_git_ignore(ignore_file, '.uatu/')

    attributes_file = join(repo_dir, '.gitattributes')
    if not exists(attributes_file):
        f = open(attributes_file, 'w')
        f.close()
    git_add(repo, get_relative_path(ignore_file, repo_dir))
    git_add(repo, get_relative_path(attributes_file, repo_dir))

    return repo