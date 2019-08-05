import json
import click
from typing import Tuple
from collections import defaultdict
from .diagrams import node_summary, node_details
from uatu.core.database import get_node, get_all_nodes, delete_node
from uatu.core.utils import get_relative_path


@click.group("node")
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
            if node:
                click.echo(node_summary(node))
            else:
                click.echo(f'Record {node_id} not exists!')

    else:
        nodes = get_all_nodes(ctx.obj["sess"])
        for node in nodes:
            click.echo(node_summary(node))


@node_cli.command("show")
@click.argument("node_ids", nargs=-1, type=str)
@click.pass_context
def node_show(ctx: click.Context, node_ids: Tuple[str]):
    if node_ids:
        nodes = []
        for node_id in node_ids:
            node = get_node(ctx.obj["sess"], node_id=node_id, create=False)
            if node:
                nodes.append(node)
            else:
                click.echo(f'Record {node_id} not exists!')

    else:
        nodes = get_all_nodes(sess=ctx.obj["sess"])
    click.echo(node_details(nodes))


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
