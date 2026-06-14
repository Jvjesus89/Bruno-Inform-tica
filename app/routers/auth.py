from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.exceptions import AuthenticationException
from app.models.usuario import Usuario

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Endpoint de login OAuth2.
    Recebe username (e-mail) e password, retorna access_token JWT.
    Compatível com o botão 'Authorize' do Swagger UI.
    """
    query = select(Usuario).where(Usuario.email == form_data.username)
    user = db.scalars(query).first()

    if not user:
        raise AuthenticationException("E-mail ou senha incorretos.")

    if not verify_password(form_data.password, user.senha):
        raise AuthenticationException("E-mail ou senha incorretos.")

    access_token = create_access_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": user.nome,
        "tipo": user.tipo,
    }
