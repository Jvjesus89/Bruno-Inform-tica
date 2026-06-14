from fastapi.testclient import TestClient
from app.main import app
import uuid
import random

client = TestClient(app)


# ──────────────────────────────────────────────────────────────
# Helper: obtém token JWT para autenticar nas rotas protegidas
# ──────────────────────────────────────────────────────────────

def _create_user_and_get_token() -> dict:
    """
    Cria um usuário único e faz login para obter o token JWT.
    Retorna os headers com Authorization: Bearer <token>.
    """
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"testuser.{unique_suffix}@test.com"
    senha = "senha-segura-123"

    # 1. Cria o usuário (rota pública)
    user_payload = {
        "nome": f"Test User {unique_suffix}",
        "email": email,
        "senha": senha,
        "tipo": "TECNICO",
    }
    resp = client.post("/usuario/", json=user_payload)
    assert resp.status_code == 201, f"Falha ao criar usuário de teste: {resp.text}"

    # 2. Faz login para obter o token
    login_resp = client.post(
        "/auth/token",
        data={"username": email, "password": senha},
    )
    assert login_resp.status_code == 200, f"Falha no login: {login_resp.text}"
    token = login_resp.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def generate_random_cpf() -> str:
    # Gera 11 dígitos numéricos aleatórios válidos para passar na validação Pydantic
    return "".join(str(random.randint(0, 9)) for _ in range(11))


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Bem-vindo à Bruno Informática!",
        "docs_url": "/docs",
        "status": "Online"
    }


# 1. Cadastrar um cliente com dados válidos
def test_criar_cliente_sucesso():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]
    payload = {
        "nome": f"Cliente Teste {unique_suffix}",
        "cpf_cnpj": generate_random_cpf(),
        "email": f"cliente.teste.{unique_suffix}@example.com",
        "telefone": "11999999999"
    }
    response = client.post("/clientes/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == payload["nome"]
    assert "idcliente" in data


# 2. Tentar cadastrar um cliente com CPF inválido (menos ou mais dígitos)
def test_criar_cliente_cpf_invalido():
    headers = _create_user_and_get_token()
    payload = {
        "nome": "Cliente CPF Erro",
        "cpf_cnpj": "12345",  # menos que 11 dígitos
        "email": "cliente.erro@example.com",
        "telefone": "11999999999"
    }
    response = client.post("/clientes/", json=payload, headers=headers)
    assert response.status_code == 422


# 3. Listar clientes e verificar se retorna lista
def test_listar_clientes():
    response = client.get("/clientes/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# 4. Cadastrar um produto com preço e estoque válidos
def test_cadastrar_produto_sucesso():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]
    payload = {
        "nome": f"Produto Teste {unique_suffix}",
        "descricao": "Descricao do produto teste",
        "preco_venda": "150.00",
        "quantidade_estoque": 10
    }
    response = client.post("/produtos/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["nome"] == payload["nome"]
    assert "idproduto" in data


# 5. Tentar cadastrar um produto com preço negativo
def test_cadastrar_produto_preco_negativo():
    headers = _create_user_and_get_token()
    payload = {
        "nome": "Mouse Preço Inválido",
        "descricao": "Mouse de teste",
        "preco_venda": "-10.00", 
        "quantidade_estoque": 2
    }
    response = client.post("/produtos/", json=payload, headers=headers)
    assert response.status_code == 422


# 6. Abrir uma Ordem de Serviço com cliente, produto, equipamento e técnico (Status inicial: ABERTA)
def test_criar_os_sucesso():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]
    
    cliente_payload = {
        "nome": f"Cliente OS {unique_suffix}",
        "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.os.{unique_suffix}@example.com",
        "telefone": "11999999999"
    }
    cli_resp = client.post("/clientes/", json=cliente_payload, headers=headers)
    assert cli_resp.status_code == 201
    idcliente = cli_resp.json()["idcliente"]

    equip_payload = {
        "tipo": "Notebook",
        "marca": "Dell",
        "modelo": "Inspiron",
        "numero_serie": f"NS-{unique_suffix}",
        "idcliente": idcliente
    }
    equip_resp = client.post("/equipamentos/", json=equip_payload, headers=headers)
    assert equip_resp.status_code == 201
    idequipamento = equip_resp.json()["idequipamento"]

    tec_payload = {
        "nome": f"Técnico OS {unique_suffix}",
        "email": f"tec.os.{unique_suffix}@example.com",
        "senha": "senha-segura",
        "tipo": "TECNICO"
    }
    tec_resp = client.post("/usuario/", json=tec_payload)
    assert tec_resp.status_code == 201
    idtecnico = tec_resp.json()["id"]

    os_payload = {
        "idcliente": idcliente,
        "idequipamento": idequipamento,
        "idtecnico": idtecnico,
        "status": "ABERTA",
        "descricao_defeito": f"Problema {unique_suffix}",
        "valor_total": "0.00"
    }
    os_resp = client.post("/os/", json=os_payload, headers=headers)
    assert os_resp.status_code == 201
    data = os_resp.json()
    assert data["status"] == "ABERTA"
    assert "idos" in data


# 7. Mudar o status da OS de ABERTA para EM_ANDAMENTO (Sucesso)
def test_transicao_status_sucesso():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]
    
    cliente_payload = {
        "nome": f"Cliente Transição {unique_suffix}",
        "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.trans.{unique_suffix}@example.com",
        "telefone": "11999999999"
    }
    idcliente = client.post("/clientes/", json=cliente_payload, headers=headers).json()["idcliente"]

    equip_payload = {
        "tipo": "Desktop",
        "marca": "Asus",
        "modelo": "ROG",
        "numero_serie": f"NS-ROG-{unique_suffix}",
        "idcliente": idcliente
    }
    idequipamento = client.post("/equipamentos/", json=equip_payload, headers=headers).json()["idequipamento"]

    tec_payload = {
        "nome": f"Tec Trans {unique_suffix}",
        "email": f"tec.trans.{unique_suffix}@example.com",
        "senha": "senha-segura",
        "tipo": "TECNICO"
    }
    idtecnico = client.post("/usuario/", json=tec_payload).json()["id"]

    os_payload = {
        "idcliente": idcliente,
        "idequipamento": idequipamento,
        "idtecnico": idtecnico,
        "status": "ABERTA",
        "descricao_defeito": f"Lentidão extrema {unique_suffix}",
        "valor_total": "150.00"
    }
    os_data = client.post("/os/", json=os_payload, headers=headers).json()
    idos = os_data["idos"]

    put_resp = client.put(f"/os/{idos}/status?novo_status=EM_ANDAMENTO", headers=headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["status_atual"] == "EM_ANDAMENTO"


# 8. Mudar o status pulando o fluxo lógico (Transição inválida)
def test_transicao_status_invalida():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]
    
    cliente_payload = {
        "nome": f"Cliente Falha {unique_suffix}",
        "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.falha.{unique_suffix}@example.com",
        "telefone": "11999999999"
    }
    idcliente = client.post("/clientes/", json=cliente_payload, headers=headers).json()["idcliente"]

    equip_payload = {
        "tipo": "Console",
        "marca": "Sony",
        "modelo": "PS5",
        "numero_serie": f"NS-PS5-{unique_suffix}",
        "idcliente": idcliente
    }
    idequipamento = client.post("/equipamentos/", json=equip_payload, headers=headers).json()["idequipamento"]

    tec_payload = {
        "nome": f"Tec Falha {unique_suffix}",
        "email": f"tec.falha.{unique_suffix}@example.com",
        "senha": "senha-segura",
        "tipo": "TECNICO"
    }
    idtecnico = client.post("/usuario/", json=tec_payload).json()["id"]

    os_payload = {
        "idcliente": idcliente,
        "idequipamento": idequipamento,
        "idtecnico": idtecnico,
        "status": "ABERTA",
        "descricao_defeito": f"Erro de drive {unique_suffix}",
        "valor_total": "200.00"
    }
    os_data = client.post("/os/", json=os_payload, headers=headers).json()
    idos = os_data["idos"]

    put_resp = client.put(f"/os/{idos}/status?novo_status=CONCLUIDA", headers=headers)
    assert put_resp.status_code == 422
    assert "Transição de estado inválida" in put_resp.json()["detail"]


# 9. Buscar uma Ordem de Serviço por ID não existente (404)
def test_buscar_os_por_id_nao_existente():
    random_id = uuid.uuid4()
    response = client.get(f"/os/{random_id}")
    assert response.status_code == 404


# 10. Buscar produtos passando parâmetros de busca na URL (Filtros)
def test_listar_produtos_com_filtro():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]
    p1 = {
        "nome": f"Gamer Mouse {unique_suffix}",
        "descricao": "Mouse Gamer USB",
        "preco_venda": "80.00",
        "quantidade_estoque": 10
    }
    p2 = {
        "nome": f"Monitor 4K Asus {unique_suffix}",
        "descricao": "Monitor Gamer Asus 27",
        "preco_venda": "2500.00",
        "quantidade_estoque": 2
    }
    client.post("/produtos/", json=p1, headers=headers)
    client.post("/produtos/", json=p2, headers=headers)

    resp_nome = client.get(f"/produtos/?nome=Asus%20{unique_suffix}")
    assert resp_nome.status_code == 200
    produtos_nome = resp_nome.json()
    assert len(produtos_nome) == 1
    assert produtos_nome[0]["nome"] == p2["nome"]

    resp_preco = client.get(f"/produtos/?preco_maximo=100.00")
    assert resp_preco.status_code == 200
    produtos_preco = resp_preco.json()
    assert len(produtos_preco) >= 1
    for prod in produtos_preco:
        assert float(prod["preco_venda"]) <= 100.00


# 11. Tentar acessar rota protegida sem token (deve retornar 401)
def test_rota_protegida_sem_token():
    payload = {
        "nome": "Cliente Sem Auth",
        "cpf_cnpj": generate_random_cpf(),
        "email": f"sem.auth.{uuid.uuid4().hex[:6]}@example.com",
        "telefone": "11999999999"
    }
    response = client.post("/clientes/", json=payload)
    assert response.status_code == 401


# 12. Fazer login e verificar o token JWT
def test_login_sucesso():
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"login.test.{unique_suffix}@test.com"
    senha = "minha-senha-123"

    # Cria o usuário
    client.post("/usuario/", json={
        "nome": f"Login Test {unique_suffix}",
        "email": email,
        "senha": senha,
        "tipo": "TECNICO",
    })

    # Faz login
    resp = client.post("/auth/token", data={"username": email, "password": senha})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# 13. Tentar login com senha errada
def test_login_senha_incorreta():
    unique_suffix = uuid.uuid4().hex[:8]
    email = f"wrongpw.{unique_suffix}@test.com"

    # Cria o usuário
    client.post("/usuario/", json={
        "nome": f"Wrong PW {unique_suffix}",
        "email": email,
        "senha": "senha-correta",
        "tipo": "TECNICO",
    })

    # Tenta login com senha errada
    resp = client.post("/auth/token", data={"username": email, "password": "senha-errada"})
    assert resp.status_code == 401
    assert "incorretos" in resp.json()["detail"]
