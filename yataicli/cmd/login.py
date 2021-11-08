import click

from yataicli.click_utils import _echo, CLI_COLOR_SUCCESS
from yataicli.config import add_context, Context, default_context_name
from yataicli.errors import YataiCliError


def add_login_sub_command(cli):
    @cli.command()
    @click.option('--endpoint', type=click.STRING, help='Yatai endpoint, like https://yatai.io')
    @click.option('--api-token', type=click.STRING, help='Yatai user api token')
    def login(endpoint: str, api_token: str) -> None:
        if not endpoint:
            raise YataiCliError('need --endpoint')

        if not api_token:
            raise YataiCliError('need --api-token')

        ctx = Context(
            name=default_context_name,
            endpoint=endpoint,
            api_token=api_token,
        )

        add_context(ctx)

        yatai_cli = ctx.get_yatai_cli()
        user = yatai_cli.get_current_user()
        org = yatai_cli.get_current_organization()
        _echo(f'login successfully! user: {user.name}, organization: {org.name}', color=CLI_COLOR_SUCCESS)
