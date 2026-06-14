from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
import uuid

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import DuplicateEntityException, EntityNotFoundException, ParentEntityHasActiveChildrenException
from app.models.clientes import Clientes  
from app.models.usuario import Usuario
from app.models.os import OS
from app.schemas.cliente import ClienteCreate, ClientesResponse  


router = APIRouter(prefix="/clientes", tags=["Clientes"])


@router.post("/", response_model=ClientesResponse, status_code=status.HTTP_201_CREATED)
def criar_cliente(
    cliente: ClienteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),  # 🔒 Rota protegida
):
    query_cpf = select(Clientes).where(Clientes.cpf_cnpj == cliente.cpf_cnpj)
    if db.scalars(query_cpf).first():
        raise DuplicateEntityException("CPF/CNPJ", cliente.cpf_cnpj)

    query_email = select(Clientes).where(Clientes.email == cliente.email)
    if db.scalars(query_email).first():
        raise DuplicateEntityException("E-mail", cliente.email)

    novo_cliente = Clientes(
        nome=cliente.nome,
        cpf_cnpj=cliente.cpf_cnpj,
        email=cliente.email,
        telefone=cliente.telefone,
    )
    db.add(novo_cliente)
    db.commit()
    db.refresh(novo_cliente)
    return novo_cliente


@router.get("/", response_model=List[ClientesResponse])
def listar_clientes(
    nome: str | None = Query(None, description="Filtrar clientes por parte do nome"),
    skip: int = Query(0, ge=0, description="Número de registros a pular (offset)"),
    limit: int = Query(10, ge=1, le=100, description="Quantidade máxima de registros a retornar (limit)"),
    db: Session = Depends(get_db),
):
    query = select(Clientes)

    if nome:
        query = query.where(Clientes.nome.ilike(f"%{nome}%"))

    query = query.offset(skip).limit(limit)
    resultado = db.scalars(query).all()

    return resultado


@router.delete("/{idcliente}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_cliente(
    idcliente: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),  # 🔒 Rota protegida
):
    query = select(Clientes).where(Clientes.idcliente == idcliente)
    cliente = db.scalars(query).first()
    if not cliente:
        raise EntityNotFoundException("Cliente", idcliente)

    # Verifica se possui OS ativa (ABERTA ou EM_ANDAMENTO)
    query_active_os = select(OS).where(
        OS.idcliente == idcliente,
        OS.status.in_(["ABERTA", "EM_ANDAMENTO"])
    )
    if db.scalars(query_active_os).first():
        raise ParentEntityHasActiveChildrenException("Cliente", idcliente)

    db.delete(cliente)
    db.commit()
    return None