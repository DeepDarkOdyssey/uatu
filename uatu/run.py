import os
import json
import click
from inspect import getfile
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
        self.description = click.prompt(
            "Please describe this experiment carefully", type=str
        )
        self.input_files = input_files
        self.output_files = output_files
        self.config = config
        self.hparams = hparams

    def save(self, script_path, metrics: dict = {}):
        file_lists = []
        if len(self.input_files) > 0:
            file_lists.append(self.input_files)
        file_lists.append([script_path])
        if len(self.output_files) > 0:
            file_lists.append(self.output_files)

        sess = initialize_db(get_uatu_config()["database_file"])
        repo = get_repo()
        get_experiment(
            sess=sess,
            repo=repo,
            description=self.description,
            file_lists=file_lists,
            config=self.config,
            hparams=self.hparams,
            metrics=metrics,
        )
        sess.commit()
        sess.close()

    def __call__(self, func):
        @wraps(func)
        def monitored_func(*args, **kwargs):
            func_file = getfile(func)
            metrics = func(*args, **kwargs)
            self.save(func_file, metrics)
            return metrics

        return monitored_func