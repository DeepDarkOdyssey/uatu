import json
import click
from typing import Tuple
from collections import defaultdict
from .base import cli
from .diagrams import file_details, file_summary
from uatu.core.database import get_file, get_all_files, delete_file


@cli.group("file")
@click.pass_context
def file_cli(ctx: click.Context):
    pass


@file_cli.command("ls")
@click.argument("files", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.pass_context
def file_ls(ctx: click.Context, files: Tuple[str]):
    if files:
        for file_path in files:
            file_ = get_file(ctx.obj["sess"], file_path=file_path, create=False)
            if not file_:
                click.echo(f"{file_path} is not under Uatu's watch!")
            else:
                click.echo(file_summary(file_))

    else:
        files = get_all_files(ctx.obj["sess"])
        for file_ in files:
            click.echo(file_summary(file_))


@file_cli.command("show")
@click.argument("file_ids", nargs=-1, type=str)
@click.pass_context
def file_show(ctx: click.Context, file_ids: Tuple[str]):
    if file_ids:
        files = []
        for file_id in file_ids:
            file_ = get_file(ctx.obj["sess"], file_id=file_id)
            if not file_:
                click.echo(f"{file_id} is not a Uatu's file id")
            else:
                files.append(file_)

    else:
        files = get_all_files(sess=ctx.obj["sess"])
    click.echo(file_details(files))


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
                    "delete every node, pipeline and experiment attached to it!",
                    default=False,
                    abort=True,
                )
            delete_file(ctx.obj["sess"], file_id=file_id)
    else:
        files = get_all_files(ctx.obj["sess"])
        for file_ in files:
            if not yes:
                click.confirm(
                    f"Are you sure you want to delete file {file_.id}?\nThis will "
                    "delete every node, pipeline and experiment attached to it!",
                    default=False,
                    abort=True,
                )
            delete_file(ctx.obj["sess"], file=file_)
