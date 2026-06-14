from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.routers.cliente import router as cliente_router
from app.routers.os import router as os_router
from app.routers.produtos import router as produto_router
from app.routers.usuario import router as usuario_router
from app.routers.equipamento import router as equipamento_router
from app.routers.auth import router as auth_router
from app.routers.ositens import router as ositens_router

from app.core.exceptions import (
    EntityNotFoundException,
    DuplicateEntityException,
    InvalidStateTransitionException,
    InvalidStatusException,
    AuthenticationException,
    ParentEntityHasActiveChildrenException,
    InsufficientStockException,
    ModifyTerminalEntityException,
)
from app.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("=" * 60)
    print("Iniciando a API do Bruno Informática...")
    print("=" * 60)
    seed_database()
    yield
    print("=" * 60)
    print("Finalizando a API do Bruno Informática...")
    print("=" * 60)


app = FastAPI(
    title="Bruno API",
    description="API para o projeto de Gerenciamento de Ordens de Serviço - Bruno",
    version="1.0.0",
    lifespan=lifespan,
)


# ──────────────────────────────────────────────────────────────
# Seção 4.4: Exception Handlers Customizados
# ──────────────────────────────────────────────────────────────

@app.exception_handler(EntityNotFoundException)
async def entity_not_found_handler(request: Request, exc: EntityNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": f"{exc.entity_name} com ID '{exc.entity_id}' não encontrado(a)."},
    )


@app.exception_handler(DuplicateEntityException)
async def duplicate_entity_handler(request: Request, exc: DuplicateEntityException):
    return JSONResponse(
        status_code=400,
        content={"detail": f"{exc.field} '{exc.value}' já cadastrado(a)."},
    )


@app.exception_handler(InvalidStateTransitionException)
async def invalid_transition_handler(request: Request, exc: InvalidStateTransitionException):
    return JSONResponse(
        status_code=422,
        content={
            "detail": (
                f"Transição de estado inválida. "
                f"Uma OS '{exc.current_status}' não pode ser alterada para '{exc.target_status}'."
            )
        },
    )


@app.exception_handler(InvalidStatusException)
async def invalid_status_handler(request: Request, exc: InvalidStatusException):
    return JSONResponse(
        status_code=400,
        content={"detail": f"Status inválido. Escolha entre: {', '.join(exc.allowed)}"},
    )


@app.exception_handler(AuthenticationException)
async def authentication_handler(request: Request, exc: AuthenticationException):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.detail},
    )


@app.exception_handler(ParentEntityHasActiveChildrenException)
async def parent_active_children_handler(request: Request, exc: ParentEntityHasActiveChildrenException):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(InsufficientStockException)
async def insufficient_stock_handler(request: Request, exc: InsufficientStockException):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(ModifyTerminalEntityException)
async def modify_terminal_entity_handler(request: Request, exc: ModifyTerminalEntityException):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


# ──────────────────────────────────────────────────────────────
# Registro de Routers
# ──────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(cliente_router)
app.include_router(produto_router)
app.include_router(os_router)
app.include_router(usuario_router)
app.include_router(equipamento_router)
app.include_router(ositens_router)


@app.get("/")
def read_root():
    return {
        "message": "Bem-vindo à Bruno Informática!",
        "docs_url": "/docs",
        "status": "Online",
    }