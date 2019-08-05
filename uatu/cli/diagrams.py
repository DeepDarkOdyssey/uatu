import json
from collections import defaultdict
from functools import reduce
from typing import List, Union
from uatu.core.orm import File, Record, Pipeline, Experiment
from tabulate import tabulate


def file_summary(file: File) -> str:
    pred_ids = json.loads(file.predecessor_ids)
    succ_ids = json.loads(file.successor_ids)
    num_rows = max(len(pred_ids), len(succ_ids), 1)
    summary = f"[ ID: {file.id} PATH: {file.path} ]"
    header_length = len(summary)
    if len(pred_ids) > 0:
        header_length += 12
    if len(succ_ids) > 0:
        header_length += 12
    header = "─" * header_length
    rows = []
    for i in range(num_rows):
        if i == 0:
            row = summary
        else:
            row = " " * len(summary)

        if len(pred_ids) == 0:
            prefix = ""
        elif i > len(pred_ids) - 1:
            prefix = " " * 12
        elif len(pred_ids) == 1:
            prefix = f"{pred_ids[i]} ─➤─"
        elif i == 0:
            prefix = f"{pred_ids[i]} ─┬➤"
        elif i == len(pred_ids) - 1:
            prefix = f"{pred_ids[i]} ─┘ "
        else:
            prefix = f"{pred_ids[i]} ─┤ "

        if len(succ_ids) == 0:
            suffix = ""
        elif i > len(succ_ids) - 1:
            suffix = " " * 12
        elif len(succ_ids) == 1:
            suffix = f"─➤─ {succ_ids[i]}"
        elif i == 0:
            suffix = f"➤┬─ {succ_ids[i]}"
        elif i == len(succ_ids) - 1:
            suffix = f" └─ {succ_ids[i]}"
        else:
            suffix = f" ├─ {succ_ids[i]}"

        row = prefix + row + suffix
        rows.append(row)

    return header + "\n" + "\n".join(rows)


def file_details(files: List[File]):
    table = defaultdict(list)
    for file in files:
        table["ID"].append(file.id)
        table["PATH"].append(file.path)
        table["NODES"].append("\n".join(node.id for node in file.nodes))
        table["PREDECESSORS"].append(
            "\n".join(pred_id for pred_id in json.loads(file.predecessor_ids))
        )
        table["SUCCESSORS"].append(
            "\n".join(succ_id for succ_id in json.loads(file.successor_ids))
        )

    return tabulate(table, headers="keys", tablefmt="grid")


def node_summary(node: Record):
    pred_ids = json.loads(node.predecessor_ids)
    succ_ids = json.loads(node.successor_ids)
    num_rows = max(len(pred_ids), len(succ_ids), 1)
    summary = f"[ ID: {node.id} PATH: {node.file.path} COMMIT_ID: {node.commit_id[:3]}...{node.commit_id[-3:]}]"
    header_length = len(summary)
    if len(pred_ids) > 0:
        header_length += 12
    if len(succ_ids) > 0:
        header_length += 12
    header = "─" * header_length
    rows = []
    for i in range(num_rows):
        if i == 0:
            row = summary
        else:
            row = " " * len(summary)

        if len(pred_ids) == 0:
            prefix = ""
        elif i > len(pred_ids) - 1:
            prefix = " " * 12
        elif len(pred_ids) == 1:
            prefix = f"{pred_ids[i]} ─➤─"
        elif i == 0:
            prefix = f"{pred_ids[i]} ─┬➤"
        elif i == len(pred_ids) - 1:
            prefix = f"{pred_ids[i]} ─┘ "
        else:
            prefix = f"{pred_ids[i]} ─┤ "

        if len(succ_ids) == 0:
            suffix = ""
        elif i > len(succ_ids) - 1:
            suffix = " " * 12
        elif len(succ_ids) == 1:
            suffix = f"─➤─ {succ_ids[i]}"
        elif i == 0:
            suffix = f"➤┬─ {succ_ids[i]}"
        elif i == len(succ_ids) - 1:
            suffix = f" └─ {succ_ids[i]}"
        else:
            suffix = f" ├─ {succ_ids[i]}"

        row = prefix + row + suffix
        rows.append(row)

    return header + "\n" + "\n".join(rows)


def node_details(nodes: List[Record]) -> str:
    table = defaultdict(list)
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
    return tabulate(table, headers="keys", tablefmt="grid")


def pipeline_summary(pipeline: Pipeline) -> str:
    file_id_lists = json.loads(pipeline.file_id_lists)
    num_rows = reduce(max, map(len, file_id_lists))
    rows = []
    for i in range(num_rows):
        if i == 0:
            row = f"ID: {pipeline.id} ┃ FILE_IDS: "
        else:
            row = " " * 13 + "┃" + " " * 11
        for j, file_id_list in enumerate(file_id_lists):
            if len(file_id_list) > i:
                if len(file_id_list) == 1:
                    prefix = "➤──"
                    suffix = "──➤"
                elif i == 0:
                    prefix = "➤┬─"
                    suffix = "─┬➤"
                elif i == len(file_id_list) - 1:
                    prefix = " └─"
                    suffix = "─┘ "
                else:
                    prefix = " ├─"
                    suffix = "─┤ "

                if len(file_id_lists) == 1:
                    pass
                elif j == 0:
                    prefix = ""
                elif j == len(file_id_lists) - 1:
                    suffix = ""

                row += prefix + f" {file_id_list[i]} " + suffix
            else:
                row += " " * 16
        rows.append(row)
    max_row_len = reduce(max, map(len, rows))
    header = "─" * 13 + "┰" + "─" * (max_row_len - 14)
    return header + "\n" + "\n".join(rows)


def pipeline_details(pipelines: List[Pipeline]):
    table = defaultdict(list)
    for pipeline in pipelines:
        table["ID"].append(pipeline.id)
        table["DESCRIPTION"].append(pipeline.description)
        file_id_lists = json.loads(pipeline.file_id_lists)
        files = [" + ".join(file_id_list) for file_id_list in file_id_lists]
        files_string = ""
        for i, file in enumerate(files):
            if i == len(files) - 1:
                files_string += file
            else:
                files_string += file + "\n↓\n"

        table["PIPELINE(files)"].append(files_string)
        table["EXPRIMENTS"].append(
            "\n".join([expr.id for expr in pipeline.experiments])
        )

    return tabulate(table, headers="keys", tablefmt="grid", stralign="center")

