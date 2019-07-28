import click
import subprocess
from os import getcwd
from typing import Tuple
from sqlalchemy.orm import Session
from git import Repo
from ..core.git import(
    check_git_initialized,
    initialize_git,
    get_repo,
    get_changed_files,
    add_file,
    get_last_commit,
    need_commit,
)
from ..core.init import (
    check_uatu_initialized,
    initialize_uatu,
    get_uatu_config,
    clean_uatu,
)
from ..core.database import initialize_db, get_node, get_file
from ..core.utils import get_relative_path
from .node import node_cli
from .file import file_cli
from .pipeline import pipeline_cli


@click.group()
@click.pass_context
def cli(ctx: click.Context):
    ctx.ensure_object(dict)
    initialized = check_git_initialized() and check_uatu_initialized()
    if not initialized:
        click.echo("This project has't been initialized yet. Please try `uatu init`.")
        click.get_current_context().abort()
    else:
        ctx.obj["sess"] = initialize_db(get_uatu_config()["database_file"])
        ctx.obj["repo"] = get_repo()


@cli.command()
@click.option("--config_file", type=click.Path(exists=True, dir_okay=False))
def init(config_file):
    if not check_git_initialized():
        click.confirm(
            "This folder is not a git repo, do you want to initialize git?",
            default=False,
            abort=True,
        )
        initialize_git()
    click.echo("Git repo is already initialized")

    if check_uatu_initialized():
        click.confirm(
            "Uatu has already been watching this project, "
            "do you still want to initialize?",
            default=False,
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
@click.option("--amend", "-a", is_flag=True, default=False)
@click.pass_context
def watch(ctx: click.Context, files: Tuple[str], message: str, amend: bool):
    repo: Repo = ctx.obj["repo"]
    sess: Session = ctx.obj["sess"]
    all_changed_files = get_changed_files(repo)

    files2watch = set()
    for file_path in files:
        rel_path = get_relative_path(file_path, repo.working_dir)
        last_commit_id = get_last_commit(repo, file_path)
        if not last_commit_id:
            files2watch.add(rel_path)
        elif rel_path in all_changed_files:
            files2watch.add(rel_path)
        else:
            file_ = get_file(sess, file_path=file_path, create=False)
            if file_:
                node = get_node(sess, file_path=file_.path, create=False)
                if not node:
                    files2watch.add(rel_path)
            else:
                files2watch.add(rel_path)

    if need_commit(repo):
        if amend:
            if not message:
                repo.git.commit("--amend", "--no-edit")
            else:
                repo.git.commit("--amend", "-m", message)
        else:
            if not message:
                message = click.prompt("Please enter a message for `git commit`")
            repo.git.commit("-m", message)
    else:
        click.echo(f"None of these files has been modified")

    if files2watch:
        commit_id = get_last_commit(repo)
        for file_path in files2watch:
            get_node(sess, file_path=file_path, commit_id=commit_id)
        click.echo(f"Uatu is now watching {list(files2watch)}, commit_id: {commit_id}")


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("script", type=str, nargs=1, required=True)
@click.argument("args", type=str, nargs=-1)
@click.option("--module", "-m", is_flag=True)
def run(script, args, module):
    if module:
        subprocess.run("python -m " + " ".join([script] + list(args)), shell=True)
    else:
        if not script.endswith(".py"):
            click.echo("Uatu only support python scripts!")
            click.get_current_context().abort()
        else:
            print("running python script")
            subprocess.run("python " + " ".join([script] + list(args)), shell=True)


cli.add_command(file_cli)
cli.add_command(node_cli)
cli.add_command(pipeline_cli)