from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import DuplicateEntityException
from app.models.produtos import Produtos
from app.models.usuario import Usuario
from app.schemas.produtos import ProdutoCreate, ProdutoResponse

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.post("/", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
def criar_produto(
    produto: ProdutoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    query_nome = select(Produtos).where(Produtos.nome == produto.nome)
    if db.scalars(query_nome).first():
        raise DuplicateEntityException("Produto com este nome", produto.nome)

    novo_produto = Produtos(
        nome=produto.nome,
        descricao=produto.descricao,
        preco_venda=produto.preco_venda,
        quantidade_estoque=produto.quantidade_estoque,
    )
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto


@router.get("/", response_model=List[ProdutoResponse])
def listar_produtos(
    nome: str | None = Query(None),
    preco_maximo: float | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = select(Produtos)
    if nome:
        query = query.where(Produtos.nome.ilike(f"%{nome}%"))
    if preco_maximo:
        query = query.where(Produtos.preco_venda <= preco_maximo)
    query = query.offset(skip).limit(limit)
    resultado = db.scalars(query).all()
    return resultado