from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from app.core.database import get_db
from app.models.ositens import OSItens
from app.schemas.ositens import OSItensResponse

router = APIRouter(prefix="/ositens", tags=["OSItens"])

@router.get("/", response_model=List[OSItensResponse])
def listar_itens(
    skip: int = Query(0, ge=0, description="Número de registros a pular (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Quantidade máxima de registros a retornar (limit)"),
    db: Session = Depends(get_db)
):
    query = select(OSItens)
    query = query.offset(skip).limit(limit)
    resultado = db.scalars(query).all()
    return resultado