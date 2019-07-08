import click
from os import getcwd
from .init import check_uatu_initialized, initialize_uatu, clean_uatu, get_uatu_config
from .database import initialize_db
from .git import check_git_initialized, initialize_git, get_repo, get_changed_files, add_file
from .utils import get_relative_path
from .database import initialize_db, get_node


@click.group()
def cli():
    pass


@cli.command()
@click.option('--config_file', type=click.Path(exists=True, dir_okay=False))
def init(config_file):
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
    initialize_uatu(user_config=config_file)
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
              'files',
              multiple=True,
              type=click.Path(exists=True, dir_okay=False))
@click.option('--expr', '-e', 'experiment')
@click.option('--message',
              '-m',
              'message',
              prompt='Please enter a message for `git commit`')
def watch(files, experiment, message):
    if files:
        if not check_git_initialized() or not check_uatu_initialized():
            click.echo('This project has\'t been initialized yet. \
                Please try `uatu init`.')
            return
        repo = get_repo()
        sess = initialize_db(get_uatu_config()['database_file'])
        all_changed_files = get_changed_files(repo)
        changed_files = []
        for file_path in files:
            relpath = get_relative_path(file_path)
            if relpath in all_changed_files:
                changed_files.append(relpath)
                add_file(repo, file_path)
        if len(changed_files) > 0:
            commit = repo.commit(message)
            for relpath in changed_files:
                get_node(sess, str(commit), relpath)
            click.echo(
                f'Uatu is now watching {changed_files}, commit_id: {str(commit)}'
            )
        else:
            click.echo(f'None of these files has been modified')


@cli.command('experiment')
def experiment_cli():
    click.echo('using experiment CLI')