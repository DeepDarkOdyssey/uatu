from sqlalchemy import Column, String, Text, PickleType, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

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