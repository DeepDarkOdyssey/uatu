import json
import click
from typing import Tuple, NoReturn
from functools import reduce
from .base import cli
from uatu.orm import Pipeline
from uatu.database import get_pipeline, get_all_pipelines


@cli.group("pipeline")
@click.pass_context
def pipeline_cli(ctx: click.Context):
    pass


@pipeline_cli.command("ls")
@click.argument("pipeline_ids", nargs=-1, type=str)
@click.pass_context
def pipeline_ls(ctx: click.Context, pipeline_ids: Tuple[str]) -> NoReturn:
    if pipeline_ids:
        for pipeline_id in pipeline_ids:
            pipeline = get_pipeline(ctx.obj["sess"], pipeline_id=pipeline_id)
            diagram = get_diagram(pipeline)
            print(diagram)
    else:
        pipelines = get_all_pipelines(ctx.obj['sess'])
        for pipeline in pipelines:
            diagram = get_diagram(pipeline)
            print(diagram)


def get_diagram(pipeline: Pipeline) -> str:
    file_id_lists = json.loads(pipeline.file_id_lists)
    num_rows = reduce(max, map(len, file_id_lists))
    rows = []
    for i in range(num_rows):
        if i == 0:
            row = f'ID: {pipeline.id} ┃ FILE_IDS: '
        else:
            row = ' ' * 13 + '┃' + ' ' * 11
        for j, file_id_list in enumerate(file_id_lists):
            if len(file_id_list) > i:
                if len(file_id_list) == 1:
                    prefix = '➤──'
                    suffix = '──➤'
                elif (i == 0) & (len(file_id_list) > 1):
                    prefix = '─┬─'
                    suffix = '─┬─'
                elif i == len(file_id_list) - 1:
                    prefix = ' └─'  
                    suffix = '─┘ '
                else:
                    prefix = ' ├─' 
                    suffix = '─┤ '
                
                if len(file_id_lists) == 1:
                    pass
                elif j == 0:
                    prefix = ''
                elif j == len(file_id_lists) - 1:
                    suffix = ''

                row += prefix + f' {file_id_list[i]} ' + suffix
            else:
                row += ' ' * 16
        rows.append(row)
    max_row_len = reduce(max, map(len, rows))
    header = '─' * 13 + '┰' + '─' * (max_row_len - 14)
    rows.insert(0, header)
    return '\n'.join(rows)

