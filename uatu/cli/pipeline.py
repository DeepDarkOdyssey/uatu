import json
import click
from typing import Tuple, NoReturn
from functools import reduce
from .diagrams import pipeline_summary, pipeline_details
from uatu.core.orm import Pipeline
from uatu.core.database import get_pipeline, get_all_pipelines


@click.group("pipeline")
@click.pass_context
def pipeline_cli(ctx: click.Context):
    pass


@pipeline_cli.command("ls")
@click.argument("pipeline_ids", nargs=-1, type=str)
@click.pass_context
def pipeline_ls(ctx: click.Context, pipeline_ids: Tuple[str]) -> NoReturn:
    if pipeline_ids:
        for pipeline_id in pipeline_ids:
            pipeline = get_pipeline(
                ctx.obj["sess"], pipeline_id=pipeline_id, create=False
            )
            if pipeline:
                click.echo(pipeline_summary(pipeline))
            else:
                click.echo(f"Pipeline '{pipeline_id}' not exists!")
    else:
        pipelines = get_all_pipelines(ctx.obj["sess"])
        for pipeline in pipelines:
            click.echo(pipeline_summary(pipeline))


@pipeline_cli.command("show")
@click.argument("pipeline_ids", nargs=-1, type=str)
@click.pass_context
def pipeline_show(ctx: click.Context, pipeline_ids: Tuple[str]) -> NoReturn:
    if pipeline_ids:
        pipelines = []
        for pipeline_id in pipeline_ids:
            pipeline = get_pipeline(ctx.obj["sess"], pipeline_id=pipeline_id)
            if pipeline:
                pipelines.append(pipeline)
            else:
                click.echo(f"Pipeline '{pipeline_id}' not exists!")

        click.echo(pipeline_details(pipelines))
    else:
        pipelines = get_all_pipelines(ctx.obj["sess"])
    click.echo(pipeline_details(pipelines))

