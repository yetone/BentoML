import io
import os
import tarfile
from pathlib import Path

import click
import requests
from ruamel import yaml

from yataicli.click_utils import _echo, CLI_COLOR_ERROR, CLI_COLOR_SUCCESS
from yataicli.config import get_current_yatai_cli
from yataicli.errors import YataiCliError
from yataicli.schemas import (
    CreateBentoSchema, BentoMLYaml, CreateBentoVersionSchema, BentoVersionManifestSchema, BentoMLYamlMetadata,
    FinishUploadBentoVersionSchema, BentoVersionUploadStatus,
)
from yaspin import yaspin
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper


def add_bento_sub_command(cli):
    @cli.group(name='bento')
    def bento_cli():
        """Bento Management"""

    @bento_cli.command()
    @click.argument("bento", type=click.STRING)
    def push(bento: str) -> None:
        name, _, version = bento.partition(':')
        if not version:
            raise YataiCliError(f'Please specify the bento version')
        bento_dir_path = Path.home() / 'bentoml' / 'repository' / name / version
        bentoml_yaml_path = bento_dir_path / 'bentoml.yml'
        if not os.path.exists(bentoml_yaml_path):
            raise YataiCliError(f'Cannot found this bento: {bento}')
        with open(bentoml_yaml_path, 'r') as f:
            dct = yaml.safe_load(f)
            bentoml_yaml = BentoMLYaml.from_dict(dct)
        yatai_cli = get_current_yatai_cli()
        with yaspin(text=f'Fetching bento {name}'):
            bento_obj = yatai_cli.get_bento(bento_name=name)
        if not bento_obj:
            bento_obj = yatai_cli.create_bento(req=CreateBentoSchema(name=name, description=''))
        with yaspin(text=f'Fetching bento version {version}'):
            bento_version_obj = yatai_cli.get_bento_version(bento_name=name, version=version)
        if not bento_version_obj:
            yatai_cli.create_bento_version(bento_name=bento_obj.name, req=CreateBentoVersionSchema(
                description='',
                version=version,
                build_at=bentoml_yaml.metadata.created_at,
                manifest=BentoVersionManifestSchema(
                    metadata=BentoMLYamlMetadata(
                        service_name=bentoml_yaml.metadata.service_name,
                        service_version=bentoml_yaml.metadata.service_version,
                        module_name=bentoml_yaml.metadata.module_name,
                        module_file=bentoml_yaml.metadata.module_file,
                    ),
                    apis=bentoml_yaml.apis),
            ))
        bento_version_obj = yatai_cli.presign_bento_version_s3_upload_url(bento_name=bento_obj.name, version=version)
        tar_io = io.BytesIO()
        with yaspin(text=f'Taring bento {name}'):
            with tarfile.open(fileobj=tar_io, mode='w:gz') as tar:
                tar.add(bento_dir_path, arcname='./')
        tar_io.seek(0, 0)
        with yaspin(text=f'Starting upload bento {name}'):
            yatai_cli.start_upload_bento_version(bento_name=bento_obj.name, version=version)
        file_size = tar_io.getbuffer().nbytes
        with tqdm(desc=f'Uploading bento {name}', total=file_size, unit='B', unit_scale=True, unit_divisor=1024) as t:
            finish_req = FinishUploadBentoVersionSchema(
                status=BentoVersionUploadStatus.SUCCESS,
                reason='',
            )
            wrapped_file = CallbackIOWrapper(t.update, tar_io, 'read')
            try:
                resp = requests.put(bento_version_obj.presigned_s3_url, data=wrapped_file)
                if resp.status_code != 200:
                    finish_req = FinishUploadBentoVersionSchema(
                        status=BentoVersionUploadStatus.FAILED,
                        reason=resp.text,
                    )
            except Exception as e:
                finish_req = FinishUploadBentoVersionSchema(
                    status=BentoVersionUploadStatus.FAILED,
                    reason=str(e),
                )
            yatai_cli.finish_upload_bento_version(bento_name=bento_obj.name, version=version, req=finish_req)
        if finish_req.status != BentoVersionUploadStatus.SUCCESS:
            _echo(f'Upload {finish_req}: {finish_req.reason}', color=CLI_COLOR_ERROR)
        else:
            _echo(f'Upload successfully', color=CLI_COLOR_SUCCESS)
