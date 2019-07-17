import click
import subprocess
from os import getcwd
from typing import Tuple
from uatu.git import (
    check_git_initialized,
    initialize_git,
    get_repo,
    get_changed_files,
    add_file,
)
from uatu.init import (
    check_uatu_initialized,
    initialize_uatu,
    get_uatu_config,
    clean_uatu,
)
from uatu.database import initialize_db, get_node
from uatu.utils import get_relative_path


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
@click.option("--append", "-a", is_flag=True, default=False)
@click.pass_context
def watch(ctx: click.Context, files: Tuple[str], message: str, append: bool):
    repo = ctx.obj["repo"]
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
        get_node(ctx.obj["sess"], commit_id, relpath)
    click.echo(f"Uatu is now watching {changed_files}, commit_id: {commit_id}")


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
