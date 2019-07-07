import click
from os import getcwd
from .init import check_uatu_initialized, initialize_uatu, clean_uatu
from .database import initialize_db
from .git import check_git_initialized, initialize_git


@click.group()
def cli():
    pass


@cli.command()
@click.option('--force', '-f', is_flag=True)
@click.option('--config_file', type=click.Path(exists=True, dir_okay=False))
def init(force, config_file):
    if not check_git_initialized():
        click.confirm(
            'This folder is not a git repo, do you want to initialize git?',
            abort=True)
        initialize_git()
    click.echo('Git repo has been initialized')

    if check_uatu_initialized():
        click.confirm(
            'Uatu is watching this project, do you still want to initialize?',
            abort=True)
    initialize_uatu()
    click.echo('Uatu has arrived!')


@cli.command()
@click.option('--dir_path',
              '-d',
              type=click.Path(exists=True, file_okay=False),
              default=getcwd())
def clean(dir_path):
    clean_uatu(dir_path)


@cli.command('watch')
@click.option('--file',
              '-f',
              'file_',
              type=click.Path(exists=True, dir_okay=False))
@click.option('--expr', '-e', 'experiment')
def watch(file_, experiment):
    initialize_db()
    if file_:
        pass


@cli.command('experiment')
def experiment_cli():
    click.echo('using experiment CLI')