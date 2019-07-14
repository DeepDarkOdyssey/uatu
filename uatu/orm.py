from sqlalchemy import Column, String, Text, PickleType, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()


class File(Base):  # type: ignore
    __tablename__ = "files"

    id = Column(String(8), primary_key=True)
    path = Column(String(64), unique=True, index=True, nullable=False)
    nodes = relationship("Node", backref="file")
    predecessor_ids = Column(Text, default="[]")
    successor_ids = Column(Text, default="[]")

    def __repr__(self):
        return f"<File id={self.id}, path={self.path}, nodes={self.nodes},\
        predecessor_ids={self.predecessor_ids}, successor_ids={self.successor_ids}>"


class Node(Base):  # type: ignore
    __tablename__ = "nodes"

    id = Column(String(16), primary_key=True)
    file_id = Column(String(8), ForeignKey("files.id"))
    commit_id = Column(String(40), nullable=False)
    predecessor_ids = Column(Text, default="[]")
    successor_ids = Column(Text, default="[]")

    def __repr__(self):
        return f"<Node id={self.id}, file_id={self.file_id}, file={self.file},\
                commit_id={self.commit_id}, predecessor_ids={self.predecessor_ids},\
                successor_ids={self.successor_ids}>"


class Pipeline(Base):  # type: ignore
    __tablename__ = "pipelines"

    id = Column(String(8), primary_key=True)
    description = Column(Text)
    file_id_lists = Column(Text, default="[]")
    experiments = relationship("Experiment", backref="pipeline")

    def __repr__(self):
        return f"<Pipeline id={self.id}, description={self.description},\
            file_id_lists={self.file_id_lists}, experiments={self.experiments}>"


class Experiment(Base):  # type: ignore
    __tablename__ = "experiments"

    id = Column(String(16), primary_key=True)
    description = Column(Text, nullable=False)
    pipeline_id = Column(String(16), ForeignKey("pipelines.id"))
    node_id_lists = Column(Text, default="[]")
    config = Column(Text, default="{}")
    hparams = Column(Text, default="{}")
    metrics = Column(Text, default="{}")

    def __repr__(self):
        return f"<Experiment id={self.id}, description={self.description},\
                pipeline_id={self.pipeline_id}, node_ids={self.node_ids},\
                config={self.config}, hparams={self.hparams}>"