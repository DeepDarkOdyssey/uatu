import os
from os.path import join, exists
from shutil import rmtree
from typing import Union
import json
from copy import deepcopy
from sqlalchemy import Column, String, Integer, PickleType, Text, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from git import Repo
from git.refs.log import RefLog
from .utils import id_generator, get_relative_path
import yaml

Base = declarative_base()


class File(Base):
    __tablename__ = 'files'

    id = Column(String(8), primary_key=True)
    path = Column(String(64), unique=True, index=True, nullable=False)
    nodes = relationship('Node', backref='file')
    parent_ids = Column(PickleType, default=set())
    child_ids = Column(PickleType, default=set())

    def __repr__(self):
        return f'<File id={self.id}, path={self.path}, nodes={self.nodes},\
        parent_ids={self.parent_ids}, child_ids={self.child_ids}>'


class Node(Base):
    __tablename__ = 'nodes'

    id = Column(String(16), primary_key=True)
    file_id = Column(String(8), ForeignKey('files.id'))
    commit_id = Column(String(40), nullable=False)
    parent_ids = Column(PickleType, default=set())
    child_ids = Column(PickleType, default=set())

    def __repr__(self):
        return f'<Node id={self.id}, file_id={self.file_id}, file={self.file},\
                commit_id={self.commit_id}, parent_ids={self.parent_ids},\
                child_ids={self.child_ids}>'


class Pipeline(Base):
    __tablename__ = 'pipelines'

    id = Column(String(8), primary_key=True)
    description = Column(Text)
    pipeline = Column(PickleType, default=[], unique=True)
    experiments = relationship('Experiment', backref='pipeline')

    def __repr__(self):
        return f'<Pipeline id={self.id}, description={self.description},\
            pipeline={self.pipeline}, experiments={self.experiments}>'


class Experiment(Base):
    __tablename__ = 'experiments'

    id = Column(String(16), primary_key=True)
    description = Column(Text)
    pipeline_id = Column(String(16), ForeignKey('pipelines.id'))
    node_ids = Column(PickleType, default=[])
    config = Column(Text, default='{}')
    hparams = Column(Text, default='{}')
    metrics = Column(Text, default='{}')

    def __repr__(self):
        return f'<Experiment id={self.id}, description={self.description},\
                pipeline_id={self.pipeline_id}, node_ids={self.node_ids},\
                config={self.config}, hparams={self.hparams}>'


def add_edge(sess, parent, child):
    parent_child_ids = deepcopy(parent.child_ids)
    parent_child_ids.add(child.id)
    parent.child_ids = parent_child_ids
    child_parent_ids = deepcopy(child.parent_ids)
    child_parent_ids.add(parent.id)
    child.parent_ids = child_parent_ids
    sess.commit()


def get_file(sess, file_path):
    file = sess.query(File).filter_by(path=file_path).first()
    if file:
        print(f'File {file.id} {file.path} exists')
    else:
        file = File(id=id_generator(8, 'file'), path=file_path)
        sess.add(file)
        sess.commit()
    return file


def get_pipeline(sess, file_paths):
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


def get_node(sess, repo, file_path):
    node_file = get_file(sess, file_path)
    commit_id = repo.git.execute(['git', 'log', '--', file_path])
    print('****', commit_id)
    commit_id = repo.git.execute(['git', 'log', '--',
                                  file_path]).split('\n')[0].split()[1]
    node = sess.query(Node).filter_by(file_id=node_file.id,
                                      commit_id=commit_id).first()
    if node:
        print(f'Node {node.id} {node.file.path} exists')
    else:
        node = Node(id=id_generator(16, 'node'),
                    file_id=node_file.id,
                    commit_id=commit_id)
        sess.add(node)
        sess.commit()
    return node


def get_experiment(sess, repo, file_paths, config=None, hparams=None):
    config = '{}' if config is None else json.dumps(config)
    hparams = '{}' if hparams is None else json.dumps(hparams)
    pipeline = get_pipeline(sess, file_paths)

    nodes, node_ids = [], []
    for file_path in file_paths:
        if type(file_path) == list:
            node, node_id = [], []
            for sub_file in file_path:
                sub_node = get_node(sess, repo, sub_file)
                node.append(sub_node)
                node_id.append(sub_node.id)
            nodes.append(node)
            node_ids.append(node_id)
        else:
            node = get_node(sess, repo, file_path)
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


def check_initialized(dir_path: str) -> bool:
    hidden_dir = join(dir_path, '.uatu')
    if exists(hidden_dir):
        if exists(join(hidden_dir, 'uatu_config.yaml')):
            with open(join(hidden_dir, 'uatu_config.yaml')) as f:
                config = yaml.safe_load(f)
            for file_name, file_path in config.items():
                if not exists(file_path):
                    print(f'{file_name} not exists!')
                    return False
            return True
        else:
            print('Uatu config not exists!')
            return False
    else:
        print('Uata folder not exists!')
        return False


def clean(cwd: str = os.getcwd()):
    uatu_dir = join(cwd, '.uatu')
    try:
        rmtree(uatu_dir)
    except FileNotFoundError:
        pass
    print('Uatu folder has been cleaned!')


def initialize_db(db_file):
    engine = create_engine(f'sqlite:///{db_file}?check_same_thread=False',
                           echo=True)
    Base.metadata.create_all(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session


def get_tracked_files(repo: Repo) -> list:
    return repo.git.ls_files().split()


def add(repo: Repo, file_path: str):
    tracked_files = get_tracked_files(repo)
    if file_path in tracked_files:
        print(f'{file_path} has already been added to git repo')
    else:
        file_size = os.path.getsize(file_path)
        if file_size > 1000000:
            repo.git.execute(['git', 'lfs', 'track', file_path])
            repo.git.execute(['git', 'add', file_path])
        else:
            repo.git.execute(['git', 'add', file_path])


def initialize_git(repo_dir: str) -> Repo:
    repo = Repo.init(repo_dir)
    ignore_file = join(repo_dir, '.gitignore')
    if exists(ignore_file):
        with open(ignore_file) as f:
            lines = [line.strip() for line in f]
        if '.uatu/' not in lines:
            with open(ignore_file, 'a') as f:
                f.write('.uatu/' + '\n')
    else:
        with open(ignore_file, 'w') as f:
            f.write('.uatu/' + '\n')

    attributes_file = join(repo_dir, '.gitattributes')
    if not exists(attributes_file):
        f = open(attributes_file, 'w')
        f.close()
    add(repo, get_relative_path(ignore_file))
    add(repo, get_relative_path(attributes_file))

    return repo


def init(user_config: str = None) -> Union[Session, dict]:
    cwd = os.getcwd()
    if check_initialized(cwd):
        if user_config is None:
            print('Uatu is already watching your project!')
            with open(join(cwd, '.uatu', 'uatu_config.yaml')) as f:
                uatu_config = yaml.safe_load(f)
            sess = initialize_db(uatu_config['database_file'])
            return sess, uatu_config
        else:
            # TODO: use prompt to ask
            print(
                "Uatu is already watching your project! Do you want to refresh\
                your project? This will lose all your preserved file")
            return None
    else:
        clean()
        uatu_dir = join(cwd, '.uatu')
        os.mkdir(uatu_dir)
        if user_config is None:
            uatu_config = {
                'database_file': join(uatu_dir, 'uatu.db'),
                'data_dir': './data',
                'experiment_dir': './experiments',
                'log_file': join(uatu_dir, 'log.txt')
            }
        else:
            uatu_config = yaml.load(user_config)

        with open(join(uatu_dir, 'uatu_config.yaml'), 'w') as yaml_file:
            yaml.dump(uatu_config, yaml_file)

        if exists(join(cwd, uatu_config['experiment_dir'])):
            # TODO: use prompt to ask user whether to delete original folder
            pass
        else:
            os.mkdir(join(cwd, uatu_config['experiment_dir']))

        if exists(join(cwd, uatu_config['data_dir'])):
            # TODO: use prompt to ask user whether to delete original folder
            pass
        else:
            os.mkdir(join(cwd, uatu_config['data_dir']))

        if not exists(join(uatu_dir, uatu_config['log_file'])):
            f = open(join(uatu_dir, uatu_config['log_file']), 'w')
            f.close()

        sess = initialize_db(uatu_config['database_file'])
        print('Uatu has been summoned! Your project is now being watched!')
        return sess, uatu_config


def experiment_ls(sess, repo):
    print(sess.query(Experiment).all())


if __name__ == "__main__":
    cwd = os.getcwd()
    repo = initialize_git(cwd)
    # add(repo, 'data/test.txt')
    # print(get_tracked_files(repo))
    sess = initialize_db('.uatu/uatu.db')
    experiment_ls(sess, repo)
    node = get_node(sess, repo, 'data/test.txt')
    print(node)

    # log = RefLog('uatu/init.py')
