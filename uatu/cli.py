import click
import subprocess
from os import getcwd
from os.path import isfile, sep, join
from inspect import getmodule, stack
from .init import check_uatu_initialized, initialize_uatu, clean_uatu, get_uatu_config
from .database import initialize_db
from .git import (
    check_git_initialized,
    initialize_git,
    get_repo,
    get_changed_files,
    add_file,
)
from .utils import get_relative_path
from .database import initialize_db, get_node, get_all_files, get_all_nodes


@click.group()
def cli():
    pass


@cli.command()
@click.option("--config_file", type=click.Path(exists=True, dir_okay=False))
def init(config_file):
    if not check_git_initialized():
        click.confirm(
            "This folder is not a git repo, do you want to initialize git?", abort=True
        )
        initialize_git()
    click.echo("Git repo is already initialized")

    if check_uatu_initialized():
        click.confirm(
            "Uatu is watching this project, do you still want to initialize?",
            abort=True,
        )
    initialize_uatu(user_config=config_file)
    click.echo("Uatu has arrived!")


@cli.command()
@click.option(
    "--dir_path", "-d", type=click.Path(exists=True, file_okay=False), default=getcwd()
)
def clean(dir_path):
    clean_uatu(dir_path)


@cli.command()
@click.argument("files", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.option("--message", "-m")
@click.option("--append", "-a", is_flag=True, default=False)
def watch(files, message: str, append: bool):
    if not check_git_initialized() or not check_uatu_initialized():
        click.echo(
            "This project has't been initialized yet. \
            Please try `uatu init`."
        )
        click.get_current_context().abort()
    repo = get_repo()
    sess = initialize_db(get_uatu_config()["database_file"])
    all_changed_files = get_changed_files(repo)

    changed_files = []
    for file_path in files:
        relpath = get_relative_path(file_path)
        if relpath in all_changed_files:
            changed_files.append(relpath)
            add_file(repo, file_path)
    if len(changed_files) > 0:
        if not message:
            message = click.prompt("Please enter a message for `git commit`")
        if append:
            repo.git.commit("-m", message, "--amend")
        else:
            repo.git.commit("-m", message)
    else:
        click.echo(f"None of these files has been modified")

    commit_id = str(next(repo.iter_commits()))
    for relpath in changed_files:
        get_node(sess, commit_id, relpath)
    click.echo(f"Uatu is now watching {changed_files}, commit_id: {commit_id}")


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument(
    "script", type=str, nargs=1, required=True
)
@click.argument("args", type=str, nargs=-1)
@click.option('--module', '-m', is_flag=True)
def run(script, args, module):
    if module:
        subprocess.run('python -m ' + ' '.join([script] + list(args)), shell=True)
    else:
        if not script.endswith('.py'):
            click.echo("Uatu only support python scripts!")
            click.get_current_context().abort()
        else:
            print('running python script')
            subprocess.run('python ' +  ' '.join([script] + list(args)), shell=True)


@cli.command("file")
def file_cli():
    sess = initialize_db(get_uatu_config()["database_file"])
    files = get_all_files(sess)
    for f in files:
        click.echo(f"ID: {f.id} ------- PATH: {f.path}")


@cli.command("node")
def node_cli():
    sess = initialize_db(get_uatu_config()["database_file"])
    nodes = get_all_nodes(sess)
    for node in nodes:
        click.echo(
            f"ID: {node.id[:3]}...{node.id[-3:]}, path: {node.file.path}, "
            f"COMMITID: {node.commit_id[:3]}...{node.commit_id[-3:]}"
        )


@cli.command("experiment")
def experiment_cli():
    click.echo("using experiment CLI")

