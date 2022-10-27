import json
import logging
from typing import Dict, List, Optional, Union

from pydantic import BaseModel

from databricks_cdk.utils import CnfResponse, get_request, post_request

logger = logging.getLogger(__name__)


Value = Union[int, bool, str]


class PolicyElement(BaseModel):
    type: str
    value: Optional[Value]
    hidden: Optional[bool]
    defaultValue: Optional[Value]
    isOptional: Optional[bool]
    minValue: Optional[int]
    maxValue: Optional[int]
    values: Optional[List[Value]]
    pattern: Optional[str]


class ClusterPolicy(BaseModel):
    name: str
    description: Optional[str]
    definition: Dict[str, PolicyElement]


class ClusterPolicyProperties(BaseModel):
    workspace_url: str
    cluster_policy: ClusterPolicy


def get_cluster_policy_url(workspace_url: str) -> str:
    """Getting url for job requests"""
    return f"{workspace_url}/api/2.0/policies/clusters"


def get_cluster_policy_by_id(cluster_policy_id: str, workspace_url: str) -> Optional[dict]:
    """Getting cluster policy by id"""
    body = {"policy_id": cluster_policy_id}
    resp = get_request(url=f"{get_cluster_policy_url(workspace_url)}/get", body=body)
    return resp


def create_or_update_cluster_policy(
    properties: ClusterPolicyProperties, physical_resource_id: Optional[str]
) -> CnfResponse:
    """Create cluster policy at databricks"""
    current = None
    base_url = get_cluster_policy_url(properties.workspace_url)
    body = json.loads(properties.cluster_policy.json(exclude_none=True))
    body["definition"] = json.dumps(body["definition"])

    if physical_resource_id is not None:
        current = get_cluster_policy_by_id(
            cluster_policy_id=physical_resource_id,
            workspace_url=properties.workspace_url,
        )
    if current is None:
        response = post_request(url=f"{base_url}/create", body=body)
        return CnfResponse(physical_resource_id=response["policy_id"])
    else:
        policy_id = current["policy_id"]
        body["policy_id"] = policy_id
        post_request(url=f"{base_url}/edit", body=body)
    return CnfResponse(physical_resource_id=policy_id)


def delete_cluster_policy(properties: ClusterPolicyProperties, physical_resource_id: str) -> CnfResponse:
    """Deletes cluster policy at databricks"""
    base_url = get_cluster_policy_url(properties.workspace_url)
    current = get_cluster_policy_by_id(physical_resource_id, properties.workspace_url)
    if current is not None:
        body = {"policy_id": current.get("policy_id")}
        post_request(url=f"{base_url}/delete", body=body)
    else:
        logger.warning("Already removed")
    return CnfResponse(physical_resource_id=physical_resource_id)
