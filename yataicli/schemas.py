from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List

from dataclasses_json import DataClassJsonMixin
from marshmallow import fields
from dateutil.parser import parse


time_format = '%Y-%m-%d %H:%M:%S.%f'


def datetime_encoder(time_obj: Optional[datetime]) -> Optional[str]:
    if not time_obj:
        return None
    return time_obj.strftime(time_format)


def datetime_decoder(datetime_str: Optional[str]) -> Optional[datetime]:
    if not datetime_str:
        return None
    return parse(datetime_str)


datetime_field_kwargs = dict(metadata={'dataclasses_json': {
    'encoder': datetime_encoder,
    'decoder': datetime_decoder,
    'mm_field': fields.DateTime(format='iso')
}})


@dataclass
class BentoMLYamlMetadata(DataClassJsonMixin):
    service_name: str = ''
    service_version: str = ''
    module_name: str = ''
    module_file: str = ''
    created_at: datetime = field(default_factory=datetime.now, **datetime_field_kwargs)


@dataclass
class BentoMLYamlApi(DataClassJsonMixin):
    name: str = ''
    docs: str = ''
    input_type: str = ''
    output_type: str = ''


@dataclass
class BentoMLYaml(DataClassJsonMixin):
    version: str = ''
    kind: str = ''
    metadata: BentoMLYamlMetadata = BentoMLYamlMetadata()
    apis: List[BentoMLYamlApi] = field(default_factory=lambda: [])


@dataclass
class BaseSchema(DataClassJsonMixin):
    uid: str = ''
    created_at: datetime = field(default_factory=datetime.now, **datetime_field_kwargs)
    updated_at: Optional[datetime] = field(default=None, **datetime_field_kwargs)
    deleted_at: Optional[datetime] = field(default=None, **datetime_field_kwargs)


class BaseListSchema(DataClassJsonMixin):
    start: int
    count: int
    total: int


class ResourceType(Enum):
    USER = 'user'
    ORG = 'organization'
    CLUSTER = 'cluster'
    BENTO = 'bento'
    BENTO_VERSION = 'bento_version'


@dataclass
class ResourceSchema(BaseSchema, DataClassJsonMixin):
    name: str = ''
    resource_type: ResourceType = ResourceType.USER


@dataclass
class UserSchema(ResourceSchema):
    name: str = ''
    email: str = ''
    first_name: str = ''
    last_name: str = ''

    def get_name(self) -> str:
        if not self.first_name and not self.last_name:
            return self.name
        return f'{self.first_name} {self.last_name}'.strip()


@dataclass
class OrganizationSchema(ResourceSchema, DataClassJsonMixin):
    description: str = ''


@dataclass
class OrganizationListSchema(BaseListSchema):
    items: List[OrganizationSchema]


@dataclass
class ClusterSchema(ResourceSchema):
    description: str = None


@dataclass
class BentoSchema(ResourceSchema):
    description: str = None
    latest_version: Optional["BentoVersionSchema"] = None


@dataclass
class CreateBentoSchema(DataClassJsonMixin):
    name: str = ''
    description: str = ''


class BentoVersionImageBuildStatus(Enum):
    PENDING = 'pending'
    BUILDING = 'building'
    SUCCESS = 'success'
    FAILED = 'failed'


class BentoVersionUploadStatus(Enum):
    PENDING = 'pending'
    BUILDING = 'uploading'
    SUCCESS = 'success'
    FAILED = 'failed'


@dataclass
class BentoVersionManifestSchema(DataClassJsonMixin):
    metadata: BentoMLYamlMetadata = BentoMLYamlMetadata()
    apis: List[BentoMLYamlApi] = field(default_factory=lambda: [])


@dataclass
class BentoVersionSchema(ResourceSchema):
    description: str = ''
    version: str = ''
    image_build_status: BentoVersionImageBuildStatus = ''
    upload_status: BentoVersionUploadStatus = ''
    upload_finished_reason: str = ''
    presigned_s3_url: str = ''
    manifest: BentoVersionManifestSchema = BentoVersionManifestSchema()

    upload_started_at: Optional[datetime] = field(default=None, **datetime_field_kwargs)
    upload_finished_at: Optional[datetime] = field(default=None, **datetime_field_kwargs)
    build_at: datetime = field(default_factory=datetime.now, **datetime_field_kwargs)


@dataclass
class CreateBentoVersionSchema(DataClassJsonMixin):
    description: str = ''
    version: str = ''
    build_at: datetime = field(default_factory=datetime.now, **datetime_field_kwargs)
    manifest: BentoVersionManifestSchema = BentoVersionManifestSchema()


@dataclass
class FinishUploadBentoVersionSchema(DataClassJsonMixin):
    status: Optional[BentoVersionUploadStatus] = None
    reason: Optional[str] = None
