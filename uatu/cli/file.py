import json
import click
from typing import Tuple
from collections import defaultdict
from tabulate import tabulate
from .base import cli
from uatu.database import get_file, get_all_files, delete_file


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