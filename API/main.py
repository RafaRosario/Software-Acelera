import io
import secrets
import zipfile
from datetime import date, datetime, timedelta
from typing import Optional
from xml.sax.saxutils import escape

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import func, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas
from database import SessionLocal, engine


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
            "checklist_confirmado": "ALTER TABLE fretes ADD COLUMN checklist_confirmado BOOLEAN DEFAULT 0",
            "checklist_confirmado_em": "ALTER TABLE fretes ADD COLUMN checklist_confirmado_em DATETIME",
            "checklist_observacoes": "ALTER TABLE fretes ADD COLUMN checklist_observacoes TEXT",
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

    if "veiculos" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("veiculos")}
        ajustes = {
            "observacoes": "ALTER TABLE veiculos ADD COLUMN observacoes TEXT",
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
                        motivo_indisponibilidade TEXT,
                        ativo BOOLEAN,
                        PRIMARY KEY (id),
                        CONSTRAINT uq_veiculos_placa_tipo UNIQUE (placa, tipo)
                    )
                """))
                conexao.execute(text("""
                    INSERT INTO veiculos (id, placa, tipo, observacoes, motivo_indisponibilidade, ativo)
                    SELECT id, placa, tipo, observacoes, motivo_indisponibilidade, COALESCE(ativo, 1)
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


preparar_banco()

app = FastAPI(title="API Acelera Transportes")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        "confirmado": bool(frete.checklist_confirmado),
        "confirmado_em": frete.checklist_confirmado_em,
        "observacoes": frete.checklist_observacoes,
    }


def pontos_adicionais_frete(frete: models.Frete) -> list[str]:
    return [ponto.strip() for ponto in (frete.empresas_coleta or "").split(",") if ponto and ponto.strip()]


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
    db.delete(db_motorista)
    db.commit()
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
def listar_fretes(db: Session = Depends(get_db)):
    return db.query(models.Frete).order_by(models.Frete.data_coleta, models.Frete.horario_coleta).all()


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


@app.put("/fretes/{frete_id}/valor", response_model=schemas.FreteResponse, tags=["Fretes"])
def atualizar_valor_frete(frete_id: int, valor: schemas.FreteValorUpdate, db: Session = Depends(get_db)):
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")
    db_frete.valor_servico = valor.valor_servico
    db_frete.valor_retorno = valor.valor_retorno
    db_frete.valor_ponto_adicional = valor.valor_ponto_adicional
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
def alocar_frete(frete_id: int, alocacao: schemas.FreteUpdate, db: Session = Depends(get_db)):
    db_frete = obter_ou_404(db, models.Frete, frete_id, "Frete nao encontrado")
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
