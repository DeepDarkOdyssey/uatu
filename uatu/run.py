import os
import json
import click
from typing import List, Optional
from functools import wraps
from .database import initialize_db, get_experiment
from .init import initialize_uatu, get_uatu_config
from .git import get_repo


class Run(object):
    def __init__(
        self,
        input_files: List[str] = [],
        output_files: List[str] = [],
        config: Optional[dict] = None,
        hparams: Optional[dict] = None,
    ):
        description = click.prompt('Please describe this experiment carefully', type=str)
        file_lists = []
        if len(input_files) > 0:
            file_lists.append(input_files)
        file_lists.append([__file__])
        if len(output_files) > 0:
            file_lists.append(output_files)

        uatu_config = get_uatu_config()
        self.sess = initialize_db(uatu_config["database_file"])
        self.repo = get_repo()
        self.experiment = get_experiment(
            sess=self.sess,
            repo=self.repo,
            description=description,
            file_lists=file_lists,
            config=config,
            hparams=hparams
        )
    
    def save(self, metrics: dict = {}):
        self.experiment.metrics = json.dumps(metrics)
        self.sess.commit()
        self.sess.close()

    def __call__(self, func):
        @wraps(func)
        def monitored_func(*args, **kwargs):
            metric = func(*args, **kwargs)
            self.save(metric)
            return metric

        return monitored_func

    # @staticmethod
    # def add_file_path(file_paths: list, extra_paths: Union[list, str]) -> list:
    #     if type(extra_paths) == str:
    #         file_paths.append(extra_paths)
    #         return file_paths

    #     else:
    #         if len(extra_paths) == 0:
    #             pass
    #         elif len(extra_paths) == 1:
    #             file_paths.append(extra_paths[0])
    #         else:
    #             file_paths.append(extra_paths)
    #         return file_paths
