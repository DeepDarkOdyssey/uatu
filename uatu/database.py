import json
import click
from typing import Union, List, Optional, NoReturn
from copy import deepcopy
from git import Repo
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from .orm import Base, File, Pipeline, Node, Experiment
from .utils import id_generator, get_relative_path
from .git import get_file_last_commit, get_tracked_files, add_file


def initialize_db(db_file: str):
    engine = create_engine(f"sqlite:///{db_file}?check_same_thread=False", echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def get_file(
    sess: Session, file_path: Optional[str] = None, file_id: Optional[str] = None
) -> File:
    assert (not file_path is None) or (not file_id is None)
    file_ = None

    if file_path:
        rel_path = get_relative_path(file_path)
        file_ = sess.query(File).filter_by(path=rel_path).first()
    if file_id:
        file_ = sess.query(File).fieter_by(id=file_id).first()

    if file_:
        click.echo(f"File {file_.id} {file_.path} exists")
    else:
        file_ = File(id=id_generator(8, "file"), path=rel_path)
        sess.add(file_)
        sess.commit()
    return file_


def get_all_files(sess: Session) -> list:
    return sess.query(File).all()


def add_edge(
    sess: Session, predecessor: Union[File, Node], successor: Union[File, Node]
) -> NoReturn:
    preds_successor_ids = deepcopy(set(json.loads(predecessor.successor_ids)))
    preds_successor_ids.add(successor.id)
    predecessor.successor_ids = json.dumps(sorted(list(preds_successor_ids)))
    sucs_predecessor_ids = deepcopy(set(json.loads(successor.predecessor_ids)))
    sucs_predecessor_ids.add(predecessor.id)
    successor.predecessor_ids = json.dumps(sorted(list(sucs_predecessor_ids)))
    sess.commit()


def get_pipeline(
    sess: Session,
    pipeline_id: Optional[str] = None,
    file_lists: Optional[List[List[str]]] = None,
) -> Pipeline:
    assert (not pipeline_id is None) or (not file_lists is None)
    pipeline = None
    file_id_lists = []

    if pipeline_id:
        pipeline = sess.query(Pipeline).filter_by(id=pipeline_id).first()
    elif file_lists:
        for file_path_list in file_lists:
            file_id_list = []
            for file_path in file_path_list:
                file_id_list.append(get_file(sess, file_path=file_path).id)
            file_id_lists.append(sorted(file_id_list))
        pipeline = (
            sess.query(Pipeline)
            .filter_by(file_id_lists=json.dumps(file_id_lists))
            .first()
        )

    if pipeline is None:
        for i in range(len(file_lists) - 1):
            if len(file_lists[i]) > 1 and len(file_lists[i + 1] > 1):
                raise ValueError("There should be no consecutive multiple files")
            for pred_file_path in file_lists[i]:
                predecessor = get_file(sess, pred_file_path)
                for succ_file_path in file_lists[i + 1]:
                    successor = get_file(sess, succ_file_path)
                    add_edge(sess, predecessor, successor)

        pipeline = Pipeline(
            id=id_generator(8, "pipeline"), file_id_lists=json.dumps(file_id_lists)
        )
        sess.add(pipeline)
        sess.commit()
    return pipeline


def get_node(sess: Session, commit_id: str, file_path: str) -> Node:
    node_file = get_file(sess, file_path)
    node = sess.query(Node).filter_by(file_id=node_file.id, commit_id=commit_id).first()
    if node:
        click.echo(f"Node {node.id} {node.file.path} exists")
    else:
        node = Node(
            id=id_generator(16, "node"), file_id=node_file.id, commit_id=commit_id
        )
        sess.add(node)
        sess.commit()
    return node


def get_all_nodes(sess: Session) -> list:
    return sess.query(Node).all()


def get_experiment(
    sess: Session,
    repo: Repo,
    experiment_id: Optional[str] = None,
    description: Optional[str] = None,
    file_lists: Optional[List[List[str]]] = None,
    config: Optional[dict] = None,
    hparams: Optional[dict] = None,
) -> Experiment:
    assert (not experiment_id is None) or (not file_lists is None)

    if experiment_id:
        experiment = sess.query(Experiment).filter_by(id=experiment_id).first()
    else:
        if description is None:
            raise ValueError(
                "Description should be provided when creating a new experiment"
            )
        pipeline = get_pipeline(sess, file_lists=file_lists)
        config = "{}" if config is None else json.dumps(config)
        hparams = "{}" if hparams is None else json.dumps(hparams)

        node_id_lists = [[] for _ in range(len(file_lists))]
        tracked_files = get_tracked_files(repo)
        first_add = True
        for i in range(len(file_lists) - 1):
            if len(file_lists[i]) > 1 and len(file_lists[i + 1]) > 1:
                raise ValueError("There should be no consecutive multiple files")
            for pred_file_path in file_lists[i]:
                pred_rel_path = get_relative_path(pred_file_path)
                if pred_rel_path not in tracked_files:
                    add_file(repo, pred_rel_path)
                    if first_add:
                        repo.git.commit("-m", description)
                        first_add = False
                    else:
                        repo.git.commit("-m", description, "--amend")
                pred_commit_id = get_file_last_commit(repo, pred_rel_path)
                predecessor = get_node(sess, pred_commit_id, pred_file_path)
                node_id_lists[i].append(predecessor.id)

                for succ_file_path in file_lists[i + 1]:
                    succ_rel_path = get_relative_path(succ_file_path)
                    if succ_rel_path not in tracked_files:
                        add_file(repo, succ_rel_path)
                        if first_add:
                            repo.git.commit("-m", description)
                            first_add = False
                        else:
                            repo.git.commit("-m", description, "--amend")
                    succ_commit_id = get_file_last_commit(repo, succ_rel_path)
                    successor = get_node(sess, succ_commit_id, succ_file_path)
                    node_id_lists[i + 1].append(successor.id)
                    add_edge(sess, predecessor, successor)

        experiment = Experiment(
            id=id_generator(16, "experiment"),
            description=description,
            pipeline_id=pipeline.id,
            node_id_lists=json.dumps(node_id_lists),
            config=config,
            hparams=hparams,
        )
        sess.add(experiment)
        sess.commit()
    return experiment
