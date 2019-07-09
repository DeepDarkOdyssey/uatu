import json
import click
from typing import Union, List
from copy import deepcopy
from git import Repo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from .orm import Base, File, Pipeline, Node, Experiment
from .utils import id_generator
from .git import get_file_last_commit


def initialize_db(db_file: str):
    engine = create_engine(f'sqlite:///{db_file}?check_same_thread=False',
                           echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def add_edge(sess: Session, parent: Union[File, Node],
             child: Union[File, Node]):
    parent_child_ids = deepcopy(parent.child_ids)
    parent_child_ids.add(child.id)
    parent.child_ids = parent_child_ids
    child_parent_ids = deepcopy(child.parent_ids)
    child_parent_ids.add(parent.id)
    child.parent_ids = child_parent_ids
    sess.commit()


def get_file(sess: Session, file_path: str) -> File:
    file_ = sess.query(File).filter_by(path=file_path).first()
    if file_:
        click.echo(f'File {file_.id} {file_.path} exists')
    else:
        file_ = File(id=id_generator(8, 'file'), path=file_path)
        sess.add(file_)
        sess.commit()
    return file_


def get_all_files(sess: Session) -> list:
    return sess.query(File).all()


def get_pipeline(sess: Session,
                 file_paths: List[Union[str, List[str]]]) -> Pipeline:
    pipeline = sess.query(Pipeline).filter_by(pipeline=file_paths).first()
    if pipeline:
        print(f'Pipeline {pipeline.id} [{" --> ".join(file_paths)}] exists')
    else:
        for i in range(len(file_paths) - 1):
            if type(file_paths[i]) == list and type(file_paths[i + 1]) == list:
                raise TypeError('Something wrong with this pipeline')
            if type(file_paths[i]) == list:
                for file_path in file_paths[i]:
                    parent_file = get_file(sess, file_path)
                    child_file = get_file(sess, file_paths[i + 1])
                    add_edge(sess, parent_file, child_file)
            elif type(file_paths[i + 1]) == list:
                for file_path in file_paths[i + 1]:
                    parent_file = get_file(sess, file_paths[i])
                    child_file = get_file(sess, file_path)
                    add_edge(sess, parent_file, child_file)
            else:
                parent_file = get_file(sess, file_paths[i])
                child_file = get_file(sess, file_paths[i + 1])
                add_edge(sess, parent_file, child_file)

        pipeline = Pipeline(id=id_generator(8, 'pipeline'),
                            pipeline=file_paths)
        sess.add(pipeline)
        sess.commit()
    return pipeline


def get_node(sess: Session, commit_id: str, file_path: str) -> Node:
    node_file = get_file(sess, file_path)
    node = sess.query(Node).filter_by(file_id=node_file.id,
                                      commit_id=commit_id).first()
    if node:
        click.echo(f'Node {node.id} {node.file.path} exists')
    else:
        node = Node(id=id_generator(16, 'node'),
                    file_id=node_file.id,
                    commit_id=commit_id)
        sess.add(node)
        sess.commit()
    return node


def get_all_nodes(sess: Session) -> list:
    return sess.query(Node).all()


def get_experiment(sess: Session,
                   repo: Repo,
                   file_paths: List,
                   config: dict = None,
                   hparams: dict = None):
    config = '{}' if config is None else json.dumps(config)
    hparams = '{}' if hparams is None else json.dumps(hparams)
    pipeline = get_pipeline(sess, file_paths)

    nodes, node_ids = [], []
    for file_path in file_paths:
        if type(file_path) == list:
            node, node_id = [], []
            for sub_file in file_path:
                sub_file_commit_id = get_file_last_commit(repo, sub_file)
                sub_node = get_node(sess, sub_file_commit_id, sub_file)
                node.append(sub_node)
                node_id.append(sub_node.id)
            nodes.append(node)
            node_ids.append(node_id)
        else:
            file_commit_id = get_file_last_commit(repo, file_path)
            node = get_node(sess, file_commit_id, file_path)
            nodes.append(node)
            node_ids.append(node.id)

    experiment = sess.query(Experiment).filter_by(node_ids=node_ids,
                                                  config=config,
                                                  hparams=hparams).first()
    if experiment:
        print(f'Experiment {experiment.id} [{" --> ".join(node_ids)}] exists')
    else:
        for i in range(len(nodes) - 1):
            if type(nodes[i]) == list:
                for node in nodes[i]:
                    parent_node = node
                    child_node = nodes[i + 1]
                    add_edge(sess, parent_node, child_node)
            elif type(nodes[i + 1]) == list:
                for node in nodes[i + 1]:
                    parent_node = nodes[i]
                    child_node = node
                    add_edge(sess, parent_node, child_node)
            else:
                parent_node = nodes[i]
                child_node = nodes[i + 1]
                add_edge(sess, parent_node, child_node)

        experiment = Experiment(id=id_generator(16, 'experiment'),
                                pipeline_id=pipeline.id,
                                node_ids=node_ids,
                                config=config,
                                hparams=hparams)
        sess.add(experiment)
        sess.commit()
    return experiment

if __name__ == "__main__":
    sess = initialize_db('./.uatu/uatu.db')
    get_all_nodes(sess)