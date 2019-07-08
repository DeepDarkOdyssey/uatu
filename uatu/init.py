import os
from os.path import join, exists
from shutil import rmtree
from typing import Union
import json
from sqlalchemy import Column, String, Integer, PickleType, Text, ForeignKey, create_engine
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from .utils import id_generator, get_relative_path
import yaml
import click
from .logger import get_logger
from .database import initialize_db


def check_uatu_initialized(dir_path: str = os.getcwd()) -> bool:
    uatu_dir = join(dir_path, '.uatu')
    if exists(uatu_dir):
        if exists(join(uatu_dir, 'config.yaml')):
            with open(join(uatu_dir, 'config.yaml')) as f:
                config = yaml.safe_load(f)
            for file_name, file_path in config.items():
                if not exists(file_path):
                    click.echo(f'{file_name} not exists!')
                    return False
            return True
        else:
            click.echo('Uatu config not exists!')
            return False
    else:
        click.echo('Uata folder not exists!')
        return False


def clean_uatu(dir_path=os.getcwd()):
    uatu_dir = join(dir_path, '.uatu')
    if exists(uatu_dir):
        click.confirm('Do you want to clean Uatu\'s memory? This will lose all your preserved records', abort=True)
        rmtree(uatu_dir)


def initialize_uatu(dir_path: str = os.getcwd(),
                    user_config: str = None) -> Session:
    clean_uatu(dir_path)

    uatu_dir = join(dir_path, '.uatu')
    os.mkdir(uatu_dir)
    if user_config is None:
        uatu_config = {
            'database_file': '.uatu/uatu.db',
            'experiment_dir': 'experiments',
            'log_file': '.uatu/log.txt'
        }
    else:
        with open(user_config) as f:
            uatu_config = yaml.safe_load(f)

    with open(join(uatu_dir, 'config.yaml'), 'w') as yaml_file:
        yaml.dump(uatu_config, yaml_file)

    if exists(join(dir_path, uatu_config['experiment_dir'])):
        if click.confirm(
                f'Do you want to refresh directory [{join(dir_path, uatu_config["experiment_dir"])}]'
        ):
            rmtree(join(dir_path, uatu_config['experiment_dir']))
            os.mkdir(join(dir_path, uatu_config['experiment_dir']))
    else:
        os.mkdir(join(dir_path, uatu_config['experiment_dir']))

    if not exists(join(dir_path, uatu_config['log_file'])):
        f = open(join(dir_path, uatu_config['log_file']), 'w')
        f.close()

    sess = initialize_db(uatu_config['database_file'])
    return sess


def get_uatu_config(dir_path: str = os.getcwd()) -> dict:
    with open(join(dir_path, '.uatu', 'config.yaml')) as f:
        return yaml.safe_load(f)
