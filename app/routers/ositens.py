from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.exceptions import (
    EntityNotFoundException,
    InsufficientStockException,
    ModifyTerminalEntityException,
)
from app.models.ositens import OSItens
from app.models.os import OS
from app.models.produtos import Produtos
from app.models.usuario import Usuario
from app.schemas.ositens import OSItensCreate, OSItensResponse

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


@router.post("/", response_model=OSItensResponse, status_code=status.HTTP_201_CREATED)
def adicionar_item(
    item: OSItensCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),  # 🔒 Rota protegida
):
    # 1. Busca e validação da OS
    query_os = select(OS).where(OS.idos == item.idos)
    os_registro = db.scalars(query_os).first()
    if not os_registro:
        raise EntityNotFoundException("Ordem de Serviço", item.idos)

    # 2. Validação: impede modificações se a OS estiver em estado terminal (CONCLUIDA ou CANCELADA)
    if os_registro.status.upper() in ["CONCLUIDA", "CANCELADA"]:
        raise ModifyTerminalEntityException("Ordem de Serviço", item.idos, os_registro.status)

    # 3. Busca e validação do Produto
    query_prod = select(Produtos).where(Produtos.idproduto == item.idproduto)
    produto = db.scalars(query_prod).first()
    if not produto:
        raise EntityNotFoundException("Produto", item.idproduto)

    # 4. Validação: estoque insuficiente
    if produto.quantidade_estoque < item.quantidade:
        raise InsufficientStockException(produto.nome, produto.quantidade_estoque, item.quantidade)

    # 5. Baixa no estoque do produto
    produto.quantidade_estoque -= item.quantidade

    # 6. Adiciona item à OS
    novo_item = OSItens(
        idos=item.idos,
        idproduto=item.idproduto,
        quantidade=item.quantidade,
        preco_unitario_aplicado=item.preco_unitario_aplicado,
    )
    db.add(novo_item)

    # 7. Atualiza o valor total da Ordem de Serviço
    os_registro.valor_total += (item.quantidade * item.preco_unitario_aplicado)

    db.commit()
    db.refresh(novo_item)
    return novo_item