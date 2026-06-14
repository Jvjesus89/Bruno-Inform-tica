class EntityNotFoundException(Exception):
    """Entidade não encontrada no banco de dados."""

    def __init__(self, entity_name: str, entity_id: str):
        self.entity_name = entity_name
        self.entity_id = str(entity_id)
        super().__init__(f"{entity_name} com ID '{entity_id}' não encontrado(a).")


class DuplicateEntityException(Exception):
    """Violação de unicidade (CPF, e-mail, nome, número de série, etc.)."""

    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"{field} '{value}' já cadastrado(a).")


class InvalidStateTransitionException(Exception):
    """Transição de status inválida na máquina de estados da OS."""

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Transição de estado inválida. "
            f"Uma OS '{current_status}' não pode ser alterada para '{target_status}'."
        )


class InvalidStatusException(Exception):
    """Status enviado não faz parte do enum permitido."""

    def __init__(self, status: str, allowed: list[str]):
        self.status = status
        self.allowed = allowed
        super().__init__(
            f"Status inválido: '{status}'. Escolha entre: {', '.join(allowed)}"
        )


class AuthenticationException(Exception):
    """Credenciais inválidas no login."""

    def __init__(self, detail: str = "E-mail ou senha incorretos."):
        self.detail = detail
        super().__init__(detail)


class ParentEntityHasActiveChildrenException(Exception):
    """Entidade pai possui filhos ativos e não pode ser deletada."""

    def __init__(self, parent_name: str, parent_id: str):
        self.parent_name = parent_name
        self.parent_id = str(parent_id)
        super().__init__(
            f"Não é possível excluir o(a) {parent_name} com ID '{parent_id}' pois possui Ordens de Serviço ativas."
        )


class InsufficientStockException(Exception):
    """Estoque insuficiente para a quantidade solicitada do produto."""

    def __init__(self, product_name: str, stock_qty: int, requested_qty: int):
        self.product_name = product_name
        self.stock_qty = stock_qty
        self.requested_qty = requested_qty
        super().__init__(
            f"Estoque insuficiente para o produto '{product_name}'. "
            f"Disponível: {stock_qty}, Solicitado: {requested_qty}."
        )


class ModifyTerminalEntityException(Exception):
    """Tentativa de modificar uma entidade em estado terminal."""

    def __init__(self, entity_name: str, entity_id: str, status: str):
        self.entity_name = entity_name
        self.entity_id = str(entity_id)
        self.status = status
        super().__init__(
            f"Não é possível modificar o(a) {entity_name} com ID '{entity_id}' "
            f"pois está no estado terminal '{status}'."
        )

