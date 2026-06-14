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
    resp = client.post("/usuarios/", json=user_payload)
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
    tec_resp = client.post("/usuarios/", json=tec_payload)
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
    os_resp = client.post("/ordens-servico/", json=os_payload, headers=headers)
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
    idtecnico = client.post("/usuarios/", json=tec_payload).json()["id"]

    os_payload = {
        "idcliente": idcliente,
        "idequipamento": idequipamento,
        "idtecnico": idtecnico,
        "status": "ABERTA",
        "descricao_defeito": f"Lentidão extrema {unique_suffix}",
        "valor_total": "150.00"
    }
    os_data = client.post("/ordens-servico/", json=os_payload, headers=headers).json()
    idos = os_data["idos"]

    put_resp = client.put(f"/ordens-servico/{idos}/status?novo_status=EM_ANDAMENTO", headers=headers)
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
    idtecnico = client.post("/usuarios/", json=tec_payload).json()["id"]

    os_payload = {
        "idcliente": idcliente,
        "idequipamento": idequipamento,
        "idtecnico": idtecnico,
        "status": "ABERTA",
        "descricao_defeito": f"Erro de drive {unique_suffix}",
        "valor_total": "200.00"
    }
    os_data = client.post("/ordens-servico/", json=os_payload, headers=headers).json()
    idos = os_data["idos"]

    put_resp = client.put(f"/ordens-servico/{idos}/status?novo_status=CONCLUIDA", headers=headers)
    assert put_resp.status_code == 422
    assert put_resp.json()["detail"] == "Transição de estado inválida. Uma OS 'ABERTA' não pode ser alterada para 'CONCLUIDA'."


# 9. Buscar uma Ordem de Serviço por ID não existente (404)
def test_buscar_os_por_id_nao_existente():
    random_id = uuid.uuid4()
    response = client.get(f"/ordens-servico/{random_id}")
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
    client.post("/usuarios/", json={
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
    client.post("/usuarios/", json={
        "nome": f"Wrong PW {unique_suffix}",
        "email": email,
        "senha": "senha-correta",
        "tipo": "TECNICO",
    })

    # Tenta login com senha errada
    resp = client.post("/auth/token", data={"username": email, "password": "senha-errada"})
    assert resp.status_code == 401
    assert "incorretos" in resp.json()["detail"]


# 14. Tentar deletar cliente ou equipamento com Ordem de Serviço ativa (Erro 400)
def test_deletar_cliente_ou_equipamento_com_os_ativa():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]
    
    # Cria o cliente
    cliente_payload = {
        "nome": f"Cliente Deletar {unique_suffix}",
        "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.del.{unique_suffix}@example.com",
        "telefone": "11999999999"
    }
    cli_resp = client.post("/clientes/", json=cliente_payload, headers=headers)
    idcliente = cli_resp.json()["idcliente"]

    # Cria o equipamento
    equip_payload = {
        "tipo": "Notebook",
        "marca": "HP",
        "modelo": "Elitebook",
        "numero_serie": f"NS-HP-{unique_suffix}",
        "idcliente": idcliente
    }
    equip_resp = client.post("/equipamentos/", json=equip_payload, headers=headers)
    idequipamento = equip_resp.json()["idequipamento"]

    # Cria o técnico
    tec_payload = {
        "nome": f"Tec Del {unique_suffix}",
        "email": f"tec.del.{unique_suffix}@example.com",
        "senha": "senha-segura",
        "tipo": "TECNICO"
    }
    idtecnico = client.post("/usuarios/", json=tec_payload).json()["id"]

    # Cria OS ativa (ABERTA)
    os_payload = {
        "idcliente": idcliente,
        "idequipamento": idequipamento,
        "idtecnico": idtecnico,
        "status": "ABERTA",
        "descricao_defeito": f"Tela piscando {unique_suffix}",
        "valor_total": "0.00"
    }
    client.post("/ordens-servico/", json=os_payload, headers=headers)

    # Tenta deletar cliente (deve falhar)
    del_cli_resp = client.delete(f"/clientes/{idcliente}", headers=headers)
    assert del_cli_resp.status_code == 400
    assert "possui Ordens de Serviço ativas" in del_cli_resp.json()["detail"]

    # Tenta deletar equipamento (deve falhar)
    del_equip_resp = client.delete(f"/equipamentos/{idequipamento}", headers=headers)
    assert del_equip_resp.status_code == 400
    assert "possui Ordens de Serviço ativas" in del_equip_resp.json()["detail"]


# 15. Deletar cliente ou equipamento sem Ordem de Serviço ativa (Sucesso 204)
def test_deletar_cliente_ou_equipamento_sem_os_ativa():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]
    
    # Cria o cliente
    cliente_payload = {
        "nome": f"Cliente Sucesso {unique_suffix}",
        "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.suc.{unique_suffix}@example.com",
        "telefone": "11999999999"
    }
    idcliente = client.post("/clientes/", json=cliente_payload, headers=headers).json()["idcliente"]

    # Cria o equipamento
    equip_payload = {
        "tipo": "Tablet",
        "marca": "Apple",
        "modelo": "iPad Air",
        "numero_serie": f"NS-IPAD-{unique_suffix}",
        "idcliente": idcliente
    }
    idequipamento = client.post("/equipamentos/", json=equip_payload, headers=headers).json()["idequipamento"]

    # Deleta equipamento primeiro
    del_equip_resp = client.delete(f"/equipamentos/{idequipamento}", headers=headers)
    assert del_equip_resp.status_code == 204

    # Deleta cliente
    del_cli_resp = client.delete(f"/clientes/{idcliente}", headers=headers)
    assert del_cli_resp.status_code == 204


# 16. Adicionar item à OS com estoque insuficiente (Erro 400)
def test_adicionar_item_os_estoque_insuficiente():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]

    # Cria cliente, equipamento, técnico e OS
    idcliente = client.post("/clientes/", json={
        "nome": f"Cli Est {unique_suffix}", "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.est.{unique_suffix}@example.com", "telefone": "11999999999"
    }, headers=headers).json()["idcliente"]

    idequipamento = client.post("/equipamentos/", json={
        "tipo": "Notebook", "marca": "Dell", "modelo": "XPS",
        "numero_serie": f"NS-XPS-{unique_suffix}", "idcliente": idcliente
    }, headers=headers).json()["idequipamento"]

    idtecnico = client.post("/usuarios/", json={
        "nome": f"Tec Est {unique_suffix}", "email": f"tec.est.{unique_suffix}@example.com",
        "senha": "senha", "tipo": "TECNICO"
    }).json()["id"]

    idos = client.post("/ordens-servico/", json={
        "idcliente": idcliente, "idequipamento": idequipamento, "idtecnico": idtecnico,
        "status": "ABERTA", "descricao_defeito": f"Defeito {unique_suffix}", "valor_total": "0.00"
    }, headers=headers).json()["idos"]

    # Cria produto com estoque de 3 unidades
    prod_resp = client.post("/produtos/", json={
        "nome": f"Memória RAM DDR4 {unique_suffix}",
        "descricao": "Pente de memória 8GB",
        "preco_venda": "250.00",
        "quantidade_estoque": 3
    }, headers=headers)
    idproduto = prod_resp.json()["idproduto"]

    # Tenta adicionar item à OS com quantidade de 5 unidades (maior que o estoque de 3)
    item_payload = {
        "idos": idos,
        "idproduto": idproduto,
        "quantidade": 5,
        "preco_unitario_aplicado": "250.00"
    }
    item_resp = client.post("/ositens/", json=item_payload, headers=headers)
    assert item_resp.status_code == 400
    assert "Estoque insuficiente" in item_resp.json()["detail"]


# 17. Adicionar item à OS com sucesso e verificar a baixa de estoque (Sucesso 201)
def test_adicionar_item_os_sucesso_e_baixa_estoque():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]

    # Cria cliente, equipamento, técnico e OS
    idcliente = client.post("/clientes/", json={
        "nome": f"Cli Ok {unique_suffix}", "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.ok.{unique_suffix}@example.com", "telefone": "11999999999"
    }, headers=headers).json()["idcliente"]

    idequipamento = client.post("/equipamentos/", json={
        "tipo": "Notebook", "marca": "Dell", "modelo": "Latitude",
        "numero_serie": f"NS-LAT-{unique_suffix}", "idcliente": idcliente
    }, headers=headers).json()["idequipamento"]

    idtecnico = client.post("/usuarios/", json={
        "nome": f"Tec Ok {unique_suffix}", "email": f"tec.ok.{unique_suffix}@example.com",
        "senha": "senha", "tipo": "TECNICO"
    }).json()["id"]

    os_data = client.post("/ordens-servico/", json={
        "idcliente": idcliente, "idequipamento": idequipamento, "idtecnico": idtecnico,
        "status": "ABERTA", "descricao_defeito": f"Defeito OK {unique_suffix}", "valor_total": "0.00"
    }, headers=headers).json()
    idos = os_data["idos"]

    # Cria produto com estoque de 10 unidades
    idproduto = client.post("/produtos/", json={
        "nome": f"SSD NVMe 1TB {unique_suffix}",
        "descricao": "SSD Samsung Evo",
        "preco_venda": "450.00",
        "quantidade_estoque": 10
    }, headers=headers).json()["idproduto"]

    # Adiciona item com quantidade 2
    item_payload = {
        "idos": idos,
        "idproduto": idproduto,
        "quantidade": 2,
        "preco_unitario_aplicado": "450.00"
    }
    item_resp = client.post("/ositens/", json=item_payload, headers=headers)
    assert item_resp.status_code == 201

    # Verifica se a Ordem de Serviço teve o valor total atualizado (2 * 450 = 900)
    os_get = client.get(f"/ordens-servico/{idos}", headers=headers).json()
    assert float(os_get["valor_total"]) == 900.00

    # Verifica se a quantidade no estoque do produto diminuiu para 8 (10 - 2)
    prod_list = client.get(f"/produtos/?nome=SSD%20NVMe%201TB%20{unique_suffix}", headers=headers).json()
    assert len(prod_list) == 1
    assert prod_list[0]["quantidade_estoque"] == 8


# 18. Tentar adicionar item a uma OS em estado terminal (Erro 400)
def test_adicionar_item_os_estado_terminal():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]

    # Cria cliente, equipamento, técnico e OS
    idcliente = client.post("/clientes/", json={
        "nome": f"Cli Term {unique_suffix}", "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.term.{unique_suffix}@example.com", "telefone": "11999999999"
    }, headers=headers).json()["idcliente"]

    idequipamento = client.post("/equipamentos/", json={
        "tipo": "Notebook", "marca": "Dell", "modelo": "Vostro",
        "numero_serie": f"NS-VOS-{unique_suffix}", "idcliente": idcliente
    }, headers=headers).json()["idequipamento"]

    idtecnico = client.post("/usuarios/", json={
        "nome": f"Tec Term {unique_suffix}", "email": f"tec.term.{unique_suffix}@example.com",
        "senha": "senha", "tipo": "TECNICO"
    }).json()["id"]

    idos = client.post("/ordens-servico/", json={
        "idcliente": idcliente, "idequipamento": idequipamento, "idtecnico": idtecnico,
        "status": "ABERTA", "descricao_defeito": f"Defeito Term {unique_suffix}", "valor_total": "0.00"
    }, headers=headers).json()["idos"]

    # Cria produto
    idproduto = client.post("/produtos/", json={
        "nome": f"Cabo HDMI {unique_suffix}",
        "descricao": "Cabo HDMI 2m",
        "preco_venda": "30.00",
        "quantidade_estoque": 10
    }, headers=headers).json()["idproduto"]

    # Avança OS para EM_ANDAMENTO
    client.put(f"/ordens-servico/{idos}/status?novo_status=EM_ANDAMENTO", headers=headers)
    # Conclui a OS (estado terminal)
    client.put(f"/ordens-servico/{idos}/status?novo_status=CONCLUIDA", headers=headers)

    # Tenta adicionar item à OS concluída
    item_payload = {
        "idos": idos,
        "idproduto": idproduto,
        "quantidade": 1,
        "preco_unitario_aplicado": "30.00"
    }
    item_resp = client.post("/ositens/", json=item_payload, headers=headers)
    assert item_resp.status_code == 400
    assert "estado terminal" in item_resp.json()["detail"]


# 19. Tentar modificar status de OS já em estado terminal (Erro 400)
def test_modificar_status_os_estado_terminal():
    headers = _create_user_and_get_token()
    unique_suffix = uuid.uuid4().hex[:6]

    # Cria cliente, equipamento, técnico e OS
    idcliente = client.post("/clientes/", json={
        "nome": f"Cli StTerm {unique_suffix}", "cpf_cnpj": generate_random_cpf(),
        "email": f"cli.stt.{unique_suffix}@example.com", "telefone": "11999999999"
    }, headers=headers).json()["idcliente"]

    idequipamento = client.post("/equipamentos/", json={
        "tipo": "Notebook", "marca": "Dell", "modelo": "Precision",
        "numero_serie": f"NS-PRE-{unique_suffix}", "idcliente": idcliente
    }, headers=headers).json()["idequipamento"]

    idtecnico = client.post("/usuarios/", json={
        "nome": f"Tec StTerm {unique_suffix}", "email": f"tec.stt.{unique_suffix}@example.com",
        "senha": "senha", "tipo": "TECNICO"
    }).json()["id"]

    idos = client.post("/ordens-servico/", json={
        "idcliente": idcliente, "idequipamento": idequipamento, "idtecnico": idtecnico,
        "status": "ABERTA", "descricao_defeito": f"Defeito StTerm {unique_suffix}", "valor_total": "0.00"
    }, headers=headers).json()["idos"]

    # Cancela a OS (estado terminal)
    client.put(f"/ordens-servico/{idos}/status?novo_status=CANCELADA", headers=headers)

    # Tenta reabrir a OS (mudar para ABERTA)
    put_resp = client.put(f"/ordens-servico/{idos}/status?novo_status=ABERTA", headers=headers)
    assert put_resp.status_code == 400
    assert "estado terminal" in put_resp.json()["detail"]

