import click

from yataicli.click_utils import BentoMLCommandGroup, _echo, CLI_COLOR_ERROR
from yataicli.cmd.bento import add_bento_sub_command
from yataicli.cmd.login import add_login_sub_command
from yataicli.errors import YataiCliError


def _create_yatai_cli():
    @click.group(cls=BentoMLCommandGroup)
    @click.version_option(version='1.0')
    def yatai_cli():
        """
        Yatai CLI tool
        """
    return yatai_cli


def create_root_cli():
    cli_ = _create_yatai_cli()
    add_login_sub_command(cli_)
    add_bento_sub_command(cli_)
    return cli_


def main():
    cli = create_root_cli()
    try:
        cli()
    except YataiCliError as e:
        _echo(str(e), color=CLI_COLOR_ERROR, err=True)
        exit(1)


if __name__ == '__main__':
    main()
