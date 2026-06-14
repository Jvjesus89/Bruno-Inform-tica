from typing import List
from sqlalchemy import String, ForeignKey, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid

class OS(Base):
    __tablename__ = "OS"

    idos: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    idcliente: Mapped[uuid.UUID] = mapped_column(ForeignKey("clientes.idcliente", ondelete="RESTRICT"), nullable=False)
    idequipamento: Mapped[uuid.UUID] = mapped_column(ForeignKey("equipamentos.idequipamento", ondelete="RESTRICT"), nullable=False)
    idtecnico: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    descricao_defeito: Mapped[str] = mapped_column(String(100), unique=True, nullable=True)
    valor_total: Mapped[float] = mapped_column(Numeric(10,2), nullable=False, default=0.0)
    data_abertura: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    data_conclusao: Mapped[DateTime] = mapped_column(DateTime, nullable=True)

    cliente: Mapped["Clientes"] = relationship(back_populates="ordens_servico")

    itens: Mapped[List["OSItens"]] = relationship(
        back_populates="ordem_servico", 
        cascade="all, delete-orphan"
    )