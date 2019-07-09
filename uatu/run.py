import os
import json
from typing import Union
from git import Repo
from functools import wraps
from .database import initialize_db, get_experiment
from .init import initialize_uatu, get_uatu_config


class Run(object):
    def __init__(self, input_files=[], output_files=[], config=None, hparams=None):
        self.input_files = input_files
        self.output_files = output_files
        self.config = config
        self.hparams = hparams
        self.metric = None

        self.cwd = os.getcwd()

        uatu_config = get_uatu_config()
        self.sess = initialize_db(uatu_config['database_file'])
        self.repo = Repo(path=self.cwd)

    def __call__(self, func):
        @wraps(func)
        def monitored_func(*args, **kwargs):
            metric = func(*args, **kwargs)
            self.save(metric)
            return metric
        return monitored_func
    
    def save(self, metrics={}):
        file_paths = []
        file_paths = self.add_file_path(file_paths, self.input_files)
        file_paths = self.add_file_path(file_paths, __file__)
        file_paths = self.add_file_path(file_paths, self.output_files)
        experiment = get_experiment(
            sess=self.sess,
            repo=self.repo,
            file_paths=file_paths,
            config=json.dumps(self.config),
            hparams=json.dumps(self.hparams),
        )
        experiment.metrics = metrics
        self.sess.commit()
        self.sess.close()
    
    @staticmethod
    def add_file_path(file_paths: list, extra_paths: Union[list, str]) -> list:
        if type(extra_paths) == str:
            file_paths.append(extra_paths)
            return file_paths

        else:
            if len(extra_paths) == 0:
                pass
            elif len(extra_paths) == 1:
                file_paths.append(extra_paths[0])
            else:
                file_paths.append(extra_paths)
            return file_paths