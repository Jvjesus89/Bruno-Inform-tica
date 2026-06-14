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
