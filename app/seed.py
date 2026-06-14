from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.models.clientes import Clientes
from app.models.produtos import Produtos
from app.models.equipamento import Equipamento
from app.models.os import OS


def seed_database():
    """Insere dados iniciais no banco se ele estiver vazio."""
    db: Session = SessionLocal()
    try:
        # Verifica se já existem usuários — se sim, o seed já rodou
        count = db.scalar(select(func.count()).select_from(Usuario))
        if count and count > 0:
            print("Seed: Banco já possui dados, pulando inserção.")
            return

        print("=" * 60)
        print("Seed: Inserindo dados iniciais...")
        print("=" * 60)

        # ── Usuários (Técnicos e Admin) ──────────────────────────
        admin = Usuario(
            nome="Administrador",
            email="admin@bruno.com",
            senha=hash_password("admin123"),
            tipo="ADMIN",
        )
        tecnico1 = Usuario(
            nome="Carlos Técnico",
            email="tecnico@bruno.com",
            senha=hash_password("tecnico123"),
            tipo="TECNICO",
        )
        db.add_all([admin, tecnico1])
        db.flush() 

        # ── Clientes ─────────────────────────────────────────────
        cliente1 = Clientes(
            nome="João Silva",
            cpf_cnpj="12345678901",
            email="joao.silva@email.com",
            telefone="11999990001",
        )
        cliente2 = Clientes(
            nome="Maria Oliveira",
            cpf_cnpj="98765432100",
            email="maria.oliveira@email.com",
            telefone="11999990002",
        )
        cliente3 = Clientes(
            nome="Pedro Santos",
            cpf_cnpj="11122233344",
            email="pedro.santos@email.com",
            telefone="11999990003",
        )
        db.add_all([cliente1, cliente2, cliente3])
        db.flush()

        # ── Produtos ─────────────────────────────────────────────
        produtos = [
            Produtos(
                nome="Mouse Gamer Logitech G502",
                descricao="Mouse óptico com sensor HERO 25K",
                preco_venda=299.90,
                quantidade_estoque=15,
            ),
            Produtos(
                nome="Teclado Mecânico Redragon Kumara",
                descricao="Teclado mecânico switch azul, TKL",
                preco_venda=189.90,
                quantidade_estoque=10,
            ),
            Produtos(
                nome="Monitor LG 24'' IPS Full HD",
                descricao="Monitor IPS 75Hz com ajuste de altura",
                preco_venda=899.90,
                quantidade_estoque=5,
            ),
            Produtos(
                nome="SSD Kingston A400 480GB",
                descricao="SSD SATA III 2.5'' - Leitura 500MB/s",
                preco_venda=219.90,
                quantidade_estoque=20,
            ),
        ]
        db.add_all(produtos)
        db.flush()

        # ── Equipamentos ─────────────────────────────────────────
        equip1 = Equipamento(
            tipo="Notebook",
            marca="Dell",
            modelo="Inspiron 15 3000",
            numero_serie="DELL-NS-001",
            idcliente=cliente1.idcliente,
        )
        equip2 = Equipamento(
            tipo="Desktop",
            marca="Montado",
            modelo="PC Gamer i5 12400F",
            numero_serie="CUSTOM-NS-002",
            idcliente=cliente2.idcliente,
        )
        db.add_all([equip1, equip2])
        db.flush()

        # ── Ordens de Serviço ────────────────────────────────────
        os1 = OS(
            idcliente=cliente1.idcliente,
            idequipamento=equip1.idequipamento,
            idtecnico=tecnico1.id,
            status="ABERTA",
            descricao_defeito="Notebook não liga após queda",
            valor_total=0.00,
        )
        os2 = OS(
            idcliente=cliente2.idcliente,
            idequipamento=equip2.idequipamento,
            idtecnico=tecnico1.id,
            status="EM_ANDAMENTO",
            descricao_defeito="PC reiniciando sozinho, possível superaquecimento",
            valor_total=150.00,
        )
        db.add_all([os1, os2])

        db.commit()
        print("Seed: Dados iniciais inseridos com sucesso!")
        print(f"  → 2 Usuários (admin@bruno.com / tecnico@bruno.com)")
        print(f"  → 3 Clientes")
        print(f"  → 4 Produtos")
        print(f"  → 2 Equipamentos")
        print(f"  → 2 Ordens de Serviço")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"Seed: ERRO ao inserir dados iniciais: {e}")
    finally:
        db.close()
