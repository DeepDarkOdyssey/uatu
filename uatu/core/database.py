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
from .git import get_last_commit, get_tracked_files, add_file, get_repo


def initialize_db(db_file: str) -> Session:
    engine = create_engine(f"sqlite:///{db_file}?check_same_thread=False", echo=False)
    Base.metadata.create_all(engine, checkfirst=True)
    Session_cls = sessionmaker(bind=engine)
    session = Session_cls()
    return session


def get_file(
    sess: Session,
    file_path: Optional[str] = None,
    file_id: Optional[str] = None,
    create: bool = True,
) -> Union[File, None]:
    assert (not file_path is None) or (not file_id is None)

    if file_path:
        rel_path = get_relative_path(file_path)
        file_ = sess.query(File).filter_by(path=rel_path).first()
    if file_id:
        file_ = sess.query(File).filter_by(id=file_id).first()

    if (not file_) and create:
        file_ = File(id=id_generator(salt="file"), path=rel_path)
        sess.add(file_)
        sess.commit()
    return file_


def delete_file(
    sess: Session,
    file: Optional[File] = None,
    file_path: Optional[str] = None,
    file_id: Optional[str] = None,
) -> NoReturn:
    assert (not file is None) or (not file_path is None) or (not file_id is None)
    if not file:
        file = get_file(sess, file_path=file_path, file_id=file_id)

    pipelines = get_all_pipelines(sess)
    for pipeline in pipelines:
        for file_id_list in pipeline.file_id_lists:
            if file.id in file_id_list:
                delete_pipeline(sess, pipeline)
                break
    for node in file.nodes:
        delete_node(sess, node=node)

    sess.delete(file)
    sess.commit()


def get_all_files(sess: Session) -> List[File]:
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


def delete_edge(
    sess: Session, predecessor: Union[File, Node], successor: Union[File, Node]
) -> NoReturn:
    preds_successor_ids = deepcopy(set(json.loads(predecessor.successor_ids)))
    preds_successor_ids.remove(successor.id)
    predecessor.successor_ids = json.dumps(sorted(list(preds_successor_ids)))
    sucs_predecessor_ids = deepcopy(set(json.loads(successor.predecessor_ids)))
    sucs_predecessor_ids.remove(predecessor.id)
    successor.predecessor_ids = json.dumps(sorted(list(sucs_predecessor_ids)))
    sess.commit()


def get_pipeline(
    sess: Session,
    pipeline_id: Optional[str] = None,
    file_lists: Optional[List[List[str]]] = None,
    create: bool = True,
) -> Union[Pipeline, None]:
    assert (not pipeline_id is None) or (not file_lists is None)
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

    if (not pipeline) and (not file_lists) and create:
        for i in range(len(file_lists) - 1):
            if len(file_lists[i]) > 1 and len(file_lists[i + 1]) > 1:
                raise ValueError("There should be no consecutive multiple files")
            for pred_file_path in file_lists[i]:
                predecessor = get_file(sess, pred_file_path)
                for succ_file_path in file_lists[i + 1]:
                    successor = get_file(sess, succ_file_path)
                    add_edge(sess, predecessor, successor)

        pipeline = Pipeline(
            id=id_generator(salt="pipeline"), file_id_lists=json.dumps(file_id_lists)
        )
        sess.add(pipeline)
        sess.commit()
    return pipeline


def delete_pipeline(
    sess: Session,
    pipeline: Optional[Pipeline] = None,
    pipeline_id: Optional[str] = None,
) -> NoReturn:
    assert (not pipeline is None) or (not pipeline_id is None)
    if not pipeline:
        pipeline = get_pipeline(sess, pipeline_id)

    for experiment in pipeline.experiments:
        delete_experiment(sess, experiment=experiment)

    file_id_lists = json.loads(pipeline.file_id_lists)
    for i in range(len(file_id_lists) - 1):
        for pred_file_id in file_id_lists[i]:
            pred_file = get_file(sess, file_id=pred_file_id)
            for succ_file_id in file_id_lists[i + 1]:
                succ_file = get_file(sess, file_id=succ_file_id)
                delete_edge(sess, pred_file, succ_file)

    sess.delete(pipeline)
    sess.commit()


def get_all_pipelines(sess: Session) -> List[Pipeline]:
    return sess.query(Pipeline).all()


def get_node(
    sess: Session,
    node_id: Optional[str] = None,
    file_path: Optional[str] = None,
    commit_id: Optional[str] = None,
    create: bool = True,
) -> Union[Node, None]:
    assert (not node_id is None) or (not file_path is None)
    if node_id:
        node = sess.query(Node).filter_by(id=node_id).first()
    else:
        node_file = get_file(sess, file_path, create=create)
        if node_file:
            if not commit_id:
                # FIXME: Maybe should add repo to function arguments
                commit_id = get_last_commit(get_repo(), file_path)
            node = (
                sess.query(Node)
                .filter_by(file_id=node_file.id, commit_id=commit_id)
                .first()
            )
        else:
            node = None

    if (not node) and create:
        if not commit_id:
            commit_id = get_last_commit(get_repo(), file_path)
        node_file = get_file(sess, file_path=file_path)
        node = Node(
            id=id_generator(salt="node"), file_id=node_file.id, commit_id=commit_id
        )
        sess.add(node)
        sess.commit()
    return node


def delete_node(
    sess: Session, node: Optional[Node] = None, node_id: Optional[str] = None
) -> NoReturn:
    assert (not node is None) or (not node_id is None)
    if not node:
        node = get_node(sess, node_id)
    experiments = get_all_experiments(sess)
    for experiment in experiments:
        for node_id_list in experiment.node_id_lists:
            if node.id in node_id_list:
                delete_experiment(sess, experiment)
                break
    sess.delete(node)
    sess.commit()


def get_all_nodes(sess: Session) -> List[Node]:
    return sess.query(Node).all()


def get_experiment(
    sess: Session,
    repo: Optional[Repo] = None,
    experiment_id: Optional[str] = None,
    description: Optional[str] = None,
    file_lists: Optional[List[List[str]]] = None,
    config: Optional[dict] = None,
    hparams: Optional[dict] = None,
    metrics: Optional[dict] = None,
) -> Experiment:
    assert (not experiment_id is None) or (not file_lists is None)

    if experiment_id:
        experiment = sess.query(Experiment).filter_by(id=experiment_id).first()
    else:
        assert not repo is None
        if description is None:
            raise ValueError(
                "Description should be provided when creating a new experiment"
            )
        pipeline = get_pipeline(sess, file_lists=file_lists)
        config = "{}" if config is None else json.dumps(config)
        hparams = "{}" if hparams is None else json.dumps(hparams)
        metrics = "{}" if metrics is None else json.dumps(metrics)

        node_id_lists = [[] for _ in range(len(file_lists))]
        tracked_files = get_tracked_files(repo)
        first_add = True
        for i in range(len(file_lists) - 1):
            if len(file_lists[i]) > 1 and len(file_lists[i + 1]) > 1:
                raise ValueError("There should be no consecutive multiple files")
            for pred_file_path in file_lists[i]:
                pred_rel_path = get_relative_path(pred_file_path, repo.working_dir)
                if pred_rel_path not in tracked_files:
                    add_file(repo, pred_rel_path)
                    if first_add:
                        repo.git.commit("-m", description)
                        first_add = False
                    else:
                        repo.git.commit("-m", description, "--amend")
                pred_commit_id = get_last_commit(repo, pred_rel_path)
                predecessor = get_node(sess, pred_commit_id, pred_file_path)
                node_id_lists[i].append(predecessor.id)

                for succ_file_path in file_lists[i + 1]:
                    succ_rel_path = get_relative_path(succ_file_path, repo.working_dir)
                    if succ_rel_path not in tracked_files:
                        add_file(repo, succ_rel_path)
                        if first_add:
                            repo.git.commit("-m", description)
                            first_add = False
                        else:
                            repo.git.commit("-m", description, "--amend")
                    succ_commit_id = get_last_commit(repo, succ_rel_path)
                    successor = get_node(sess, succ_commit_id, succ_file_path)
                    node_id_lists[i + 1].append(successor.id)
                    add_edge(sess, predecessor, successor)

        experiment = Experiment(
            id=id_generator(salt="experiment"),
            description=description,
            pipeline_id=pipeline.id,
            node_id_lists=json.dumps(node_id_lists),
            config=config,
            hparams=hparams,
            metrics=metrics,
        )
        sess.add(experiment)
        sess.commit()
    return experiment


def delete_experiment(
    sess: Session,
    experiment: Optional[Experiment] = None,
    expr_id: Optional[str] = None,
) -> NoReturn:
    assert (not experiment is None) or (not expr_id is None)
    if not experiment:
        experiment = get_experiment(sess, experiment_id=expr_id)
    node_id_lists = json.loads(experiment.node_id_lists)
    for i in range(len(node_id_lists) - 1):
        for pred_node_id in node_id_lists[i]:
            pred_node = get_node(sess, node_id=pred_node_id)
            for succ_node_id in node_id_lists[i + 1]:
                succ_node = get_node(sess, node_id=succ_node_id)
                delete_edge(sess, pred_node, succ_node)

    sess.delete(experiment)
    sess.commit()


def get_all_experiments(sess: Session) -> List[Experiment]:
    return sess.query(Experiment).all()
