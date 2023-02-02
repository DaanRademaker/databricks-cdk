import json
import logging
from typing import Dict, Optional

from pydantic import BaseModel

from databricks_cdk.utils import CnfResponse, delete_request, get_request, patch_request, post_request

logger = logging.getLogger(__name__)


class Catalog(BaseModel):
    name: str
    comment: Optional[str]
    properties: Dict[str, str] = {}
    owner: Optional[str]


class CatalogProperties(BaseModel):
    workspace_url: str
    catalog: Catalog


class CatalogResponse(CnfResponse):
    name: str


def get_catalog_url(workspace_url: str):
    """Getting url for job requests"""
    return f"{workspace_url}/api/2.1/unity-catalog/catalogs"


def get_catalog_by_name(catalog_name: str, base_url: str) -> Optional[dict]:
    return get_request(f"{base_url}/{catalog_name}")


def create_or_update_catalog(properties: CatalogProperties) -> CatalogResponse:
    """Create catalog at databricks"""
    current: Optional[dict] = None
    base_url = get_catalog_url(properties.workspace_url)
    if current is None:
        current = get_catalog_by_name(properties.catalog.name, base_url=base_url)
    if current is None:
        post_request(base_url, body=json.loads(properties.catalog.json()))
    else:
        patch_request(
            f"{base_url}/{properties.catalog.name}",
            body=json.loads(properties.catalog.json()),
        )
    return CatalogResponse(
        name=properties.catalog.name,
        physical_resource_id=properties.catalog.name,
    )


def delete_catalog(properties: CatalogProperties, physical_resource_id: str) -> CnfResponse:
    """Deletes catalog at databricks"""
    base_url = get_catalog_url(properties.workspace_url)
    current = get_catalog_by_name(properties.catalog.name, base_url=base_url)
    if current is not None:
        delete_request(f"{base_url}/{properties.catalog.name}")
    else:
        logger.warning("Already removed")
    return CnfResponse(physical_resource_id=physical_resource_id)
