from typing import Optional

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session

from ..crud.secrets import create_secret, get_secret, delete_secret
from ..database import schemas, models
from ..database.config import get_db

router = APIRouter()

@router.post("/", response_model=schemas.SecretResponse)
async def create_new_secret(
    secret_data: schemas.SecretCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    return create_secret(db, secret_data, request.client.host)


@router.get("/{secret_key}", response_model=schemas.SecretReadResponse)
async def api_get_secret(
    secret_key: str,
    request: Request,
    passphrase: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        secret_content = get_secret(
            db=db,
            secret_key=secret_key,
            passphrase=passphrase,  # Передаём passphrase (может быть None)
            ip_address=request.client.host
        )
        return {"secret": secret_content}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete(
    "/{secret_key}",
    response_model=schemas.SecretDeleteResponse,
    status_code=http_status.HTTP_200_OK
)
async def api_delete_secret(
    secret_key: str,
    request: Request,
    db: Session = Depends(get_db)
):
    operation_success, secret_id = delete_secret(db, secret_key, request.client.host)

    if not operation_success:
        log = models.SecretLog(
            secret_id=secret_id,
            secret_key=secret_key,
            action="delete_attempt_failed",
            ip_address=request.client.host
        )
        db.add(log)
        db.commit()

        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Secret not found or already deleted"
        )

    return {"status": "secret_deleted"}