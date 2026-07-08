import asyncio
import base64
import hashlib
import hmac
import io
import json as json_module
import os
import re
import secrets
import zipfile
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import ValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response, StreamingResponse
from sqlalchemy import func, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

try:
    from pywebpush import WebPushException
    from pywebpush import webpush as _enviar_webpush
    WEBPUSH_DISPONIVEL = True
except ImportError:
    WEBPUSH_DISPONIVEL = False
    print("AVISO: pywebpush nao instalado. Execute: pip install pywebpush")

try:
    from openai import OpenAI
    OPENAI_DISPONIVEL = True
except ImportError:
    OPENAI_DISPONIVEL = False
    print("AVISO: openai nao instalado. Execute: pip install openai")

import models
import schemas
from database import SQLALCHEMY_DATABASE_URL, SessionLocal, engine

API_DIR = Path(__file__).resolve().parent
ROOT_DIR = API_DIR.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv(API_DIR / ".env")
load_dotenv(API_DIR / ".env.local")


STATUS_FRETE = [
    "Aguardando horario",
    "A caminho P1",
    "coletado P1",
    "A caminho ponto adicional",
    "Pontos adicionais",
    "A caminho destino",
    "Chegada no destino",
    "retornando",
    "concluido",
]

CARGO_ADMIN = "admin"
CARGO_CONTROLE = "controle"
CARGO_MOTORISTA = "motorista"
CARGOS_VALIDOS = {CARGO_ADMIN, CARGO_CONTROLE, CARGO_MOTORISTA}
JWT_ALGORITMO = "HS256"
JWT_SECRET = os.getenv("ACELERA_JWT_SECRET", "acelera-dev-secret-altere-em-producao")
JWT_EXPIRA_HORAS = max(1, int(os.getenv("ACELERA_JWT_EXPIRE_HOURS", "12")))
SENHA_PBKDF2_ITERACOES = max(120_000, int(os.getenv("ACELERA_PASSWORD_ITERATIONS", "240000")))
CORS_ORIGINS = [
    origem.strip()
    for origem in os.getenv(
        "ACELERA_CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000",
    ).split(",")
    if origem.strip()
]

ROTAS_PUBLICAS = {"/", "/docs", "/redoc", "/openapi.json", "/auth/login", "/push/vapid-public-key"}
ROTAS_PUBLICAS_PREFIXO = ("/checklist/", "/checklists/")

TIMEZONE = os.getenv("ACELERA_TIMEZONE", "America/Sao_Paulo")

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")

if WEBPUSH_DISPONIVEL and (not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY):
    from cryptography.hazmat.primitives.asymmetric import ec as _ec
    from cryptography.hazmat.primitives.serialization import Encoding as _Enc, PublicFormat as _PF
    _pk = _ec.generate_private_key(_ec.SECP256R1())
    _raw = _pk.private_numbers().private_value.to_bytes(32, "big")
    VAPID_PRIVATE_KEY = base64.urlsafe_b64encode(_raw).rstrip(b"=").decode()
    _pub = _pk.public_key().public_bytes(_Enc.X962, _PF.UncompressedPoint)
    VAPID_PUBLIC_KEY = base64.urlsafe_b64encode(_pub).rstrip(b"=").decode()
    print("=" * 60)
    print("ATENCAO: Chaves VAPID geradas automaticamente (temporarias).")
    print("Defina no Railway para que as inscricoes persistam entre reinicializacoes:")
    print(f"  VAPID_PRIVATE_KEY={VAPID_PRIVATE_KEY}")
    print(f"  VAPID_PUBLIC_KEY={VAPID_PUBLIC_KEY}")
    print("=" * 60)


def normalizar_email(email: str) -> str:
    return (email or "").strip().lower()


def nome_padrao_usuario(email: str) -> str:
    prefixo = (email or "").split("@", 1)[0]
    nome = re.sub(r"[._-]+", " ", prefixo).strip()
    if not nome:
        return "Administrador"
    return " ".join(parte.capitalize() for parte in nome.split())


def gerar_hash_senha(senha: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, SENHA_PBKDF2_ITERACOES)
    salt_b64 = base64.urlsafe_b64encode(salt).decode("utf-8").rstrip("=")
    digest_b64 = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return f"pbkdf2_sha256${SENHA_PBKDF2_ITERACOES}${salt_b64}${digest_b64}"


def _decodificar_b64(valor: str) -> bytes:
    padding = "=" * (-len(valor) % 4)
    return base64.urlsafe_b64decode(f"{valor}{padding}")


def conferir_hash_senha(senha: str, senha_hash: str) -> bool:
    if not senha_hash:
        return False

    try:
        algoritmo, iteracoes_bruto, salt_b64, digest_b64 = senha_hash.split("$", 3)
        if algoritmo != "pbkdf2_sha256":
            return False
        iteracoes = int(iteracoes_bruto)
        salt = _decodificar_b64(salt_b64)
        hash_esperado = _decodificar_b64(digest_b64)
    except Exception:
        return False

    hash_atual = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, iteracoes)
    return hmac.compare_digest(hash_esperado, hash_atual)


def caminho_normalizado(path: str) -> str:
    caminho = (path or "").strip()
    if not caminho:
        return "/"
    if caminho != "/" and caminho.endswith("/"):
        caminho = caminho[:-1]
    return caminho or "/"


def rota_publica(path: str) -> bool:
    caminho = caminho_normalizado(path)
    caminhos_para_validar = {caminho}

    # Em producao, algumas configuracoes de proxy encaminham a API com prefixo /api.
    # Aceitamos as mesmas rotas publicas com e sem esse prefixo.
    if caminho.startswith("/api/"):
        caminhos_para_validar.add(caminho[4:])
    elif caminho == "/api":
        caminhos_para_validar.add("/")

    for caminho_item in caminhos_para_validar:
        if caminho_item in ROTAS_PUBLICAS:
            return True
        if any(caminho_item.startswith(prefixo) for prefixo in ROTAS_PUBLICAS_PREFIXO):
            return True
    return False


def rota_permitida(cargo: str, metodo: str, path: str) -> bool:
    if cargo == CARGO_ADMIN:
        return True

    caminho = caminho_normalizado(path)
    metodo_http = (metodo or "").upper()

    if caminho == "/auth/me" and metodo_http == "GET":
        return True

    if caminho == "/push/subscribe" and metodo_http in {"POST", "DELETE"}:
        return True

    # Assistente de chat: liberado para admin (retorna True acima) e controle.
    if caminho == "/chat" and metodo_http == "POST":
        return cargo == CARGO_CONTROLE

    if cargo == CARGO_CONTROLE:
        if metodo_http != "GET":
            return False
        if re.fullmatch(r"/fretes/\d+/sugestao-valor", caminho):
            return True
        return caminho in {
            "/fretes",
            "/fretes/concluidos/exportar",
            "/empresas",
            "/motoristas",
            "/veiculos",
        }

    if cargo == CARGO_MOTORISTA:
        if metodo_http == "GET" and caminho == "/fretes":
            return True
        if metodo_http == "PUT" and re.fullmatch(r"/fretes/\d+/alocar", caminho):
            return True
        return False

    return False


def criar_token_acesso(usuario: models.Usuario) -> str:
    expira_em = datetime.utcnow() + timedelta(hours=JWT_EXPIRA_HORAS)
    payload = {
        "sub": str(usuario.id),
        "cargo": usuario.cargo,
        "exp": expira_em,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITMO)


def ler_token_acesso(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITMO])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalido")


def serializar_usuario_sessao(usuario: models.Usuario) -> dict:
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": normalizar_email(usuario.email),
        "cargo": usuario.cargo,
        "motorista_id": usuario.motorista_id,
        "avatar_url": usuario.avatar_url,
    }


def serializar_usuario_sistema(usuario: models.Usuario) -> dict:
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": normalizar_email(usuario.email),
        "cargo": usuario.cargo,
        "ativo": bool(usuario.ativo),
        "motorista_id": usuario.motorista_id,
        "motorista_nome": usuario.motorista.nome if usuario.motorista else None,
        "avatar_url": usuario.avatar_url,
        "criado_em": usuario.criado_em,
        "atualizado_em": usuario.atualizado_em,
    }


def preparar_banco():
    models.Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tabelas = inspector.get_table_names()

    if "fretes" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("fretes")}
        ajustes = {
            "cte": "ALTER TABLE fretes ADD COLUMN cte VARCHAR",
            "oc": "ALTER TABLE fretes ADD COLUMN oc VARCHAR",
            "nota_fiscal": "ALTER TABLE fretes ADD COLUMN nota_fiscal VARCHAR",
            "origem": "ALTER TABLE fretes ADD COLUMN origem VARCHAR DEFAULT 'Edscha' NOT NULL",
            "empresas_coleta": "ALTER TABLE fretes ADD COLUMN empresas_coleta TEXT",
            "destino": "ALTER TABLE fretes ADD COLUMN destino VARCHAR DEFAULT '' NOT NULL",
            "retorno": "ALTER TABLE fretes ADD COLUMN retorno BOOLEAN DEFAULT 0",
            "tipo_frete": "ALTER TABLE fretes ADD COLUMN tipo_frete VARCHAR DEFAULT 'principal' NOT NULL",
            "frete_principal_id": "ALTER TABLE fretes ADD COLUMN frete_principal_id INTEGER",
            "valor_servico": "ALTER TABLE fretes ADD COLUMN valor_servico FLOAT",
            "valor_retorno": "ALTER TABLE fretes ADD COLUMN valor_retorno FLOAT",
            "valor_ponto_adicional": "ALTER TABLE fretes ADD COLUMN valor_ponto_adicional FLOAT",
            "observacoes": "ALTER TABLE fretes ADD COLUMN observacoes TEXT",
            "checklist_token": "ALTER TABLE fretes ADD COLUMN checklist_token VARCHAR",
            "checklist_tacografo": "ALTER TABLE fretes ADD COLUMN checklist_tacografo BOOLEAN DEFAULT 0",
            "checklist_pneus": "ALTER TABLE fretes ADD COLUMN checklist_pneus BOOLEAN DEFAULT 0",
            "checklist_oleo": "ALTER TABLE fretes ADD COLUMN checklist_oleo BOOLEAN DEFAULT 0",
            "checklist_avarias_externas": "ALTER TABLE fretes ADD COLUMN checklist_avarias_externas BOOLEAN DEFAULT 0",
            "checklist_avarias_internas": "ALTER TABLE fretes ADD COLUMN checklist_avarias_internas BOOLEAN DEFAULT 0",
            "checklist_luzes": "ALTER TABLE fretes ADD COLUMN checklist_luzes BOOLEAN DEFAULT 0",
            "checklist_confirmado": "ALTER TABLE fretes ADD COLUMN checklist_confirmado BOOLEAN DEFAULT 0",
            "checklist_confirmado_em": "ALTER TABLE fretes ADD COLUMN checklist_confirmado_em DATETIME",
            "checklist_observacoes": "ALTER TABLE fretes ADD COLUMN checklist_observacoes TEXT",
            "ultima_notificacao_push": "ALTER TABLE fretes ADD COLUMN ultima_notificacao_push " + ("DATETIME" if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else "TIMESTAMP"),
        }

        with engine.begin() as conexao:
            for coluna, comando in ajustes.items():
                if coluna not in colunas:
                    conexao.execute(text(comando))
            fretes_sem_token = conexao.execute(text("""
                SELECT id
                FROM fretes
                WHERE checklist_token IS NULL OR checklist_token = ''
            """)).fetchall()
            for (frete_id,) in fretes_sem_token:
                conexao.execute(
                    text("UPDATE fretes SET checklist_token = :token WHERE id = :id"),
                    {"token": secrets.token_urlsafe(16), "id": frete_id},
                )
            conexao.execute(text("""
                UPDATE fretes
                SET valor_retorno = COALESCE(
                    valor_retorno,
                    (
                        SELECT retorno.valor_servico
                        FROM fretes AS retorno
                        WHERE retorno.frete_principal_id = fretes.id
                            AND retorno.tipo_frete = 'retorno'
                            AND retorno.valor_servico IS NOT NULL
                        LIMIT 1
                    )
                )
                WHERE COALESCE(tipo_frete, 'principal') = 'principal'
            """))
            conexao.execute(text("""
                DELETE FROM fretes
                WHERE tipo_frete = 'retorno'
            """))

    if "motoristas" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("motoristas")}
        if "observacoes" not in colunas:
            with engine.begin() as conexao:
                conexao.execute(text("ALTER TABLE motoristas ADD COLUMN observacoes TEXT"))

    if "usuarios" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("usuarios")}
        ajustes = {
            "nome": "ALTER TABLE usuarios ADD COLUMN nome VARCHAR DEFAULT '' NOT NULL",
            "email": "ALTER TABLE usuarios ADD COLUMN email VARCHAR DEFAULT '' NOT NULL",
            "senha_hash": "ALTER TABLE usuarios ADD COLUMN senha_hash VARCHAR",
            "cargo": "ALTER TABLE usuarios ADD COLUMN cargo VARCHAR DEFAULT 'controle' NOT NULL",
            "google_sub": "ALTER TABLE usuarios ADD COLUMN google_sub VARCHAR",
            "avatar_url": "ALTER TABLE usuarios ADD COLUMN avatar_url VARCHAR",
            "ativo": "ALTER TABLE usuarios ADD COLUMN ativo BOOLEAN DEFAULT 1",
            "motorista_id": "ALTER TABLE usuarios ADD COLUMN motorista_id INTEGER",
            "criado_em": "ALTER TABLE usuarios ADD COLUMN criado_em DATETIME",
            "atualizado_em": "ALTER TABLE usuarios ADD COLUMN atualizado_em DATETIME",
        }
        agora = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        with engine.begin() as conexao:
            for coluna, comando in ajustes.items():
                if coluna not in colunas:
                    conexao.execute(text(comando))
            conexao.execute(
                text("""
                    UPDATE usuarios
                    SET email = LOWER(TRIM(COALESCE(email, ''))),
                        nome = TRIM(COALESCE(nome, '')),
                        cargo = LOWER(TRIM(COALESCE(cargo, 'controle')))
                """)
            )
            conexao.execute(text(
                "UPDATE usuarios SET cargo = 'controle' WHERE cargo NOT IN ('admin', 'controle', 'motorista')"
            ))
            conexao.execute(text("UPDATE usuarios SET nome = email WHERE nome = '' AND email <> ''"))
            conexao.execute(
                text("UPDATE usuarios SET senha_hash = NULL WHERE TRIM(COALESCE(senha_hash, '')) = ''")
            )
            conexao.execute(
                text(
                    "UPDATE usuarios SET criado_em = :agora WHERE criado_em IS NULL"
                ),
                {"agora": agora},
            )
            conexao.execute(
                text(
                    "UPDATE usuarios SET atualizado_em = :agora WHERE atualizado_em IS NULL"
                ),
                {"agora": agora},
            )

    if "veiculos" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("veiculos")}
        ajustes = {
            "observacoes": "ALTER TABLE veiculos ADD COLUMN observacoes TEXT",
            "observacao_estado": "ALTER TABLE veiculos ADD COLUMN observacao_estado TEXT",
            "motivo_indisponibilidade": "ALTER TABLE veiculos ADD COLUMN motivo_indisponibilidade TEXT",
            "ativo": "ALTER TABLE veiculos ADD COLUMN ativo BOOLEAN DEFAULT 1",
        }

        with engine.begin() as conexao:
            for coluna, comando in ajustes.items():
                if coluna not in colunas:
                    conexao.execute(text(comando))

        inspector = inspect(engine)
        indices_unicos_placa = [
            indice
            for indice in inspector.get_indexes("veiculos")
            if indice.get("unique") and indice.get("column_names") == ["placa"]
        ]
        constraints_unicas_placa = [
            constraint
            for constraint in inspector.get_unique_constraints("veiculos")
            if constraint.get("column_names") == ["placa"]
        ]
        if indices_unicos_placa or constraints_unicas_placa:
            with engine.begin() as conexao:
                conexao.execute(text("PRAGMA foreign_keys=OFF"))
                conexao.execute(text("ALTER TABLE veiculos RENAME TO veiculos_antigos"))
                conexao.execute(text("""
                    CREATE TABLE veiculos (
                        id INTEGER NOT NULL,
                        placa VARCHAR NOT NULL,
                        tipo VARCHAR NOT NULL,
                        observacoes TEXT,
                        observacao_estado TEXT,
                        motivo_indisponibilidade TEXT,
                        ativo BOOLEAN,
                        PRIMARY KEY (id),
                        CONSTRAINT uq_veiculos_placa_tipo UNIQUE (placa, tipo)
                    )
                """))
                conexao.execute(text("""
                    INSERT INTO veiculos (id, placa, tipo, observacoes, observacao_estado, motivo_indisponibilidade, ativo)
                    SELECT id, placa, tipo, observacoes, observacao_estado, motivo_indisponibilidade, COALESCE(ativo, 1)
                    FROM veiculos_antigos
                """))
                conexao.execute(text("DROP TABLE veiculos_antigos"))
                conexao.execute(text("PRAGMA foreign_keys=ON"))

    if "empresas" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("empresas")}
        ajustes = {
            "cliente": "ALTER TABLE empresas ADD COLUMN cliente BOOLEAN DEFAULT 0",
            "cep": "ALTER TABLE empresas ADD COLUMN cep VARCHAR",
            "logradouro": "ALTER TABLE empresas ADD COLUMN logradouro VARCHAR",
            "numero": "ALTER TABLE empresas ADD COLUMN numero VARCHAR",
            "complemento": "ALTER TABLE empresas ADD COLUMN complemento VARCHAR",
            "bairro": "ALTER TABLE empresas ADD COLUMN bairro VARCHAR",
            "cidade": "ALTER TABLE empresas ADD COLUMN cidade VARCHAR",
            "uf": "ALTER TABLE empresas ADD COLUMN uf VARCHAR",
            "observacoes": "ALTER TABLE empresas ADD COLUMN observacoes TEXT",
        }

        with engine.begin() as conexao:
            for coluna, comando in ajustes.items():
                if coluna not in colunas:
                    conexao.execute(text(comando))

    if "fornecedores" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("fornecedores")}
        ajustes = {
            "nome": "ALTER TABLE fornecedores ADD COLUMN nome VARCHAR DEFAULT '' NOT NULL",
            "telefone": "ALTER TABLE fornecedores ADD COLUMN telefone VARCHAR",
            "cep": "ALTER TABLE fornecedores ADD COLUMN cep VARCHAR",
            "logradouro": "ALTER TABLE fornecedores ADD COLUMN logradouro VARCHAR",
            "numero": "ALTER TABLE fornecedores ADD COLUMN numero VARCHAR",
            "complemento": "ALTER TABLE fornecedores ADD COLUMN complemento VARCHAR",
            "bairro": "ALTER TABLE fornecedores ADD COLUMN bairro VARCHAR",
            "endereco": "ALTER TABLE fornecedores ADD COLUMN endereco TEXT DEFAULT '' NOT NULL",
            "cidade": "ALTER TABLE fornecedores ADD COLUMN cidade VARCHAR DEFAULT '' NOT NULL",
            "uf": "ALTER TABLE fornecedores ADD COLUMN uf VARCHAR",
            "marca": "ALTER TABLE fornecedores ADD COLUMN marca VARCHAR DEFAULT '' NOT NULL",
            "observacoes": "ALTER TABLE fornecedores ADD COLUMN observacoes TEXT",
            "ativo": "ALTER TABLE fornecedores ADD COLUMN ativo BOOLEAN DEFAULT 1",
        }

        with engine.begin() as conexao:
            for coluna, comando in ajustes.items():
                if coluna not in colunas:
                    conexao.execute(text(comando))
            conexao.execute(text("""
                UPDATE fornecedores
                SET logradouro = COALESCE(NULLIF(logradouro, ''), NULLIF(endereco, '')),
                    endereco = COALESCE(NULLIF(endereco, ''), NULLIF(logradouro, ''), '')
            """))

    if "prestadores_servicos" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("prestadores_servicos")}
        ajustes = {
            "nome": "ALTER TABLE prestadores_servicos ADD COLUMN nome VARCHAR DEFAULT '' NOT NULL",
            "telefone": "ALTER TABLE prestadores_servicos ADD COLUMN telefone VARCHAR",
            "cep": "ALTER TABLE prestadores_servicos ADD COLUMN cep VARCHAR",
            "logradouro": "ALTER TABLE prestadores_servicos ADD COLUMN logradouro VARCHAR",
            "rua": "ALTER TABLE prestadores_servicos ADD COLUMN rua VARCHAR DEFAULT '' NOT NULL",
            "numero": "ALTER TABLE prestadores_servicos ADD COLUMN numero VARCHAR",
            "complemento": "ALTER TABLE prestadores_servicos ADD COLUMN complemento VARCHAR",
            "bairro": "ALTER TABLE prestadores_servicos ADD COLUMN bairro VARCHAR",
            "cidade": "ALTER TABLE prestadores_servicos ADD COLUMN cidade VARCHAR DEFAULT '' NOT NULL",
            "uf": "ALTER TABLE prestadores_servicos ADD COLUMN uf VARCHAR",
            "endereco": "ALTER TABLE prestadores_servicos ADD COLUMN endereco TEXT DEFAULT '' NOT NULL",
            "tipo": "ALTER TABLE prestadores_servicos ADD COLUMN tipo VARCHAR DEFAULT '' NOT NULL",
            "observacoes": "ALTER TABLE prestadores_servicos ADD COLUMN observacoes TEXT",
            "ativo": "ALTER TABLE prestadores_servicos ADD COLUMN ativo BOOLEAN DEFAULT 1",
        }

        with engine.begin() as conexao:
            for coluna, comando in ajustes.items():
                if coluna not in colunas:
                    conexao.execute(text(comando))
            conexao.execute(text("""
                UPDATE prestadores_servicos
                SET logradouro = COALESCE(NULLIF(logradouro, ''), NULLIF(rua, '')),
                    rua = COALESCE(NULLIF(rua, ''), NULLIF(logradouro, ''), ''),
                    endereco = COALESCE(
                        NULLIF(endereco, ''),
                        TRIM(
                            COALESCE(NULLIF(logradouro, ''), '') ||
                            CASE WHEN COALESCE(NULLIF(numero, ''), '') <> '' THEN ', ' || numero ELSE '' END ||
                            CASE WHEN COALESCE(NULLIF(cidade, ''), '') <> '' THEN ', ' || cidade ELSE '' END
                        ),
                        ''
                    )
            """))


preparar_banco()


def _verificar_fretes_pendentes():
    if not WEBPUSH_DISPONIVEL or not VAPID_PRIVATE_KEY:
        return
    tz = ZoneInfo(TIMEZONE)
    agora_utc = datetime.utcnow()
    agora_loc = datetime.now(tz).replace(tzinfo=None)

    db = SessionLocal()
    try:
        fretes = db.query(models.Frete).filter(
            models.Frete.status == "Aguardando horario"
        ).all()

        fretes_para_notificar = []
        for frete in fretes:
            coleta_dt = datetime.combine(frete.data_coleta, frete.horario_coleta)
            minutos_restantes = (coleta_dt - agora_loc).total_seconds() / 60
            if minutos_restantes > 20:
                continue
            if frete.ultima_notificacao_push is None:
                fretes_para_notificar.append((frete, minutos_restantes))
            else:
                desde_ultima = (agora_utc - frete.ultima_notificacao_push).total_seconds() / 60
                if desde_ultima >= 10:
                    fretes_para_notificar.append((frete, minutos_restantes))

        if not fretes_para_notificar:
            return

        subscriptions = db.query(models.PushSubscription).all()
        if not subscriptions:
            return

        ids_expiradas = set()
        for frete, minutos_restantes in fretes_para_notificar:
            horario_str = frete.horario_coleta.strftime("%H:%M")
            if minutos_restantes > 1:
                titulo = f"Frete em {int(minutos_restantes)} min — acao necessaria"
                corpo = f"{frete.cliente} — saida prevista {horario_str}, ainda Aguardando Horario"
            elif minutos_restantes >= 0:
                titulo = f"Horario do frete agora! ({horario_str})"
                corpo = f"{frete.cliente} — ainda em Aguardando Horario"
            else:
                titulo = f"Frete atrasado {int(-minutos_restantes)} min"
                corpo = f"{frete.cliente} — saida era {horario_str}, ainda Aguardando"

            payload = json_module.dumps({
                "title": titulo,
                "body": corpo,
                "url": "/fretes",
                "frete_id": frete.id,
            })

            for sub in subscriptions:
                try:
                    _enviar_webpush(
                        subscription_info={
                            "endpoint": sub.endpoint,
                            "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                        },
                        data=payload,
                        vapid_private_key=VAPID_PRIVATE_KEY,
                        vapid_claims={"sub": "mailto:noreply@acelera.com"},
                        ttl=900,
                    )
                except WebPushException as exc:
                    if exc.response is not None and exc.response.status_code in (404, 410):
                        ids_expiradas.add(sub.id)
                    else:
                        print(f"Push falhou (endpoint expirado?): {exc}")
                except Exception as exc:
                    print(f"Erro ao enviar push: {exc}")

            frete.ultima_notificacao_push = agora_utc

        if ids_expiradas:
            db.query(models.PushSubscription).filter(
                models.PushSubscription.id.in_(ids_expiradas)
            ).delete(synchronize_session=False)

        db.commit()
    except Exception as exc:
        print(f"Erro em _verificar_fretes_pendentes: {exc}")
        db.rollback()
    finally:
        db.close()


async def _loop_notificacoes():
    while True:
        await asyncio.sleep(60)
        try:
            await asyncio.get_event_loop().run_in_executor(None, _verificar_fretes_pendentes)
        except Exception as exc:
            print(f"Erro no loop de notificacoes: {exc}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    tarefa = asyncio.create_task(_loop_notificacoes())
    yield
    tarefa.cancel()
    try:
        await tarefa
    except asyncio.CancelledError:
        pass


app = FastAPI(title="API Acelera Transportes", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def usuario_logado(request: Request) -> dict:
    dados = getattr(request.state, "usuario", None)
    if not dados:
        raise HTTPException(status_code=401, detail="Nao autenticado")
    return dados


@app.middleware("http")
async def middleware_autenticacao(request: Request, call_next):
    path = request.url.path

    if request.method.upper() == "OPTIONS" or rota_publica(path):
        return await call_next(request)

    autorizacao = request.headers.get("Authorization", "")
    if not autorizacao.lower().startswith("bearer "):
        return JSONResponse(status_code=401, content={"detail": "Token de acesso obrigatorio"})

    token = autorizacao.split(" ", 1)[1].strip()
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Token de acesso invalido"})

    try:
        payload = ler_token_acesso(token)
        usuario_id = int(payload.get("sub"))
    except (HTTPException, TypeError, ValueError):
        return JSONResponse(status_code=401, content={"detail": "Token de acesso invalido"})

    with SessionLocal() as db:
        usuario = db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

    if not usuario or not usuario.ativo:
        return JSONResponse(status_code=403, content={"detail": "Usuario sem acesso"})

    cargo = (usuario.cargo or CARGO_CONTROLE).strip().lower()
    if cargo not in CARGOS_VALIDOS:
        return JSONResponse(status_code=403, content={"detail": "Cargo sem permissao"})
    if cargo == CARGO_MOTORISTA and not usuario.motorista_id:
        return JSONResponse(status_code=403, content={"detail": "Motorista sem vinculo de cadastro"})
    if not rota_permitida(cargo, request.method, path):
        return JSONResponse(status_code=403, content={"detail": "Permissao insuficiente para esta operacao"})

    request.state.usuario = {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": normalizar_email(usuario.email),
        "cargo": cargo,
        "motorista_id": usuario.motorista_id,
        "avatar_url": usuario.avatar_url,
    }
    return await call_next(request)


def montar_rota(frete: schemas.FreteCreate | schemas.FreteUpdate) -> str:
    origem = frete.origem or ""
    destino = frete.destino or ""
    empresas = frete.empresas_coleta or ""
    pontos = [ponto.strip() for ponto in [origem, empresas, destino] if ponto and ponto.strip()]
    return " -> ".join(pontos)


def resposta_checklist_frete(frete: models.Frete) -> dict:
    return {
        "token": frete.checklist_token,
        "frete_id": frete.id,
        "caminhao": frete.veiculo.tipo if frete.veiculo else frete.tipo_caminhao_necessario,
        "placa": frete.veiculo.placa if frete.veiculo else "Sem caminhao",
        "motorista": frete.motorista.nome if frete.motorista else "Sem motorista",
        "origem": frete.origem,
        "destino": frete.destino,
        "data_coleta": frete.data_coleta,
        "horario_coleta": frete.horario_coleta,
        "tacografo": bool(frete.checklist_tacografo),
        "pneus": bool(frete.checklist_pneus),
        "oleo": bool(frete.checklist_oleo),
        "avarias_externas": bool(frete.checklist_avarias_externas),
        "avarias_internas": bool(frete.checklist_avarias_internas),
        "luzes": bool(frete.checklist_luzes),
        "confirmado": bool(frete.checklist_confirmado),
        "confirmado_em": frete.checklist_confirmado_em,
        "observacoes": frete.checklist_observacoes,
    }


def pontos_adicionais_frete(frete: models.Frete) -> list[str]:
    return [ponto.strip() for ponto in (frete.empresas_coleta or "").split(",") if ponto and ponto.strip()]


def tem_ponto_adicional_frete(frete: models.Frete) -> bool:
    return len(pontos_adicionais_frete(frete)) > 0


def chave_template_frete(frete: models.Frete) -> dict:
    return {
        "empresa_id": (frete.cliente or "").strip(),
        "caminhao_contratado_id": (frete.tipo_caminhao_necessario or "").strip(),
        "origem_id": (frete.origem or "").strip(),
        "destino_id": (frete.destino or "").strip(),
        "tem_retorno": bool(frete.retorno),
        "tem_ponto_adicional": tem_ponto_adicional_frete(frete),
    }


def obter_template_valor_frete(db: Session, frete: models.Frete) -> Optional[models.FreteTemplateValor]:
    chave = chave_template_frete(frete)
    if not all([chave["empresa_id"], chave["caminhao_contratado_id"], chave["origem_id"], chave["destino_id"]]):
        return None
    return db.query(models.FreteTemplateValor).filter_by(**chave).first()


def salvar_template_valor_frete(db: Session, frete: models.Frete) -> None:
    if frete.valor_servico is None and frete.valor_retorno is None and frete.valor_ponto_adicional is None:
        return

    chave = chave_template_frete(frete)
    if not all([chave["empresa_id"], chave["caminhao_contratado_id"], chave["origem_id"], chave["destino_id"]]):
        return

    template = db.query(models.FreteTemplateValor).filter_by(**chave).first()
    if template is None:
        template = models.FreteTemplateValor(
            **chave,
            valor_padrao=frete.valor_servico,
            valor_retorno=frete.valor_retorno,
            valor_ponto_adicional=frete.valor_ponto_adicional,
            fonte="manual_confirmado",
            qtd_usos=1,
        )
        db.add(template)
        return

    template.valor_padrao = frete.valor_servico
    template.valor_retorno = frete.valor_retorno
    template.valor_ponto_adicional = frete.valor_ponto_adicional
    template.fonte = "manual_confirmado"
    template.qtd_usos = (template.qtd_usos or 0) + 1
    template.updated_at = datetime.utcnow()


def montar_endereco_empresa(empresa: schemas.EmpresaCreate) -> str:
    partes = [
        empresa.logradouro,
        empresa.numero,
        empresa.complemento,
        empresa.bairro,
        empresa.cidade,
        empresa.uf,
        empresa.cep,
    ]
    endereco = ", ".join(parte.strip() for parte in partes if parte and parte.strip())
    return endereco or empresa.endereco or ""


def montar_endereco_cep(logradouro: Optional[str], numero: Optional[str], complemento: Optional[str], bairro: Optional[str], cidade: Optional[str], uf: Optional[str], cep: Optional[str], fallback: Optional[str] = "") -> str:
    partes = [logradouro, numero, complemento, bairro, cidade, uf, cep]
    endereco = ", ".join(parte.strip() for parte in partes if parte and parte.strip())
    return endereco or (fallback or "")


def coluna_excel(indice: int) -> str:
    letras = ""
    while indice:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def celula_xml(linha: int, coluna: int, valor, estilo: int = 0) -> str:
    ref = f"{coluna_excel(coluna)}{linha}"
    style = f' s="{estilo}"' if estilo else ""
    if valor is None:
        valor = ""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return f'<c r="{ref}"{style}><v>{valor}</v></c>'
    return f'<c r="{ref}" t="inlineStr"{style}><is><t>{escape(str(valor))}</t></is></c>'


def criar_xlsx(linhas: list[list]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as arquivo:
        arquivo.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>""",
        )
        arquivo.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        arquivo.writestr(
            "xl/workbook.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets><sheet name="Fretes concluidos" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
        )
        arquivo.writestr(
            "xl/_rels/workbook.xml.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>""",
        )
        arquivo.writestr(
            "xl/styles.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="1"><fill><patternFill patternType="none"/></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>""",
        )

        sheet_rows = []
        for indice_linha, linha in enumerate(linhas, start=1):
            cells = "".join(celula_xml(indice_linha, indice_coluna, valor, 1 if indice_linha == 1 else 0) for indice_coluna, valor in enumerate(linha, start=1))
            sheet_rows.append(f'<row r="{indice_linha}">{cells}</row>')

        arquivo.writestr(
            "xl/worksheets/sheet1.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<cols><col min="1" max="10" width="16" customWidth="1"/></cols>
<sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>""",
        )
    return buffer.getvalue()


def nome_aba_excel(nome: str, usados: set[str]) -> str:
    proibidos = "[]:*?/\\"
    limpo = "".join("_" if caractere in proibidos else caractere for caractere in (nome or "Motorista")).strip()
    base = (limpo or "Motorista")[:31]
    nome_final = base
    contador = 2

    while nome_final in usados:
        sufixo = f" {contador}"
        nome_final = f"{base[:31 - len(sufixo)]}{sufixo}"
        contador += 1

    usados.add(nome_final)
    return nome_final


def criar_xlsx_abas(abas: list[tuple[str, list[list]]]) -> bytes:
    buffer = io.BytesIO()
    usados: set[str] = set()
    abas_normalizadas = [(nome_aba_excel(nome, usados), linhas) for nome, linhas in abas]

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as arquivo:
        worksheets = "\n".join(
            f'<Override PartName="/xl/worksheets/sheet{indice}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for indice, _ in enumerate(abas_normalizadas, start=1)
        )
        arquivo.writestr(
            "[Content_Types].xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
{worksheets}
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>""",
        )
        arquivo.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        )
        sheets = "".join(
            f'<sheet name="{escape(nome)}" sheetId="{indice}" r:id="rId{indice}"/>'
            for indice, (nome, _) in enumerate(abas_normalizadas, start=1)
        )
        arquivo.writestr(
            "xl/workbook.xml",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<sheets>{sheets}</sheets>
</workbook>""",
        )
        rels = "\n".join(
            f'<Relationship Id="rId{indice}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{indice}.xml"/>'
            for indice, _ in enumerate(abas_normalizadas, start=1)
        )
        arquivo.writestr(
            "xl/_rels/workbook.xml.rels",
            f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{rels}
<Relationship Id="rId{len(abas_normalizadas) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>""",
        )
        arquivo.writestr(
            "xl/styles.xml",
            """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts>
<fills count="1"><fill><patternFill patternType="none"/></fill></fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/></cellXfs>
</styleSheet>""",
        )

        for indice_aba, (_, linhas) in enumerate(abas_normalizadas, start=1):
            sheet_rows = []
            for indice_linha, linha in enumerate(linhas, start=1):
                cells = "".join(
                    celula_xml(indice_linha, indice_coluna, valor, 1 if indice_linha == 1 else 0)
                    for indice_coluna, valor in enumerate(linha, start=1)
                )
                sheet_rows.append(f'<row r="{indice_linha}">{cells}</row>')

            arquivo.writestr(
                f"xl/worksheets/sheet{indice_aba}.xml",
                f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<cols>
<col min="1" max="1" width="10" customWidth="1"/>
<col min="2" max="2" width="14" customWidth="1"/>
<col min="3" max="4" width="20" customWidth="1"/>
<col min="5" max="5" width="24" customWidth="1"/>
<col min="6" max="6" width="42" customWidth="1"/>
</cols>
<sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>""",
            )

    return buffer.getvalue()


def obter_ou_404(db: Session, modelo, item_id: int, detalhe: str):
    item = db.query(modelo).filter(modelo.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=detalhe)
    return item


@app.get("/", tags=["Home"])
def home():
    return {"status": "API Acelera Transportes online", "status_frete": STATUS_FRETE}


@app.post("/auth/login", response_model=schemas.AuthLoginResponse, tags=["Auth"])
def login_interno(payload: schemas.AuthLoginRequest, db: Session = Depends(get_db)):
    email = normalizar_email(payload.email)
    senha = payload.senha.strip()
    nome_informado = (payload.nome or "").strip()

    usuario = db.query(models.Usuario).filter(func.lower(models.Usuario.email) == email).first()
    total_usuarios = db.query(func.count(models.Usuario.id)).scalar() or 0
    total_usuarios_com_senha = (
        db.query(func.count(models.Usuario.id))
        .filter(models.Usuario.senha_hash.isnot(None))
        .filter(models.Usuario.senha_hash != "")
        .scalar()
        or 0
    )

    if not usuario:
        if total_usuarios == 0:
            usuario = models.Usuario(
                nome=nome_informado or nome_padrao_usuario(email),
                email=email,
                senha_hash=gerar_hash_senha(senha),
                cargo=CARGO_ADMIN,
                ativo=True,
            )
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
        else:
            raise HTTPException(
                status_code=403,
                detail="Acesso nao autorizado. Solicite ao administrador o cadastro do seu email.",
            )
    else:
        if not usuario.senha_hash:
            cargo_sem_senha = (usuario.cargo or CARGO_CONTROLE).strip().lower()
            if total_usuarios_com_senha == 0 and cargo_sem_senha == CARGO_ADMIN:
                usuario.senha_hash = gerar_hash_senha(senha)
                if not (usuario.nome or "").strip():
                    usuario.nome = nome_informado or nome_padrao_usuario(email)
                db.commit()
                db.refresh(usuario)
            else:
                raise HTTPException(
                    status_code=403,
                    detail="Senha ainda nao configurada para este acesso. Solicite ao administrador.",
                )
        elif not conferir_hash_senha(senha, usuario.senha_hash):
            raise HTTPException(status_code=401, detail="Email ou senha invalidos")

    if not usuario.ativo:
        raise HTTPException(status_code=403, detail="Usuario inativo")

    cargo = (usuario.cargo or CARGO_CONTROLE).strip().lower()
    if cargo not in CARGOS_VALIDOS:
        raise HTTPException(status_code=403, detail="Cargo de acesso invalido")
    if cargo == CARGO_MOTORISTA and not usuario.motorista_id:
        raise HTTPException(
            status_code=403,
            detail="Usuario motorista sem vinculo com cadastro de motorista",
        )

    usuario.email = email
    usuario.cargo = cargo
    if nome_informado and total_usuarios == 0:
        usuario.nome = nome_informado
    db.commit()
    db.refresh(usuario)

    token = criar_token_acesso(usuario)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": serializar_usuario_sessao(usuario),
    }


@app.get("/auth/me", response_model=schemas.UsuarioSessao, tags=["Auth"])
def auth_me(request: Request, db: Session = Depends(get_db)):
    dados = usuario_logado(request)
    usuario = db.query(models.Usuario).filter(models.Usuario.id == dados["id"]).first()
    if not usuario or not usuario.ativo:
        raise HTTPException(status_code=401, detail="Sessao invalida")
    return serializar_usuario_sessao(usuario)


@app.get("/usuarios/", response_model=list[schemas.UsuarioSistemaResponse], tags=["Usuarios"])
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).order_by(models.Usuario.nome).all()
    return [serializar_usuario_sistema(usuario) for usuario in usuarios]


@app.post("/usuarios/", response_model=schemas.UsuarioSistemaResponse, tags=["Usuarios"])
def criar_usuario_sistema(dados: schemas.UsuarioSistemaCreate, db: Session = Depends(get_db)):
    email = normalizar_email(dados.email)
    if db.query(models.Usuario).filter(func.lower(models.Usuario.email) == email).first():
        raise HTTPException(status_code=400, detail="Email ja cadastrado")

    motorista_id = dados.motorista_id if dados.cargo == CARGO_MOTORISTA else None
    if motorista_id:
        obter_ou_404(db, models.Motorista, motorista_id, "Motorista nao encontrado")
        existente = db.query(models.Usuario).filter(models.Usuario.motorista_id == motorista_id).first()
        if existente:
            raise HTTPException(status_code=400, detail="Ja existe usuario vinculado a este motorista")

    usuario = models.Usuario(
        nome=dados.nome.strip(),
        email=email,
        senha_hash=gerar_hash_senha(dados.senha),
        cargo=dados.cargo,
        ativo=dados.ativo,
        motorista_id=motorista_id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return serializar_usuario_sistema(usuario)


@app.put("/usuarios/{usuario_id}", response_model=schemas.UsuarioSistemaResponse, tags=["Usuarios"])
def atualizar_usuario_sistema(usuario_id: int, dados: schemas.UsuarioSistemaUpdate, db: Session = Depends(get_db)):
    usuario = obter_ou_404(db, models.Usuario, usuario_id, "Usuario nao encontrado")
    dados_atualizacao = dados.model_dump(exclude_unset=True)

    if "nome" in dados_atualizacao:
        usuario.nome = dados_atualizacao["nome"].strip()
    if "email" in dados_atualizacao:
        email = normalizar_email(dados_atualizacao["email"])
        existente = db.query(models.Usuario).filter(func.lower(models.Usuario.email) == email, models.Usuario.id != usuario_id).first()
        if existente:
            raise HTTPException(status_code=400, detail="Email ja cadastrado")
        usuario.email = email
    if "ativo" in dados_atualizacao:
        usuario.ativo = bool(dados_atualizacao["ativo"])
    if dados_atualizacao.get("nova_senha"):
        usuario.senha_hash = gerar_hash_senha(dados_atualizacao["nova_senha"])

    novo_cargo = dados_atualizacao.get("cargo", usuario.cargo)
    motorista_id = dados_atualizacao.get("motorista_id", usuario.motorista_id)

    if novo_cargo == CARGO_MOTORISTA and not motorista_id:
        raise HTTPException(status_code=400, detail="Usuario motorista precisa de motorista vinculado")

    if novo_cargo != CARGO_MOTORISTA:
        motorista_id = None

    if motorista_id:
        obter_ou_404(db, models.Motorista, motorista_id, "Motorista nao encontrado")
        existente = db.query(models.Usuario).filter(
            models.Usuario.motorista_id == motorista_id,
            models.Usuario.id != usuario_id,
        ).first()
        if existente:
            raise HTTPException(status_code=400, detail="Ja existe usuario vinculado a este motorista")

    usuario.cargo = novo_cargo
    usuario.motorista_id = motorista_id

    db.commit()
    db.refresh(usuario)
    return serializar_usuario_sistema(usuario)


@app.post("/motoristas/", response_model=schemas.MotoristaResponse, tags=["Motoristas"])
def criar_motorista(motorista: schemas.MotoristaCreate, db: Session = Depends(get_db)):
    dados = motorista.model_dump()
    dados["cnh"] = dados.get("cnh") or ""
    dados["observacoes"] = dados.get("observacoes") or ""
    db_motorista = models.Motorista(**dados)
    db.add(db_motorista)
    db.commit()
    db.refresh(db_motorista)
    return db_motorista


@app.get("/motoristas/", response_model=list[schemas.MotoristaResponse], tags=["Motoristas"])
def listar_motoristas(db: Session = Depends(get_db)):
    return db.query(models.Motorista).order_by(models.Motorista.nome).all()


@app.put("/motoristas/{motorista_id}", response_model=schemas.MotoristaResponse, tags=["Motoristas"])
def atualizar_motorista(motorista_id: int, dados: schemas.MotoristaUpdate, db: Session = Depends(get_db)):
    db_motorista = obter_ou_404(db, models.Motorista, motorista_id, "Motorista nao encontrado")
    dados_atualizacao = dados.model_dump(exclude_unset=True)
    if "cnh" in dados_atualizacao:
        dados_atualizacao["cnh"] = dados_atualizacao["cnh"] or ""
    if "observacoes" in dados_atualizacao:
        dados_atualizacao["observacoes"] = dados_atualizacao["observacoes"] or ""
    for campo, valor in dados_atualizacao.items():
        setattr(db_motorista, campo, valor)
    db.commit()
    db.refresh(db_motorista)
    return db_motorista


@app.delete("/motoristas/{motorista_id}", tags=["Motoristas"])
def excluir_motorista(motorista_id: int, db: Session = Depends(get_db)):
    db_motorista = obter_ou_404(db, models.Motorista, motorista_id, "Motorista nao encontrado")

    usuario_vinculado = db.query(models.Usuario).filter(
        models.Usuario.motorista_id == motorista_id
    ).first()
    if usuario_vinculado:
        raise HTTPException(
            status_code=400,
            detail=f"Este motorista está vinculado ao usuário '{usuario_vinculado.nome}'. Remova o vínculo em Acessos antes de excluir.",
        )

    # Fretes do historico sao preservados: apenas perdem o vinculo com o motorista.
    fretes_desvinculados = db.query(models.Frete).filter(
        models.Frete.motorista_id == motorista_id
    ).update({"motorista_id": None})

    try:
        db.delete(db_motorista)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Nao e possivel excluir: motorista possui registros vinculados.")

    if fretes_desvinculados:
        return {
            "mensagem": (
                f"Motorista excluido. {fretes_desvinculados} frete(s) do histórico foram "
                "mantidos, agora sem motorista vinculado."
            )
        }
    return {"mensagem": "Motorista excluido"}


@app.post("/veiculos/", response_model=schemas.VeiculoResponse, tags=["Veiculos"])
def criar_veiculo(veiculo: schemas.VeiculoCreate, db: Session = Depends(get_db)):
    db_veiculo = models.Veiculo(**veiculo.model_dump())
    db.add(db_veiculo)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ja existe caminhao com esta identificacao e tipo")
    db.refresh(db_veiculo)
    return db_veiculo


@app.get("/veiculos/", response_model=list[schemas.VeiculoResponse], tags=["Veiculos"])
def listar_veiculos(db: Session = Depends(get_db)):
    return db.query(models.Veiculo).order_by(models.Veiculo.placa).all()


@app.put("/veiculos/{veiculo_id}", response_model=schemas.VeiculoResponse, tags=["Veiculos"])
def atualizar_veiculo(veiculo_id: int, dados: schemas.VeiculoUpdate, db: Session = Depends(get_db)):
    db_veiculo = obter_ou_404(db, models.Veiculo, veiculo_id, "Veiculo nao encontrado")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(db_veiculo, campo, valor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Ja existe caminhao com esta identificacao e tipo")
    db.refresh(db_veiculo)
    return db_veiculo


@app.delete("/veiculos/{veiculo_id}", tags=["Veiculos"])
def excluir_veiculo(veiculo_id: int, db: Session = Depends(get_db)):
    db_veiculo = obter_ou_404(db, models.Veiculo, veiculo_id, "Veiculo nao encontrado")
    db.delete(db_veiculo)
    db.commit()
    return {"mensagem": "Veiculo excluido"}


@app.post("/ocorrencias-veiculos/", response_model=schemas.OcorrenciaVeiculoResponse, tags=["Veiculos"])
def criar_ocorrencia_veiculo(ocorrencia: schemas.OcorrenciaVeiculoCreate, db: Session = Depends(get_db)):
    obter_ou_404(db, models.Veiculo, ocorrencia.veiculo_id, "Veiculo nao encontrado")
    db_ocorrencia = models.OcorrenciaVeiculo(**ocorrencia.model_dump())
    db.add(db_ocorrencia)
    db.commit()
    db.refresh(db_ocorrencia)
    return db_ocorrencia


@app.get("/ocorrencias-veiculos/", response_model=list[schemas.OcorrenciaVeiculoResponse], tags=["Veiculos"])
def listar_ocorrencias_veiculos(db: Session = Depends(get_db)):
    return db.query(models.OcorrenciaVeiculo).order_by(models.OcorrenciaVeiculo.criado_em.desc()).all()


@app.put("/ocorrencias-veiculos/{ocorrencia_id}", response_model=schemas.OcorrenciaVeiculoResponse, tags=["Veiculos"])
def atualizar_ocorrencia_veiculo(ocorrencia_id: int, dados: schemas.OcorrenciaVeiculoUpdate, db: Session = Depends(get_db)):
    db_ocorrencia = obter_ou_404(db, models.OcorrenciaVeiculo, ocorrencia_id, "Ocorrencia nao encontrada")
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(db_ocorrencia, campo, valor)
    if dados.status == "Resolvido" and not db_ocorrencia.resolvido_em:
        db_ocorrencia.resolvido_em = datetime.utcnow()
    db.commit()
    db.refresh(db_ocorrencia)
    return db_ocorrencia


@app.delete("/ocorrencias-veiculos/{ocorrencia_id}", tags=["Veiculos"])
def excluir_ocorrencia_veiculo(ocorrencia_id: int, db: Session = Depends(get_db)):
    db_ocorrencia = obter_ou_404(db, models.OcorrenciaVeiculo, ocorrencia_id, "Ocorrencia nao encontrada")
    db.delete(db_ocorrencia)
    db.commit()
    return {"mensagem": "Ocorrencia excluida"}


@app.post("/empresas/", response_model=schemas.EmpresaResponse, tags=["Empresas"])
def criar_empresa(empresa: schemas.EmpresaCreate, db: Session = Depends(get_db)):
    dados = empresa.model_dump()
    dados["endereco"] = montar_endereco_empresa(empresa)
    db_empresa = models.Empresa(**dados)
    db.add(db_empresa)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa


@app.get("/empresas/", response_model=list[schemas.EmpresaResponse], tags=["Empresas"])
def listar_empresas(db: Session = Depends(get_db)):
    return db.query(models.Empresa).order_by(models.Empresa.nome).all()


@app.put("/empresas/{empresa_id}", response_model=schemas.EmpresaResponse, tags=["Empresas"])
def atualizar_empresa(empresa_id: int, empresa: schemas.EmpresaUpdate, db: Session = Depends(get_db)):
    db_empresa = obter_ou_404(db, models.Empresa, empresa_id, "Empresa nao encontrada")
    dados = empresa.model_dump(exclude_unset=True)
    if any(campo in dados for campo in ["logradouro", "numero", "bairro", "cidade", "uf", "endereco"]):
        dados["endereco"] = montar_endereco_empresa(empresa)
    for campo, valor in dados.items():
        setattr(db_empresa, campo, valor)
    db.commit()
    db.refresh(db_empresa)
    return db_empresa


@app.delete("/empresas/{empresa_id}", tags=["Empresas"])
def excluir_empresa(empresa_id: int, db: Session = Depends(get_db)):
    db_empresa = obter_ou_404(db, models.Empresa, empresa_id, "Empresa nao encontrada")
    db.delete(db_empresa)
    db.commit()
    return {"mensagem": "Empresa excluida"}


@app.post("/fornecedores/", response_model=schemas.FornecedorResponse, tags=["Fornecedores"])
def criar_fornecedor(fornecedor: schemas.FornecedorCreate, db: Session = Depends(get_db)):
    dados = fornecedor.model_dump()
    dados["nome"] = (dados.get("nome") or "").strip()
    dados["telefone"] = (dados.get("telefone") or "").strip()
    dados["cep"] = (dados.get("cep") or "").strip()
    dados["logradouro"] = (dados.get("logradouro") or "").strip()
    dados["numero"] = (dados.get("numero") or "").strip()
    dados["complemento"] = (dados.get("complemento") or "").strip()
    dados["bairro"] = (dados.get("bairro") or "").strip()
    dados["cidade"] = (dados.get("cidade") or "").strip()
    dados["uf"] = (dados.get("uf") or "").strip()
    dados["marca"] = (dados.get("marca") or "").strip()
    dados["observacoes"] = (dados.get("observacoes") or "").strip()
    dados["endereco"] = montar_endereco_cep(
        dados.get("logradouro"),
        dados.get("numero"),
        dados.get("complemento"),
        dados.get("bairro"),
        dados.get("cidade"),
        dados.get("uf"),
        dados.get("cep"),
        dados.get("endereco"),
    )

    if not dados["nome"] or not dados["cep"] or not dados["cidade"] or not dados["marca"]:
        raise HTTPException(status_code=400, detail="Nome, CEP, cidade e marca sao obrigatorios")

    db_fornecedor = models.Fornecedor(**dados)
    db.add(db_fornecedor)
    db.commit()
    db.refresh(db_fornecedor)
    return db_fornecedor


@app.get("/fornecedores/", response_model=list[schemas.FornecedorResponse], tags=["Fornecedores"])
def listar_fornecedores(db: Session = Depends(get_db)):
    return db.query(models.Fornecedor).order_by(models.Fornecedor.nome).all()


@app.put("/fornecedores/{fornecedor_id}", response_model=schemas.FornecedorResponse, tags=["Fornecedores"])
def atualizar_fornecedor(fornecedor_id: int, fornecedor: schemas.FornecedorUpdate, db: Session = Depends(get_db)):
    db_fornecedor = obter_ou_404(db, models.Fornecedor, fornecedor_id, "Fornecedor nao encontrado")
    dados = fornecedor.model_dump(exclude_unset=True)

    for campo in ["nome", "telefone", "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "marca", "observacoes"]:
        if campo in dados:
            dados[campo] = (dados[campo] or "").strip()

    if "nome" in dados and not dados["nome"]:
        raise HTTPException(status_code=400, detail="Nome do fornecedor e obrigatorio")
    if "cep" in dados and not dados["cep"]:
        raise HTTPException(status_code=400, detail="CEP do fornecedor e obrigatorio")
    if "cidade" in dados and not dados["cidade"]:
        raise HTTPException(status_code=400, detail="Cidade do fornecedor e obrigatoria")
    if "marca" in dados and not dados["marca"]:
        raise HTTPException(status_code=400, detail="Marca do fornecedor e obrigatoria")

    for campo, valor in dados.items():
        setattr(db_fornecedor, campo, valor)

    if any(campo in dados for campo in ["cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "endereco"]):
        db_fornecedor.endereco = montar_endereco_cep(
            db_fornecedor.logradouro,
            db_fornecedor.numero,
            db_fornecedor.complemento,
            db_fornecedor.bairro,
            db_fornecedor.cidade,
            db_fornecedor.uf,
            db_fornecedor.cep,
            db_fornecedor.endereco,
        )

    db.commit()
    db.refresh(db_fornecedor)
    return db_fornecedor


@app.delete("/fornecedores/{fornecedor_id}", tags=["Fornecedores"])
def excluir_fornecedor(fornecedor_id: int, db: Session = Depends(get_db)):
    db_fornecedor = obter_ou_404(db, models.Fornecedor, fornecedor_id, "Fornecedor nao encontrado")
    db.delete(db_fornecedor)
    db.commit()
    return {"mensagem": "Fornecedor excluido"}


@app.post("/prestadores-servicos/", response_model=schemas.PrestadorServicoResponse, tags=["Prestadores de servicos"])
def criar_prestador_servico(prestador: schemas.PrestadorServicoCreate, db: Session = Depends(get_db)):
    dados = prestador.model_dump()
    dados["nome"] = (dados.get("nome") or "").strip()
    dados["telefone"] = (dados.get("telefone") or "").strip()
    dados["cep"] = (dados.get("cep") or "").strip()
    dados["logradouro"] = (dados.get("logradouro") or "").strip()
    dados["numero"] = (dados.get("numero") or "").strip()
    dados["complemento"] = (dados.get("complemento") or "").strip()
    dados["bairro"] = (dados.get("bairro") or "").strip()
    dados["cidade"] = (dados.get("cidade") or "").strip()
    dados["uf"] = (dados.get("uf") or "").strip()
    dados["tipo"] = (dados.get("tipo") or "").strip()
    dados["observacoes"] = (dados.get("observacoes") or "").strip()
    dados["rua"] = dados["logradouro"]
    dados["endereco"] = montar_endereco_cep(
        dados.get("logradouro"),
        dados.get("numero"),
        dados.get("complemento"),
        dados.get("bairro"),
        dados.get("cidade"),
        dados.get("uf"),
        dados.get("cep"),
        dados.get("endereco"),
    )

    if not dados["nome"] or not dados["cep"] or not dados["cidade"] or not dados["tipo"]:
        raise HTTPException(status_code=400, detail="Nome, CEP, cidade e tipo sao obrigatorios")

    db_prestador = models.PrestadorServico(**dados)
    db.add(db_prestador)
    db.commit()
    db.refresh(db_prestador)
    return db_prestador


@app.get("/prestadores-servicos/", response_model=list[schemas.PrestadorServicoResponse], tags=["Prestadores de servicos"])
def listar_prestadores_servicos(db: Session = Depends(get_db)):
    return db.query(models.PrestadorServico).order_by(models.PrestadorServico.nome).all()


@app.put("/prestadores-servicos/{prestador_id}", response_model=schemas.PrestadorServicoResponse, tags=["Prestadores de servicos"])
def atualizar_prestador_servico(prestador_id: int, prestador: schemas.PrestadorServicoUpdate, db: Session = Depends(get_db)):
    db_prestador = obter_ou_404(db, models.PrestadorServico, prestador_id, "Prestador de servico nao encontrado")
    dados = prestador.model_dump(exclude_unset=True)

    for campo in ["nome", "telefone", "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "tipo", "observacoes"]:
        if campo in dados:
            dados[campo] = (dados[campo] or "").strip()

    if "nome" in dados and not dados["nome"]:
        raise HTTPException(status_code=400, detail="Nome do prestador e obrigatorio")
    if "cep" in dados and not dados["cep"]:
        raise HTTPException(status_code=400, detail="CEP do prestador e obrigatorio")
    if "cidade" in dados and not dados["cidade"]:
        raise HTTPException(status_code=400, detail="Cidade do prestador e obrigatoria")
    if "tipo" in dados and not dados["tipo"]:
        raise HTTPException(status_code=400, detail="Tipo do prestador e obrigatorio")

    for campo, valor in dados.items():
        setattr(db_prestador, campo, valor)

    if "logradouro" in dados:
        db_prestador.rua = db_prestador.logradouro or ""

    if any(campo in dados for campo in ["cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "endereco"]):
        db_prestador.endereco = montar_endereco_cep(
            db_prestador.logradouro,
            db_prestador.numero,
            db_prestador.complemento,
            db_prestador.bairro,
            db_prestador.cidade,
            db_prestador.uf,
            db_prestador.cep,
            db_prestador.endereco,
        )

    db.commit()
    db.refresh(db_prestador)
    return db_prestador


@app.delete("/prestadores-servicos/{prestador_id}", tags=["Prestadores de servicos"])
def excluir_prestador_servico(prestador_id: int, db: Session = Depends(get_db)):
    db_prestador = obter_ou_404(db, models.PrestadorServico, prestador_id, "Prestador de servico nao encontrado")
    db.delete(db_prestador)
    db.commit()
    return {"mensagem": "Prestador de servico excluido"}


@app.post("/fretes/", response_model=schemas.FreteResponse, tags=["Fretes"])
def criar_frete(frete: schemas.FreteCreate, db: Session = Depends(get_db)):
    dados = frete.model_dump()
    dados["tipo_frete"] = dados.get("tipo_frete") or "principal"
    dados["rota"] = montar_rota(frete)
    dados["pontoAdicional"] = frete.retorno and dados["tipo_frete"] == "principal"
    dados["checklist_token"] = secrets.token_urlsafe(16)
    db_frete = models.Frete(**dados)
    db.add(db_frete)
    db.commit()
    db.refresh(db_frete)
    return db_frete


@app.get("/fretes/", response_model=list[schemas.FreteResponse], tags=["Fretes"])
def listar_fretes(request: Request, db: Session = Depends(get_db)):
    dados_usuario = usuario_logado(request)
    consulta = db.query(models.Frete)

    if dados_usuario["cargo"] == CARGO_MOTORISTA:
        consulta = consulta.filter(models.Frete.motorista_id == dados_usuario["motorista_id"])

    return consulta.order_by(models.Frete.data_coleta, models.Frete.horario_coleta).all()


@app.get("/checklists/{token}", response_model=schemas.ChecklistFreteResponse, tags=["Checklist"])
def obter_checklist_frete(token: str, db: Session = Depends(get_db)):
    frete = db.query(models.Frete).filter(models.Frete.checklist_token == token).first()
    if not frete:
        raise HTTPException(status_code=404, detail="Checklist nao encontrado")
    return resposta_checklist_frete(frete)


@app.put("/checklists/{token}", response_model=schemas.ChecklistFreteResponse, tags=["Checklist"])
def confirmar_checklist_frete(token: str, checklist: schemas.ChecklistFreteUpdate, db: Session = Depends(get_db)):
    frete = db.query(models.Frete).filter(models.Frete.checklist_token == token).first()
    if not frete:
        raise HTTPException(status_code=404, detail="Checklist nao encontrado")

    frete.checklist_tacografo = checklist.tacografo
    frete.checklist_pneus = checklist.pneus
    frete.checklist_oleo = checklist.oleo
    frete.checklist_avarias_externas = checklist.avarias_externas
    frete.checklist_avarias_internas = checklist.avarias_internas
    frete.checklist_luzes = checklist.luzes
    frete.checklist_confirmado = True
    frete.checklist_confirmado_em = datetime.now()
    frete.checklist_observacoes = checklist.observacoes
    db.commit()
    db.refresh(frete)
    return resposta_checklist_frete(frete)


@app.get("/fretes/concluidos/exportar", tags=["Fretes"])
def exportar_fretes_concluidos(
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    cliente: Optional[str] = None,
    db: Session = Depends(get_db),
):
    consulta = db.query(models.Frete).filter(
        models.Frete.status.in_(["concluido", "Concluida"]),
        models.Frete.tipo_frete != "retorno",
    )
    if inicio:
        consulta = consulta.filter(models.Frete.data_coleta >= inicio)
    if fim:
        consulta = consulta.filter(models.Frete.data_coleta <= fim)
    if cliente:
        consulta = consulta.filter(models.Frete.cliente == cliente)

    fretes = consulta.order_by(models.Frete.data_coleta, models.Frete.horario_coleta).all()
    empresas = {empresa.nome: empresa for empresa in db.query(models.Empresa).all()}

    linhas = [[
        "Nota",
        "OC",
        "Data Frete",
        "Veículo",
        "Remetente",
        "Cidade Rem.",
        "Destinatário",
        "Cidade Dest.",
        "Total Prest.",
        "Vencimento",
    ]]

    for frete in fretes:
        remetente = empresas.get(frete.origem)
        destinatario = empresas.get(frete.destino)
        linhas.append([
            frete.nota_fiscal or "",
            frete.oc or "",
            frete.data_coleta.strftime("%d.%m"),
            frete.tipo_caminhao_necessario,
            frete.origem,
            remetente.cidade if remetente else "",
            frete.destino,
            destinatario.cidade if destinatario else "",
            frete.valor_servico or 0,
            "35 d",
        ])
        pontos_adicionais = pontos_adicionais_frete(frete)
        if pontos_adicionais and frete.valor_ponto_adicional is not None:
            primeiro_ponto = pontos_adicionais[0]
            empresa_ponto = empresas.get(primeiro_ponto)
            linhas.append([
                frete.nota_fiscal or "",
                frete.oc or "",
                frete.data_coleta.strftime("%d.%m"),
                frete.tipo_caminhao_necessario,
                frete.origem,
                remetente.cidade if remetente else "",
                primeiro_ponto,
                empresa_ponto.cidade if empresa_ponto else "",
                frete.valor_ponto_adicional or 0,
                "35 d",
            ])
        if frete.retorno and frete.valor_retorno is not None:
            linhas.append([
                frete.nota_fiscal or "",
                frete.oc or "",
                frete.data_coleta.strftime("%d.%m"),
                frete.tipo_caminhao_necessario,
                frete.destino,
                destinatario.cidade if destinatario else "",
                frete.origem,
                remetente.cidade if remetente else "",
                frete.valor_retorno or 0,
                "35 d",
            ])

    conteudo = criar_xlsx(linhas)
    nome = "fretes-concluidos.xlsx"
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@app.delete("/fretes/concluidos", tags=["Fretes"])
def excluir_fretes_concluidos(
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    cliente: Optional[str] = None,
    db: Session = Depends(get_db),
):
    consulta = db.query(models.Frete).filter(
        models.Frete.status.in_(["concluido", "Concluida"]),
        models.Frete.tipo_frete != "retorno",
    )
    if inicio:
        consulta = consulta.filter(models.Frete.data_coleta >= inicio)
    if fim:
        consulta = consulta.filter(models.Frete.data_coleta <= fim)
    if cliente:
        consulta = consulta.filter(models.Frete.cliente == cliente)

    fretes = consulta.all()
    total = len(fretes)
    for frete in fretes:
        db.delete(frete)

    db.commit()
    return {"mensagem": "Fretes concluidos excluidos", "total": total}


@app.put("/fretes/{frete_id}", response_model=schemas.FreteResponse, tags=["Fretes"])
def atualizar_frete(frete_id: int, frete: schemas.FreteUpdate, db: Session = Depends(get_db)):
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")
    dados = frete.model_dump(exclude_unset=True)

    for campo, valor in dados.items():
        setattr(db_frete, campo, valor)

    if any(campo in dados for campo in ["origem", "empresas_coleta", "destino"]):
        db_frete.rota = " -> ".join(
            ponto.strip()
            for ponto in [db_frete.origem, db_frete.empresas_coleta, db_frete.destino]
            if ponto and ponto.strip()
        )

    if "retorno" in dados:
        db_frete.pontoAdicional = dados["retorno"]

    db.commit()
    db.refresh(db_frete)
    return db_frete


@app.get("/fretes/{frete_id}/sugestao-valor", response_model=schemas.FreteSugestaoValorResponse, tags=["Fretes"])
def obter_sugestao_valor_frete(frete_id: int, db: Session = Depends(get_db)):
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")
    template = obter_template_valor_frete(db, db_frete)
    if not template:
        return {
            "possui_sugestao": False,
            "fonte": None,
            "qtd_usos": 0,
            "valor_servico": None,
            "valor_retorno": None,
            "valor_ponto_adicional": None,
        }
    return {
        "possui_sugestao": True,
        "fonte": template.fonte,
        "qtd_usos": template.qtd_usos or 0,
        "valor_servico": template.valor_padrao,
        "valor_retorno": template.valor_retorno,
        "valor_ponto_adicional": template.valor_ponto_adicional,
    }


@app.get("/fretes-templates/valores", response_model=list[schemas.FreteTemplateValorResponse], tags=["Fretes"])
def listar_templates_valores_frete(db: Session = Depends(get_db)):
    return (
        db.query(models.FreteTemplateValor)
        .order_by(models.FreteTemplateValor.updated_at.desc(), models.FreteTemplateValor.id.desc())
        .all()
    )


@app.put("/fretes-templates/valores/{template_id}", response_model=schemas.FreteTemplateValorResponse, tags=["Fretes"])
def atualizar_template_valor_frete(template_id: int, payload: schemas.FreteTemplateValorUpdate, db: Session = Depends(get_db)):
    template = obter_ou_404(db, models.FreteTemplateValor, template_id, "Template de valor nao encontrado")
    template.valor_padrao = payload.valor_padrao
    template.valor_retorno = payload.valor_retorno
    template.valor_ponto_adicional = payload.valor_ponto_adicional
    template.fonte = "manual_confirmado"
    template.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(template)
    return template


@app.put("/fretes/{frete_id}/valor", response_model=schemas.FreteResponse, tags=["Fretes"])
def atualizar_valor_frete(frete_id: int, valor: schemas.FreteValorUpdate, db: Session = Depends(get_db)):
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")
    db_frete.valor_servico = valor.valor_servico
    db_frete.valor_retorno = valor.valor_retorno
    db_frete.valor_ponto_adicional = valor.valor_ponto_adicional
    salvar_template_valor_frete(db, db_frete)
    db.commit()
    db.refresh(db_frete)
    return db_frete


@app.put("/fretes/{frete_id}/documentos", response_model=schemas.FreteResponse, tags=["Fretes"])
def atualizar_documentos_frete(frete_id: int, documentos: schemas.FreteDocumentosUpdate, db: Session = Depends(get_db)):
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")
    db_frete.cte = documentos.cte
    db_frete.oc = documentos.oc
    db.commit()
    db.refresh(db_frete)
    return db_frete


@app.put("/fretes/{frete_id}/nota-fiscal", response_model=schemas.FreteResponse, tags=["Fretes"])
def atualizar_nota_fiscal_frete(frete_id: int, nota: schemas.FreteNotaFiscalUpdate, db: Session = Depends(get_db)):
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")
    db_frete.nota_fiscal = nota.nota_fiscal
    db.commit()
    db.refresh(db_frete)
    return db_frete


@app.put("/fretes/{frete_id}/alocar", response_model=schemas.FreteResponse, tags=["Fretes"])
def alocar_frete(frete_id: int, alocacao: schemas.FreteUpdate, request: Request, db: Session = Depends(get_db)):
    dados_usuario = usuario_logado(request)
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")

    if dados_usuario["cargo"] == CARGO_MOTORISTA:
        motorista_id_usuario = dados_usuario["motorista_id"]
        if db_frete.motorista_id != motorista_id_usuario:
            raise HTTPException(status_code=403, detail="Este frete nao pertence ao motorista logado")
        if alocacao.motorista_id is not None and alocacao.motorista_id != motorista_id_usuario:
            raise HTTPException(status_code=403, detail="Nao e permitido trocar motorista")
        if alocacao.veiculo_id is not None:
            raise HTTPException(status_code=403, detail="Nao e permitido trocar caminhao")
        if not alocacao.status:
            raise HTTPException(status_code=400, detail="Status obrigatorio")
        db_frete.status = alocacao.status
        db.commit()
        db.refresh(db_frete)
        return db_frete

    if alocacao.motorista_id is not None:
        obter_ou_404(db, models.Motorista, alocacao.motorista_id, "Motorista nao encontrado")
        db_frete.motorista_id = alocacao.motorista_id
    if alocacao.veiculo_id is not None:
        obter_ou_404(db, models.Veiculo, alocacao.veiculo_id, "Veiculo nao encontrado")
        db_frete.veiculo_id = alocacao.veiculo_id
    if alocacao.status:
        db_frete.status = alocacao.status
    db.commit()
    db.refresh(db_frete)
    return db_frete


@app.delete("/fretes/{frete_id}", tags=["Fretes"])
def excluir_frete(frete_id: int, db: Session = Depends(get_db)):
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")
    retornos = db.query(models.Frete).filter(models.Frete.frete_principal_id == db_frete.id).all()
    for frete_retorno in retornos:
        db.delete(frete_retorno)
    db.delete(db_frete)
    db.commit()
    return {"mensagem": "Frete excluido"}


@app.get("/motoristas/historico/exportar", tags=["Alocacao"])
def exportar_historico_motoristas(db: Session = Depends(get_db)):
    motoristas = db.query(models.Motorista).order_by(models.Motorista.nome).all()
    abas = []

    for motorista in motoristas:
        fretes_motorista = (
            db.query(models.Frete)
            .filter(
                models.Frete.motorista_id == motorista.id,
                models.Frete.status.in_(["concluido", "Concluida"]),
            )
            .order_by(models.Frete.data_coleta, models.Frete.horario_coleta)
            .all()
        )
        linhas = [[None, "veiculo", "origem", "destino", "pontos adicionais", "obs"]]

        for frete in fretes_motorista:
            pontos = ", ".join(
                ponto.strip()
                for ponto in (frete.empresas_coleta or "").split(",")
                if ponto and ponto.strip()
            )
            linhas.append([
                frete.data_coleta.strftime("%d.%m"),
                frete.tipo_caminhao_necessario,
                frete.origem,
                frete.destino,
                pontos,
                frete.observacoes or "",
            ])

        abas.append((motorista.nome, linhas))

    if not abas:
        abas = [("Motoristas", [[None, "veiculo", "origem", "destino", "pontos adicionais", "obs"]])]

    conteudo = criar_xlsx_abas(abas)
    nome = "fretes-motoristas-controle.xlsx"
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )


@app.get("/motoristas/alocacao/", response_model=list[schemas.MotoristaComContagem], tags=["Alocacao"])
def listar_motoristas_alocacao(db: Session = Depends(get_db)):
    hoje = date.today()
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    fim_semana = inicio_semana + timedelta(days=6)

    motoristas = db.query(models.Motorista).order_by(models.Motorista.nome).all()

    return [
        {
            "id": motorista.id,
            "nome": motorista.nome,
            "telefone": motorista.telefone,
            "rg": motorista.rg,
            "cpf": motorista.cpf,
            "cnh": motorista.cnh,
            "observacoes": motorista.observacoes,
            "ativo": motorista.ativo,
            "viagens_dia": db.query(func.count(models.Frete.id))
            .filter(
                models.Frete.motorista_id == motorista.id,
                models.Frete.data_coleta == hoje,
                models.Frete.status != "Cancelada",
            )
            .scalar(),
            "viagens_semana": db.query(func.count(models.Frete.id))
            .filter(
                models.Frete.motorista_id == motorista.id,
                models.Frete.data_coleta >= inicio_semana,
                models.Frete.data_coleta <= fim_semana,
                models.Frete.status != "Cancelada",
            )
            .scalar(),
        }
        for motorista in motoristas
    ]


@app.get("/push/vapid-public-key", tags=["Push"])
def obter_vapid_public_key():
    return {"public_key": VAPID_PUBLIC_KEY}


@app.post("/push/subscribe", tags=["Push"])
def registrar_push_subscription(
    dados: schemas.PushSubscriptionCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    usuario = usuario_logado(request)
    usuario_id = int(usuario["id"])

    existente = db.query(models.PushSubscription).filter(
        models.PushSubscription.endpoint == dados.endpoint
    ).first()
    if existente:
        existente.p256dh = dados.p256dh
        existente.auth = dados.auth
        existente.usuario_id = usuario_id
        db.commit()
        return {"status": "atualizado"}

    nova = models.PushSubscription(
        usuario_id=usuario_id,
        endpoint=dados.endpoint,
        p256dh=dados.p256dh,
        auth=dados.auth,
    )
    db.add(nova)
    db.commit()
    return {"status": "inscrito"}


@app.delete("/push/subscribe", tags=["Push"])
def remover_push_subscription(
    dados: schemas.PushSubscriptionCreate,
    db: Session = Depends(get_db),
):
    db.query(models.PushSubscription).filter(
        models.PushSubscription.endpoint == dados.endpoint
    ).delete()
    db.commit()
    return {"status": "removido"}


# ---------------------------------------------------------------------------
# Assistente de chat (consultas em linguagem natural sobre o banco)
# ---------------------------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-5-mini")
CHAT_MAX_RODADAS_SQL = 6
CHAT_MAX_LINHAS_SQL = 200
CHAT_MAX_CHARS_RESULTADO = 20_000

_openai_client = None


def _obter_openai_client():
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


CHAT_PALAVRAS_PROIBIDAS_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|grant|revoke|"
    r"attach|detach|pragma|vacuum|reindex|copy|call|execute|merge|into)\b",
    re.IGNORECASE,
)
CHAT_TABELAS_PROIBIDAS_SQL = re.compile(
    r"\b(usuarios|push_subscriptions|senha_hash|google_sub)\b",
    re.IGNORECASE,
)


def _validar_sql_somente_leitura(sql: str) -> str:
    consulta = (sql or "").strip().rstrip(";").strip()
    if not consulta:
        raise ValueError("Consulta vazia.")
    if ";" in consulta:
        raise ValueError("Apenas uma instrucao por consulta.")
    if not re.match(r"^(select|with)\b", consulta, re.IGNORECASE):
        raise ValueError("Apenas consultas SELECT sao permitidas.")
    if CHAT_PALAVRAS_PROIBIDAS_SQL.search(consulta):
        raise ValueError("Consulta contem operacao nao permitida (somente leitura).")
    if CHAT_TABELAS_PROIBIDAS_SQL.search(consulta):
        raise ValueError("Esta tabela/coluna nao esta disponivel para o assistente.")
    if not re.search(r"\blimit\b", consulta, re.IGNORECASE):
        consulta = f"{consulta} LIMIT {CHAT_MAX_LINHAS_SQL}"
    return consulta


def _serializar_valor_sql(valor):
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if hasattr(valor, "isoformat"):
        return valor.isoformat()
    if isinstance(valor, (int, float, str, bool)) or valor is None:
        return valor
    return str(valor)


def _executar_sql_chat(sql: str) -> str:
    try:
        consulta = _validar_sql_somente_leitura(sql)
    except ValueError as exc:
        return json_module.dumps({"erro": str(exc)}, ensure_ascii=False)

    try:
        with SessionLocal() as db:
            resultado = db.execute(text(consulta))
            colunas = list(resultado.keys())
            linhas = [
                {coluna: _serializar_valor_sql(valor) for coluna, valor in zip(colunas, linha)}
                for linha in resultado.fetchmany(CHAT_MAX_LINHAS_SQL)
            ]
    except Exception as exc:
        return json_module.dumps(
            {"erro": f"Falha ao executar a consulta: {exc}"}, ensure_ascii=False
        )

    corpo = json_module.dumps(
        {"total_linhas": len(linhas), "linhas": linhas}, ensure_ascii=False, default=str
    )
    if len(corpo) > CHAT_MAX_CHARS_RESULTADO:
        corpo = json_module.dumps(
            {
                "erro": "Resultado muito grande. Refaca a consulta com agregacao (COUNT, SUM...) "
                "ou selecione menos colunas/linhas.",
                "total_linhas": len(linhas),
            },
            ensure_ascii=False,
        )
    return corpo


# Entidades que o assistente pode cadastrar/atualizar/excluir, reutilizando as
# mesmas funcoes (e validacoes) dos endpoints do site. Escrita e restrita a admin.
CHAT_ENTIDADES_ESCRITA = {
    "motorista": {
        "criar": (criar_motorista, schemas.MotoristaCreate),
        "atualizar": (atualizar_motorista, schemas.MotoristaUpdate),
        "excluir": excluir_motorista,
    },
    "veiculo": {
        "criar": (criar_veiculo, schemas.VeiculoCreate),
        "atualizar": (atualizar_veiculo, schemas.VeiculoUpdate),
        "excluir": excluir_veiculo,
    },
    "empresa": {
        "criar": (criar_empresa, schemas.EmpresaCreate),
        "atualizar": (atualizar_empresa, schemas.EmpresaUpdate),
        "excluir": excluir_empresa,
    },
    "fornecedor": {
        "criar": (criar_fornecedor, schemas.FornecedorCreate),
        "atualizar": (atualizar_fornecedor, schemas.FornecedorUpdate),
        "excluir": excluir_fornecedor,
    },
    "prestador_servico": {
        "criar": (criar_prestador_servico, schemas.PrestadorServicoCreate),
        "atualizar": (atualizar_prestador_servico, schemas.PrestadorServicoUpdate),
        "excluir": excluir_prestador_servico,
    },
    "frete": {
        "criar": (criar_frete, schemas.FreteCreate),
        "atualizar": (atualizar_frete, schemas.FreteUpdate),
        "excluir": excluir_frete,
    },
    "ocorrencia_veiculo": {
        "criar": (criar_ocorrencia_veiculo, schemas.OcorrenciaVeiculoCreate),
        "atualizar": (atualizar_ocorrencia_veiculo, schemas.OcorrenciaVeiculoUpdate),
        "excluir": excluir_ocorrencia_veiculo,
    },
}


def _serializar_registro_chat(registro) -> dict:
    if isinstance(registro, dict):
        return {chave: _serializar_valor_sql(valor) for chave, valor in registro.items()}
    return {
        coluna.name: _serializar_valor_sql(getattr(registro, coluna.name))
        for coluna in registro.__table__.columns
    }


def _executar_escrita_chat(operacao: str, argumentos: dict, usuario: dict) -> str:
    def erro(mensagem, **extras):
        return json_module.dumps({"erro": mensagem, **extras}, ensure_ascii=False)

    if usuario.get("cargo") != CARGO_ADMIN:
        return erro("Apenas administradores podem executar acoes de escrita.")

    entidade = str(argumentos.get("entidade") or "")
    config = CHAT_ENTIDADES_ESCRITA.get(entidade)
    if not config:
        return erro(f"Entidade desconhecida: '{entidade}'.")

    try:
        if operacao == "cadastrar":
            funcao, schema_cls = config["criar"]
            payload = schema_cls(**(argumentos.get("dados") or {}))
            with SessionLocal() as db:
                registro = funcao(payload, db)

        elif operacao == "atualizar":
            registro_id = int(argumentos.get("registro_id"))
            funcao, schema_cls = config["atualizar"]
            payload = schema_cls(**(argumentos.get("dados") or {}))
            with SessionLocal() as db:
                registro = funcao(registro_id, payload, db)

        elif operacao == "excluir":
            if not argumentos.get("confirmado_pelo_usuario"):
                return erro(
                    "Exclusao bloqueada: o usuario ainda nao confirmou. Mostre o registro "
                    "e pergunte antes de chamar novamente com confirmado_pelo_usuario=true."
                )
            registro_id = int(argumentos.get("registro_id"))
            with SessionLocal() as db:
                registro = config["excluir"](registro_id, db)

        else:
            return erro(f"Operacao desconhecida: '{operacao}'.")

    except ValidationError as exc:
        detalhes = [
            f"{'.'.join(str(parte) for parte in e['loc'])}: {e['msg']}" for e in exc.errors()
        ]
        return erro("Dados invalidos para esta entidade.", detalhes=detalhes)
    except HTTPException as exc:
        return erro(str(exc.detail))
    except (TypeError, ValueError) as exc:
        return erro(f"Argumentos invalidos: {exc}")
    except Exception as exc:
        print(f"Erro em acao de escrita do chat ({operacao}/{entidade}): {exc}")
        return erro("Falha inesperada ao executar a acao.")

    return json_module.dumps(
        {"sucesso": True, "operacao": operacao, "entidade": entidade,
         "registro": _serializar_registro_chat(registro)},
        ensure_ascii=False,
        default=str,
    )


def _executar_ferramenta_chat(nome: str, argumentos: dict, usuario: dict) -> str:
    if nome == "executar_sql":
        return _executar_sql_chat(str(argumentos.get("sql", "")))
    if nome == "cadastrar_registro":
        return _executar_escrita_chat("cadastrar", argumentos, usuario)
    if nome == "atualizar_registro":
        return _executar_escrita_chat("atualizar", argumentos, usuario)
    if nome == "excluir_registro":
        return _executar_escrita_chat("excluir", argumentos, usuario)
    return json_module.dumps({"erro": "Ferramenta desconhecida."}, ensure_ascii=False)


CHAT_REGRAS_ESCRITA = """
ACOES DE ESCRITA (disponiveis para voce):
Alem de consultar, voce pode cadastrar, atualizar e excluir registros com as ferramentas
cadastrar_registro, atualizar_registro e excluir_registro.
Entidades: motorista, veiculo, empresa, fornecedor, prestador_servico, frete, ocorrencia_veiculo.

Regras de escrita:
- Antes de atualizar ou excluir, localize o registro com executar_sql para obter o id correto.
  Se houver mais de um candidato, liste-os e pergunte qual e o certo.
- EXCLUSAO: NUNCA exclua sem confirmacao explicita do usuario NESTA conversa. Primeiro mostre o
  registro (id e dados principais) e pergunte se confirma. So apos o usuario responder sim,
  chame excluir_registro com confirmado_pelo_usuario=true.
- Cadastro/atualizacao: se faltar campo obrigatorio, pergunte ao usuario. Nao invente valores.
  Apos executar, informe em uma linha o que foi feito, com o id do registro.
- Excluir motorista mantem os fretes do historico (ficam sem motorista vinculado) - avise isso ao
  pedir a confirmacao. Se a exclusao falhar por outros vinculos, explique e ofereca desativar em
  vez de excluir: atualizar_registro com dados {"ativo": false}.
- Cancelar um frete = atualizar_registro do frete com dados {"status": "Cancelada"}.
- Concluir um frete = atualizar status para 'concluido'. Alocar motorista/caminhao ao frete =
  atualizar motorista_id / veiculo_id (busque os ids pelos nomes/placas primeiro).

Campos do cadastro por entidade (obrigatorios primeiro):
- motorista: nome, telefone, rg (7 a 9 digitos), cpf (valido, com ou sem pontuacao); opcionais: cnh, observacoes
- veiculo: placa, tipo (Motoboy|Fiorino|Iveco|3/4|Toco|Truk|Carreta); opcionais: observacoes, observacao_estado
- empresa: nome, cnpj; opcionais: cliente (true se for cliente da transportadora), cep, logradouro,
  numero, complemento, bairro, cidade, uf, observacoes (o campo endereco e montado automaticamente)
- fornecedor: nome, marca; opcionais: telefone, cidade, uf, cep, logradouro, numero, bairro, observacoes
- prestador_servico: nome, tipo (valvula|mecanicos|bombistas|outros); opcionais: telefone, cidade, uf, observacoes
- frete: data_coleta (AAAA-MM-DD), horario_coleta (HH:MM), origem, destino, tipo_caminhao_necessario;
  opcionais: cliente (padrao Edscha), empresas_coleta (pontos adicionais separados por virgula),
  retorno (true/false), valor_servico, observacoes, motorista_id, veiculo_id, nota_fiscal, cte, oc
- ocorrencia_veiculo: veiculo_id, categoria, descricao; opcionais: urgencia (Baixa|Media|Alta), reportado_por
"""


def _montar_system_prompt_chat(usuario: dict) -> str:
    agora = datetime.now(ZoneInfo(TIMEZONE))
    dialeto = engine.dialect.name  # "sqlite" ou "postgresql"
    regras_escrita = CHAT_REGRAS_ESCRITA if usuario.get("cargo") == CARGO_ADMIN else ""
    return f"""Voce e o assistente interno da Acelera Transportes, uma transportadora. \
Voce responde perguntas dos funcionarios consultando o banco de dados do sistema de gestao de fretes.

Data e hora atual: {agora.strftime("%Y-%m-%d %H:%M")} ({agora.strftime("%A")}), fuso {TIMEZONE}.
Usuario logado: {usuario.get("nome")} (cargo: {usuario.get("cargo")}).
Dialeto SQL do banco: {dialeto}.

REGRAS:
- Use a ferramenta executar_sql para buscar dados reais antes de responder. Nunca invente dados.
- Se a consulta nao retornar nada, diga claramente que nao encontrou.
- Responda sempre em portugues do Brasil, de forma direta e organizada.
- Responda em TEXTO SIMPLES, sem markdown (sem asteriscos, sem #). Use listas com "-" e quebras de linha.
- Valores monetarios no formato R$ 1.234,56. Datas no formato DD/MM/AAAA.
- Buscas por nome de pessoa/empresa devem ser aproximadas: use LIKE com % e sem diferenciar maiusculas (ex.: WHERE lower(nome) LIKE lower('%joao%')).
- "Esta semana" = de segunda a domingo da semana atual, salvo indicacao contraria.

SCHEMA DO BANCO (tabelas disponiveis):

motoristas(id, nome, telefone, rg, cpf, cnh, observacoes, ativo)

veiculos(id, placa, tipo, observacoes, observacao_estado, motivo_indisponibilidade, ativo)
- tipo: Motoboy, Fiorino, Iveco, 3/4, Toco, Truk, Carreta

empresas(id, nome, cnpj, cliente, cep, logradouro, numero, complemento, bairro, cidade, uf, endereco, observacoes, ativo)
- cliente (boolean): true quando a empresa e cliente da transportadora

fornecedores(id, nome, telefone, cidade, uf, marca, endereco, observacoes, ativo)

prestadores_servicos(id, nome, telefone, cidade, uf, tipo, endereco, observacoes, ativo)
- tipo: valvula, mecanicos, bombistas, outros

fretes(id, cliente, cte, oc, nota_fiscal, data_coleta, horario_coleta, origem, empresas_coleta, destino, rota,
       tipo_caminhao_necessario, retorno, tipo_frete, frete_principal_id, status,
       valor_servico, valor_retorno, valor_ponto_adicional, observacoes,
       motorista_id, veiculo_id, checklist_confirmado, checklist_confirmado_em)
- cliente: nome do cliente (texto)
- data_coleta: DATE / horario_coleta: TIME
- status: 'Aguardando horario', 'A caminho P1', 'coletado P1', 'A caminho ponto adicional',
  'Pontos adicionais', 'A caminho destino', 'Chegada no destino', 'retornando', 'concluido', 'Cancelada'
  (frete concluido = status 'concluido' ou 'Concluida')
- tipo_frete: 'principal' ou 'retorno'. IMPORTANTE: ao contar/listar fretes, considere apenas
  tipo_frete = 'principal' e status <> 'Cancelada', salvo se o usuario pedir o contrario.
- valor total de um frete = COALESCE(valor_servico,0) + COALESCE(valor_retorno,0) + COALESCE(valor_ponto_adicional,0)
- empresas_coleta: pontos adicionais de coleta separados por virgula (texto)
- motorista_id -> motoristas.id / veiculo_id -> veiculos.id (use JOIN para trazer nomes/placas)

ocorrencias_veiculos(id, veiculo_id, categoria, descricao, urgencia, reportado_por, criado_em, status, resolucao, resolvido_em)
- urgencia: Baixa/Media/Alta; status: 'Aberto' ou 'Resolvido'

fretes_templates_valores(id, empresa_id, caminhao_contratado_id, origem_id, destino_id,
                         tem_retorno, tem_ponto_adicional, valor_padrao, valor_retorno,
                         valor_ponto_adicional, fonte, qtd_usos, updated_at)
- historico de valores praticados por rota/cliente/caminhao

As tabelas de usuarios do sistema NAO estao disponiveis.
{regras_escrita}"""


CHAT_ENTIDADES_NOMES = list(CHAT_ENTIDADES_ESCRITA.keys())

CHAT_TOOLS_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "executar_sql",
            "description": (
                "Executa uma consulta SQL somente leitura (SELECT) no banco de dados da "
                "transportadora e retorna as linhas em JSON. Use JOINs para trazer nomes de "
                "motoristas e placas de veiculos. Prefira agregacoes (COUNT, SUM) quando a "
                "pergunta for quantitativa."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "A consulta SELECT a executar.",
                    }
                },
                "required": ["sql"],
            },
        },
    }
]

CHAT_TOOLS_ESCRITA_OPENAI = [
    {
        "type": "function",
        "function": {
            "name": "cadastrar_registro",
            "description": (
                "Cadastra um novo registro no sistema (motorista, veiculo, empresa, fornecedor, "
                "prestador de servico, frete ou ocorrencia de veiculo). Os dados passam pelas "
                "mesmas validacoes dos formularios do site."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "entidade": {"type": "string", "enum": CHAT_ENTIDADES_NOMES},
                    "dados": {
                        "type": "object",
                        "description": "Campos do registro conforme a entidade (ver regras no prompt).",
                    },
                },
                "required": ["entidade", "dados"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "atualizar_registro",
            "description": (
                "Atualiza campos de um registro existente. Envie apenas os campos que devem "
                "mudar. Use executar_sql antes para descobrir o id do registro. Tambem serve "
                "para desativar/reativar (campo ativo), cancelar frete (status='Cancelada'), "
                "concluir frete (status='concluido') e alocar motorista/veiculo em frete."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "entidade": {"type": "string", "enum": CHAT_ENTIDADES_NOMES},
                    "registro_id": {"type": "integer", "description": "O id do registro."},
                    "dados": {
                        "type": "object",
                        "description": "Somente os campos a alterar.",
                    },
                },
                "required": ["entidade", "registro_id", "dados"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "excluir_registro",
            "description": (
                "Exclui permanentemente um registro. So chame depois que o usuario confirmar "
                "explicitamente a exclusao nesta conversa."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "entidade": {"type": "string", "enum": CHAT_ENTIDADES_NOMES},
                    "registro_id": {"type": "integer", "description": "O id do registro."},
                    "confirmado_pelo_usuario": {
                        "type": "boolean",
                        "description": "true somente se o usuario confirmou a exclusao na conversa.",
                    },
                },
                "required": ["entidade", "registro_id", "confirmado_pelo_usuario"],
            },
        },
    },
]


def _tools_chat_para_usuario(usuario: dict) -> list:
    if usuario.get("cargo") == CARGO_ADMIN:
        return CHAT_TOOLS_OPENAI + CHAT_TOOLS_ESCRITA_OPENAI
    return CHAT_TOOLS_OPENAI


def _gerar_resposta_chat(mensagens_openai: list, usuario: dict):
    client = _obter_openai_client()
    tools = _tools_chat_para_usuario(usuario)

    for _ in range(CHAT_MAX_RODADAS_SQL):
        stream = client.chat.completions.create(
            model=OPENAI_CHAT_MODEL,
            messages=mensagens_openai,
            tools=tools,
            max_completion_tokens=3000,
            stream=True,
        )

        conteudo_parcial = []
        tool_calls_parciais = {}
        finish_reason = None

        for chunk in stream:
            if not chunk.choices:
                continue
            escolha = chunk.choices[0]
            delta = escolha.delta

            if delta and delta.content:
                conteudo_parcial.append(delta.content)
                yield delta.content

            if delta and delta.tool_calls:
                for tc in delta.tool_calls:
                    acumulado = tool_calls_parciais.setdefault(
                        tc.index, {"id": "", "nome": "", "argumentos": []}
                    )
                    if tc.id:
                        acumulado["id"] = tc.id
                    if tc.function and tc.function.name:
                        acumulado["nome"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        acumulado["argumentos"].append(tc.function.arguments)

            if escolha.finish_reason:
                finish_reason = escolha.finish_reason

        if finish_reason != "tool_calls" or not tool_calls_parciais:
            return

        tool_calls_msg = []
        resultados_tools = []
        for indice in sorted(tool_calls_parciais):
            chamada = tool_calls_parciais[indice]
            argumentos_brutos = "".join(chamada["argumentos"])
            tool_calls_msg.append(
                {
                    "id": chamada["id"],
                    "type": "function",
                    "function": {"name": chamada["nome"], "arguments": argumentos_brutos},
                }
            )
            try:
                argumentos = json_module.loads(argumentos_brutos or "{}")
            except json_module.JSONDecodeError:
                argumentos = {}

            resultado = _executar_ferramenta_chat(chamada["nome"], argumentos, usuario)

            resultados_tools.append(
                {"role": "tool", "tool_call_id": chamada["id"], "content": resultado}
            )

        mensagens_openai.append(
            {
                "role": "assistant",
                "content": "".join(conteudo_parcial) or None,
                "tool_calls": tool_calls_msg,
            }
        )
        mensagens_openai.extend(resultados_tools)

    yield "\n\nNao consegui concluir a consulta. Tente reformular a pergunta."


@app.post("/chat", tags=["Assistente"])
def conversar_com_assistente(dados: schemas.ChatRequest, request: Request):
    if not OPENAI_DISPONIVEL:
        raise HTTPException(status_code=503, detail="Biblioteca openai nao instalada no servidor.")
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY nao configurada no servidor.")

    usuario = usuario_logado(request)

    mensagens_openai = [{"role": "system", "content": _montar_system_prompt_chat(usuario)}]
    for mensagem in dados.mensagens:
        mensagens_openai.append({"role": mensagem.papel, "content": mensagem.texto})

    def fluxo():
        try:
            yield from _gerar_resposta_chat(mensagens_openai, usuario)
        except Exception as exc:
            print(f"Erro no assistente de chat: {exc}")
            yield "\n\nDesculpe, ocorreu um erro ao consultar o assistente. Tente novamente."

    return StreamingResponse(
        fluxo(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )
