import sys
import click

print('running simple test')
print(sys.argv)
@click.command()
@click.option('--shit')
@click.option('--test')
@click.option('--whoami')
def main(shit, test, whoami):
    print(shit)
    print(test)
    print(whoami)

if __name__ == "__main__":
    main()