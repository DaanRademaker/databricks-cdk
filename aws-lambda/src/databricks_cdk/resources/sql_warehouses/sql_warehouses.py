import logging
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from databricks_cdk.utils import CnfResponse, delete_request, get_request, post_request

logger = logging.getLogger(__name__)


class WarehouseTagPairs(BaseModel):
    key: str
    value: str


class WarehouseTags(BaseModel):
    custom_tags: List[WarehouseTagPairs]


class Channel(BaseModel):
    name: str


class SQLWarehouse(BaseModel):
    name: str
    cluster_size: str
    min_num_clusters: Optional[int] = None
    max_num_clusters: int
    auto_stop_mins: Optional[int] = None
    tags: Optional[WarehouseTags] = None
    spot_instance_policy: Optional[str] = None
    enable_photon: Optional[bool] = None
    enable_serverless_compute: Optional[bool] = None
    channel: Optional[Channel] = None


class SQLWarehouseEdit(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    cluster_size: Optional[str] = None
    min_num_clusters: Optional[int] = None
    max_num_clusters: Optional[int] = None
    auto_stop_mins: Optional[int] = None
    tags: Optional[WarehouseTags] = None
    spot_instance_policy: Optional[str] = None
    enable_photon: Optional[bool] = None
    enable_serverless_compute: Optional[bool] = None
    channel: Optional[Channel] = None


class SQLWarehouseProperties(BaseModel):
    action: str = "warehouse"
    workspace_url: str
    warehouse: SQLWarehouse


class SQLWarehouseResponse(CnfResponse):
    id: str


def get_warehouse_url(workspace_url: str):
    """Getting url for SQL Warehouse requests"""
    return f"{workspace_url}/api/2.0/sql/warehouses/"


def get_warehouse_by_name(warehouse_name: str, workspace_url: str) -> Optional[dict]:
    """Getting warehouse by name"""
    all_warehouses = get_request(f"{workspace_url}/api/2.0/sql/warehouses/")["warehouses"]

    for warehouse_dict in all_warehouses:
        if warehouse_name == warehouse_dict["name"]:
            return warehouse_dict

    return None


def create_or_update_warehouse(properties: SQLWarehouseProperties, physical_resource_id: Optional[str]):
    """Create or update warehouse at Databricks"""
    url = get_warehouse_url(properties.workspace_url)
    current: Optional[dict] = None
    warehouse_properties = properties.warehouse

    if physical_resource_id is not None:
        current = get_warehouse_by_name(warehouse_properties.name, properties.workspace_url)

    if current is None:
        create_response = post_request(url=url, body=warehouse_properties.dict())
        warehouse_id = create_response.get("id")
        return SQLWarehouseResponse(id=warehouse_id, physical_resource_id=warehouse_id)
    else:
        warehouse_id = current.get("id")
        warehouse_edit = SQLWarehouseEdit(
            id=warehouse_id,
            name=warehouse_properties.name,
            cluster_size=warehouse_properties.cluster_size,
            min_num_clusters=warehouse_properties.min_num_clusters,
            max_num_clusters=warehouse_properties.max_num_clusters,
            auto_stop_mins=warehouse_properties.auto_stop_mins,
            tags=warehouse_properties.tags,
            spot_instance_policy=warehouse_properties.spot_instance_policy,
            enable_photon=warehouse_properties.enable_photon,
            enable_serverless_compute=warehouse_properties.enable_serverless_compute,
            channel=warehouse_properties.channel,
        )

        post_request(f"{url}{warehouse_id}/edit", body=warehouse_edit.dict())
        return SQLWarehouseResponse(id=warehouse_id, physical_resource_id=warehouse_id)


def delete_warehouse(properties: SQLWarehouseProperties, physical_resource_id: str):
    """Delete warehouse at databricks"""
    current = get_warehouse_by_name(properties.warehouse.name, properties.workspace_url)

    if current is not None:
        delete_request(f"{get_warehouse_url(properties.workspace_url)}{physical_resource_id}")
    else:
        logger.warning("Already removed")

    return CnfResponse(physical_resource_id=physical_resource_id)
