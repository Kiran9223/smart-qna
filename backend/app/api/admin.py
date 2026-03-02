import boto3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.core.dependencies import require_role

router = APIRouter(prefix="/admin", tags=["Admin"])


def _cognito_client():
    return boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)


@router.get("/users")
async def list_users(_=Depends(require_role("ADMIN"))):
    client = _cognito_client()
    users_by_group = {}

    for group in ("STUDENT", "TA", "ADMIN"):
        resp = client.list_users_in_group(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            GroupName=group,
        )
        users_by_group[group] = [
            {
                "username": u["Username"],
                "email": next(
                    (a["Value"] for a in u["Attributes"] if a["Name"] == "email"), ""
                ),
                "status": u["UserStatus"],
            }
            for u in resp.get("Users", [])
        ]

    return users_by_group


class RoleUpdate(BaseModel):
    role: str


@router.patch("/users/{username}/role")
async def update_user_role(
    username: str,
    body: RoleUpdate,
    _=Depends(require_role("ADMIN")),
):
    if body.role not in ("STUDENT", "TA", "ADMIN"):
        raise HTTPException(status_code=400, detail="Invalid role")

    client = _cognito_client()
    pool_id = settings.COGNITO_USER_POOL_ID

    # Remove from all groups first, then add to the new one
    for group in ("STUDENT", "TA", "ADMIN"):
        try:
            client.admin_remove_user_from_group(
                UserPoolId=pool_id, Username=username, GroupName=group
            )
        except client.exceptions.ResourceNotFoundException:
            pass

    client.admin_add_user_to_group(
        UserPoolId=pool_id, Username=username, GroupName=body.role
    )

    return {"username": username, "role": body.role}
