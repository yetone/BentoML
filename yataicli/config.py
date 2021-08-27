import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dataclasses_json import DataClassJsonMixin
from ruamel.yaml import YAML
from yamldataclassconfig import YamlDataClassConfig, create_file_path_field

from yataicli.client.yatai import YataiClient
from yataicli.errors import YataiCliError

yaml = YAML()

default_context_name = 'default'


def get_config_path() -> Path:
    return Path.home() / '.yatai.yaml'


@dataclass
class Context(DataClassJsonMixin):
    name: str
    endpoint: str
    api_token: str

    def get_yatai_cli(self) -> YataiClient:
        return YataiClient(self.endpoint, self.api_token)


@dataclass
class Config(YamlDataClassConfig):
    contexts: List[Context] = field(default_factory=lambda: [])
    current_context_name: str = ''

    FILE_PATH: Path = create_file_path_field(get_config_path())

    def get_current_context(self) -> Context:
        for ctx in self.contexts:
            if ctx.name == self.current_context_name:
                return ctx
        raise YataiCliError(f'Not found {self.current_context_name} yatai context, please login!')


_config: Config = Config()


def store_config(config: Config) -> None:
    with open(get_config_path(), 'w') as f:
        dct = config.to_dict()
        dct.pop('FILE_PATH', None)
        yaml.dump(dct, stream=f)


def init_config() -> Config:
    config = Config(contexts=[], current_context_name=default_context_name)
    store_config(config)
    return config


def get_config() -> Config:
    if not os.path.exists(get_config_path()):
        return init_config()
    _config.load()
    return _config


def add_context(context: Context) -> None:
    config = get_config()
    for idx, ctx in enumerate(config.contexts):
        if ctx.name == context.name:
            config.contexts[idx] = context
            break
    else:
        config.contexts.append(context)
    store_config(config)


def get_current_context() -> Context:
    config = get_config()
    return config.get_current_context()


def get_current_yatai_cli() -> YataiClient:
    ctx = get_current_context()
    return ctx.get_yatai_cli()
