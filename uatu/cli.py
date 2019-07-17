import click
import subprocess
import json
from os import getcwd
from os.path import isfile, sep, join
from inspect import getmodule, stack
from typing import Tuple
from collections import defaultdict
from .init import check_uatu_initialized, initialize_uatu, clean_uatu, get_uatu_config
from .database import initialize_db, get_file, delete_file
from .git import (
    check_git_initialized,
    initialize_git,
    get_repo,
    get_changed_files,
    add_file,
)
from .utils import get_relative_path
from .database import initialize_db, get_node, get_all_files, get_all_nodes
from tabulate import tabulate


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


@cli.group("file")
@click.pass_context
def file_cli(ctx: click.Context):
    ctx.ensure_object(dict)
    initialized = check_git_initialized() and check_uatu_initialized()
    if not initialized:
        click.echo("This project has't been initialized yet. Please try `uatu init`.")
        click.get_current_context().abort()
    else:
        ctx.obj["sess"] = initialize_db(get_uatu_config()["database_file"])
        ctx.obj["repo"] = get_repo()


@file_cli.command("ls")
@click.argument("files", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def file_ls(ctx: click.Context, files: Tuple[str]):
    if files:
        for file_path in files:
            f = get_file(ctx.obj["sess"], file_path)
            info = ""
            if len(f.predecessor_ids) > 2:
                info += f"{f.predecessor_ids} >>> "
            info += f"|| id: {f.id} -- path: {f.path} ||"
            if len(f.successor_ids) > 2:
                info += f" >>> {f.successor_ids}"
            click.echo(info)

    else:
        files = get_all_files(ctx.obj["sess"])
        for f in files:
            info = ""
            if len(f.predecessor_ids) > 2:
                info += f"{f.predecessor_ids} >>> "
            info += f"|| id: {f.id} -- path: {f.path} ||"
            if len(f.successor_ids) > 2:
                info += f" >>> {f.successor_ids}"
            click.echo(info)


@file_cli.command("show")
@click.argument("file_ids", nargs=-1, type=str)
@click.pass_context
def file_show(ctx: click.Context, file_ids: Tuple[str]):
    table = defaultdict(list)
    if file_ids:
        for file_id in file_ids:
            f = get_file(ctx.obj["sess"], file_id=file_id)
            table["ID"].append(f.id)
            table["PATH"].append(f.path)
            table["NODES"].append("\n".join(node.id for node in f.nodes))
            table["PREDECESSORS"].append(
                "\n".join(pred_id for pred_id in json.loads(f.predecessor_ids))
            )
            table["SUCCESSORS"].append(
                "\n".join(succ_id for succ_id in json.loads(f.successor_ids))
            )

    else:
        files = get_all_files(sess=ctx.obj["sess"])
        for f in files:
            table["ID"].append(f.id)
            table["PATH"].append(f.path)
            table["NODES"].append("\n".join(node.id for node in f.nodes))
            table["PREDECESSORS"].append(
                "\n".join(pred_id for pred_id in json.loads(f.predecessor_ids))
            )
            table["SUCCESSORS"].append(
                "\n".join(succ_id for succ_id in json.loads(f.successor_ids))
            )
    click.echo(tabulate(table, headers="keys", tablefmt="grid"))


@file_cli.command("del")
@click.argument("file_ids", nargs=-1, type=str)
@click.option("--yes", "-y", is_flag=True)
@click.pass_context
def file_delete(ctx: click.Context, file_ids: Tuple[str], yes: bool):
    if file_ids:
        for file_id in file_ids:
            if not yes:
                click.confirm(
                    f"Are you sure you want to delete file {file_id}?\nThis will "
                    "delete every node, pipeline and experiment attached to it!"
                , default=False, abort=True)
            delete_file(ctx.obj["sess"], file_id=file_id)
    else:
        files = get_all_files(ctx.obj['sess'])
        for file_ in files:
            if not yes:
                click.confirm(
                    f"Are you sure you want to delete file {file_.id}?\nThis will "
                    "delete every node, pipeline and experiment attached to it!"
                , default=False, abort=True)
            delete_file(ctx.obj["sess"], file=file_)


@cli.command("node")
@click.option("--list", "-ls", "list_", is_flag=True)
def node_cli(list_):
    if list_:
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

