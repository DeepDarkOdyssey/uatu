import json
import click
from typing import Tuple
from collections import defaultdict
from .base import cli
from .diagrams import node_summary
from uatu.core.database import get_node, get_all_nodes, delete_node
from uatu.core.utils import get_relative_path


@cli.group("node")
@click.pass_context
def node_cli(ctx: click.Context):
    pass


@node_cli.command("ls")
@click.argument("node_ids", nargs=-1, type=str)
@click.pass_context
def node_ls(ctx: click.Context, node_ids: Tuple[str]):
    if node_ids:
        for node_id in node_ids:
            node = get_node(ctx.obj["sess"], node_id=node_id)
            info = ""
            if len(node.predecessor_ids) > 2:
                info += f"{node.predecessor_ids} >>> "
            info += f"|| id: {node.id} -- file: {node.file.path} -- commit id: {node.commit_id} ||"
            if len(node.successor_ids) > 2:
                info += f" >>> {node.successor_ids}"
            click.echo(info)

    else:
        nodes = get_all_nodes(ctx.obj["sess"])
        for node in nodes:
            info = ""
            if len(node.predecessor_ids) > 2:
                info += f"{node.predecessor_ids} >>> "
            info += f"|| id: {node.id} -- file: {node.file.path} -- commit id: {node.commit_id} ||"
            if len(node.successor_ids) > 2:
                info += f" >>> {node.successor_ids}"
            click.echo(info)


@node_cli.command("show")
@click.argument("node_ids", nargs=-1, type=str)
@click.pass_context
def file_show(ctx: click.Context, node_ids: Tuple[str]):
    table = defaultdict(list)
    if node_ids:
        for node_id in node_ids:
            node = get_node(ctx.obj["sess"], node_id=node_id)
            table["ID"].append(node.id)
            table["FILE"].append(node.file.path)
            table["FILE_ID"].append(node.file_id)
            table["COMMIT_ID"].append(node.commit_id)
            table["PREDECESSORS"].append(
                "\n".join(pred_id for pred_id in json.loads(node.predecessor_ids))
            )
            table["SUCCESSORS"].append(
                "\n".join(succ_id for succ_id in json.loads(node.successor_ids))
            )

    else:
        nodes = get_all_nodes(sess=ctx.obj["sess"])
        for node in nodes:
            table["ID"].append(node.id)
            table["FILE"].append(node.file.path)
            table["FILE_ID"].append(node.file_id)
            table["COMMIT_ID"].append(node.commit_id)
            table["PREDECESSORS"].append(
                "\n".join(pred_id for pred_id in json.loads(node.predecessor_ids))
            )
            table["SUCCESSORS"].append(
                "\n".join(succ_id for succ_id in json.loads(node.successor_ids))
            )
    click.echo(tabulate(table, headers="keys", tablefmt="grid"))


@node_cli.command("del")
@click.argument("node_ids", nargs=-1, type=str)
@click.option("--yes", "-y", is_flag=True)
@click.pass_context
def node_delete(ctx: click.Context, node_ids: Tuple[str], yes: bool):
    if node_ids:
        for node_id in node_ids:
            if not yes:
                click.confirm(
                    f"Are you sure you want to delete node {node_id}?\n"
                    "This will delete every experiment attached to it!",
                    default=False,
                    abort=True,
                )
            delete_node(ctx.obj["sess"], node_id=node_id)
    else:
        nodes = get_all_nodes(ctx.obj["sess"])
        for node in nodes:
            if not yes:
                click.confirm(
                    f"Are you sure you want to delete node {node_id}?\n"
                    "This will delete every experiment attached to it!",
                    default=False,
                    abort=True,
                )
            delete_node(ctx.obj["sess"], node=node)
