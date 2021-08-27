import logging
from typing import Optional
from urllib.parse import urljoin

import requests

from yataicli.errors import YataiCliError
from yataicli.schemas import UserSchema, BentoSchema, CreateBentoSchema, CreateBentoVersionSchema, BentoVersionSchema, \
    OrganizationListSchema, FinishUploadBentoVersionSchema

logger = logging.getLogger(__name__)


class YataiClient:
    def __init__(self, endpoint: str, api_token: str) -> None:
        self.endpoint = endpoint
        self.session = requests.Session()
        self.session.headers.update({
            'X-YATAI-API-TOKEN': api_token,
            'Content-Type': 'application/json',
        })

    def _is_not_found(self, resp: requests.Response) -> bool:
        # Forgive me, I don't know how to map the error returned by gorm to juju/errors
        return resp.status_code == 400 and 'record not found' in resp.text

    def _check_resp(self, resp: requests.Response) -> None:
        if resp.status_code != 200:
            raise YataiCliError(f'request failed with status code {resp.status_code}: {resp.text}')

    def get_current_user(self) -> Optional[UserSchema]:
        url = urljoin(self.endpoint, '/api/v1/auth/current')
        resp = self.session.get(url)
        if self._is_not_found(resp):
            return None
        self._check_resp(resp)
        return UserSchema.from_json(resp.text)

    def list_organizations(self, start: int, count: int) -> OrganizationListSchema:
        url = urljoin(self.endpoint, '/api/v1/orgs')
        resp = self.session.get(url, params={
            'start': start,
            'count': count,
        })
        self._check_resp(resp)
        return OrganizationListSchema.from_json(resp.text)

    def get_bento(self, org_name: str, bento_name: str) -> Optional[BentoSchema]:
        url = urljoin(self.endpoint, f'/api/v1/orgs/{org_name}/bentos/{bento_name}')
        resp = self.session.get(url)
        if self._is_not_found(resp):
            return None
        self._check_resp(resp)
        return BentoSchema.from_json(resp.text)

    def create_bento(self, org_name: str, req: CreateBentoSchema) -> BentoSchema:
        url = urljoin(self.endpoint, f'/api/v1/orgs/{org_name}/bentos')
        resp = self.session.post(url, data=req.to_json())
        self._check_resp(resp)
        return BentoSchema.from_json(resp.text)

    def get_bento_version(self, org_name: str, bento_name: str, version: str) -> Optional[BentoVersionSchema]:
        url = urljoin(self.endpoint, f'/api/v1/orgs/{org_name}/bentos/{bento_name}/versions/{version}')
        resp = self.session.get(url)
        if self._is_not_found(resp):
            return None
        self._check_resp(resp)
        return BentoVersionSchema.from_json(resp.text)

    def create_bento_version(self, org_name: str, bento_name: str, req: CreateBentoVersionSchema) -> BentoVersionSchema:
        url = urljoin(self.endpoint, f'/api/v1/orgs/{org_name}/bentos/{bento_name}/versions')
        resp = self.session.post(url, data=req.to_json())
        self._check_resp(resp)
        return BentoVersionSchema.from_json(resp.text)

    def presign_bento_version_s3_upload_url(self, org_name: str, bento_name: str, version: str) -> BentoVersionSchema:
        url = urljoin(self.endpoint, f'/api/v1/orgs/{org_name}/bentos/{bento_name}/versions/{version}/presign_s3_upload_url')
        resp = self.session.patch(url)
        self._check_resp(resp)
        return BentoVersionSchema.from_json(resp.text)

    def start_upload_bento_version(self, org_name: str, bento_name: str, version: str) -> BentoVersionSchema:
        url = urljoin(self.endpoint, f'/api/v1/orgs/{org_name}/bentos/{bento_name}/versions/{version}/start_upload')
        resp = self.session.patch(url)
        self._check_resp(resp)
        return BentoVersionSchema.from_json(resp.text)

    def finish_upload_bento_version(self, org_name: str, bento_name: str, version: str,
                                    req: FinishUploadBentoVersionSchema) -> BentoVersionSchema:
        url = urljoin(self.endpoint, f'/api/v1/orgs/{org_name}/bentos/{bento_name}/versions/{version}/finish_upload')
        resp = self.session.patch(url, data=req.to_json())
        self._check_resp(resp)
        return BentoVersionSchema.from_json(resp.text)
