from uatu.core.init import initialize_db, get_uatu_config
from uatu.core.database import get_all_files, get_all_nodes, get_all_pipelines
from uatu.cli.diagrams import (
    file_summary,
    file_details,
    node_summary,
    node_details,
    pipeline_summary,
    pipeline_details,
)

sess = initialize_db(get_uatu_config()["database_file"])


def test_file_diagrams():
    files = get_all_files(sess)
    print('\nFile summaries:')
    for file_ in files:
        print(file_summary(file_))
    print('\nFile details:')
    print(file_details(files))


def test_node_diagrams():
    nodes = get_all_nodes(sess)
    print('\nNode summaries:')
    for node in nodes:
        print(node_summary(node))
    print('\nNode details:')
    print(node_details(nodes))


def test_pipeline_diagrams():
    pipelines = get_all_pipelines(sess)
    print('\nPipeline summaries')
    for pipeline in pipelines:
        print(pipeline_summary(pipeline))
    print('\nPipeline details')
    print(pipeline_details(pipelines))
