from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import (
    EntityNotFoundException,
    InvalidStatusException,
    InvalidStateTransitionException,
    ModifyTerminalEntityException,
)
from app.models.os import OS
from app.models import Clientes, Equipamento, Usuario
from app.schemas.os import OSCreate, OSResponse

router = APIRouter(prefix="/ordens-servico", tags=["Ordens de Serviço"])

STATUS_PERMITIDOS = ["ABERTA", "EM_ANDAMENTO", "CONCLUIDA", "CANCELADA"]

MAPA_TRANSIÇÕES = {
    "ABERTA": ["EM_ANDAMENTO", "CANCELADA"],
    "EM_ANDAMENTO": ["CONCLUIDA", "CANCELADA"],
    "CONCLUIDA": [], 
    "CANCELADA": []   
}

@router.post("/", response_model=OSResponse, status_code=status.HTTP_201_CREATED)
def criar_os(
    os_input: OSCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),  
):
    query_cliente = select(Clientes).where(Clientes.idcliente == os_input.idcliente)
    if not db.scalars(query_cliente).first():
        raise EntityNotFoundException("Cliente", os_input.idcliente)

    query_equip = select(Equipamento).where(Equipamento.idequipamento == os_input.idequipamento)
    if not db.scalars(query_equip).first():
        raise EntityNotFoundException("Equipamento", os_input.idequipamento)

    query_tec = select(Usuario).where(Usuario.id == os_input.idtecnico)
    if not db.scalars(query_tec).first():
        raise EntityNotFoundException("Técnico", os_input.idtecnico)

    nova_os = OS(
        idcliente=os_input.idcliente,
        idequipamento=os_input.idequipamento,
        idtecnico=os_input.idtecnico,
        status=os_input.status,
        descricao_defeito=os_input.descricao_defeito,
        valor_total=os_input.valor_total
    )
    db.add(nova_os)
    db.commit()
    db.refresh(nova_os)
    return nova_os

@router.get("/{id_os}", response_model=OSResponse)
def buscar_os(id_os: uuid.UUID, db: Session = Depends(get_db)):
    query = select(OS).where(OS.idos == id_os)
    os_registro = db.scalars(query).first()
    if not os_registro:
        raise EntityNotFoundException("Ordem de Serviço", id_os)
    return os_registro

@router.put("/{id_os}/status", status_code=status.HTTP_200_OK)
def atualizar_status_os(
    id_os: uuid.UUID,
    novo_status: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user), 
):
    novo_status = novo_status.upper()
    if novo_status not in STATUS_PERMITIDOS:
        raise InvalidStatusException(novo_status, STATUS_PERMITIDOS)

    query = select(OS).where(OS.idos == id_os)
    os_registro = db.scalars(query).first()

    if not os_registro:
        raise EntityNotFoundException("Ordem de Serviço", id_os)

    status_atual = os_registro.status.upper()

    if status_atual in ["CONCLUIDA", "CANCELADA"]:
        raise ModifyTerminalEntityException("Ordem de Serviço", id_os, status_atual)

    if status_atual == novo_status:
        return {"message": "A OS já está com este status.", "status": status_atual}

    transicoes_possiveis = MAPA_TRANSIÇÕES.get(status_atual, [])
    if novo_status not in transicoes_possiveis:
        raise InvalidStateTransitionException(status_atual, novo_status)

    os_registro.status = novo_status
    db.commit()
    db.refresh(os_registro)

    return {
        "message": "Status atualizado com sucesso!",
        "id_os": os_registro.idos,
        "status_anterior": status_atual,
        "status_atual": os_registro.status
    }
    
@router.get("/", response_model=List[OSResponse])
def listar_OS(
    skip: int = Query(0, ge=0, description="Número de registros a pular (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Quantidade máxima de registros a retornar (limit)"),
    db: Session = Depends(get_db)
):
    query = select(OS)
    if skip > 0:
        query = query.offset(skip)
    if limit > 0:
        query = query.limit(limit)
    resultado = db.scalars(query).all()
    return resultado