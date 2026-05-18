import io
import zipfile
from datetime import date, timedelta
from typing import Optional
from xml.sax.saxutils import escape

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import func, inspect, text
from sqlalchemy.orm import Session

import models
import schemas
from database import SessionLocal, engine


STATUS_FRETE = [
    "Aguardando horario",
    "A caminho P1",
    "coletado P1",
    "retornando",
    "concluido",
    "Cancelada",
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
            "valor_servico": "ALTER TABLE fretes ADD COLUMN valor_servico FLOAT",
            "observacoes": "ALTER TABLE fretes ADD COLUMN observacoes TEXT",
        }

        with engine.begin() as conexao:
            for coluna, comando in ajustes.items():
                if coluna not in colunas:
                    conexao.execute(text(comando))

    if "motoristas" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("motoristas")}
        if "observacoes" not in colunas:
            with engine.begin() as conexao:
                conexao.execute(text("ALTER TABLE motoristas ADD COLUMN observacoes TEXT"))

    if "veiculos" in tabelas:
        colunas = {coluna["name"] for coluna in inspector.get_columns("veiculos")}
        if "observacoes" not in colunas:
            with engine.begin() as conexao:
                conexao.execute(text("ALTER TABLE veiculos ADD COLUMN observacoes TEXT"))

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
    db_motorista = models.Motorista(**motorista.model_dump())
    db.add(db_motorista)
    db.commit()
    db.refresh(db_motorista)
    return db_motorista


@app.get("/motoristas/", response_model=list[schemas.MotoristaResponse], tags=["Motoristas"])
def listar_motoristas(db: Session = Depends(get_db)):
    return db.query(models.Motorista).order_by(models.Motorista.nome).all()


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
    db.commit()
    db.refresh(db_veiculo)
    return db_veiculo


@app.get("/veiculos/", response_model=list[schemas.VeiculoResponse], tags=["Veiculos"])
def listar_veiculos(db: Session = Depends(get_db)):
    return db.query(models.Veiculo).order_by(models.Veiculo.placa).all()


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


@app.delete("/empresas/{empresa_id}", tags=["Empresas"])
def excluir_empresa(empresa_id: int, db: Session = Depends(get_db)):
    db_empresa = obter_ou_404(db, models.Empresa, empresa_id, "Empresa nao encontrada")
    db.delete(db_empresa)
    db.commit()
    return {"mensagem": "Empresa excluida"}


@app.post("/fretes/", response_model=schemas.FreteResponse, tags=["Fretes"])
def criar_frete(frete: schemas.FreteCreate, db: Session = Depends(get_db)):
    dados = frete.model_dump()
    dados["rota"] = montar_rota(frete)
    dados["pontoAdicional"] = frete.retorno
    db_frete = models.Frete(**dados)
    db.add(db_frete)
    db.commit()
    db.refresh(db_frete)
    return db_frete


@app.get("/fretes/", response_model=list[schemas.FreteResponse], tags=["Fretes"])
def listar_fretes(db: Session = Depends(get_db)):
    return db.query(models.Frete).order_by(models.Frete.data_coleta, models.Frete.horario_coleta).all()


@app.get("/fretes/concluidos/exportar", tags=["Fretes"])
def exportar_fretes_concluidos(
    inicio: Optional[date] = None,
    fim: Optional[date] = None,
    cliente: Optional[str] = None,
    db: Session = Depends(get_db),
):
    consulta = db.query(models.Frete).filter(models.Frete.status.in_(["concluido", "Concluida"]))
    if inicio:
        consulta = consulta.filter(models.Frete.data_coleta >= inicio)
    if fim:
        consulta = consulta.filter(models.Frete.data_coleta <= fim)
    if cliente:
        consulta = consulta.filter(models.Frete.cliente == cliente)

    fretes = consulta.order_by(models.Frete.data_coleta, models.Frete.horario_coleta).all()
    empresas = {empresa.nome: empresa for empresa in db.query(models.Empresa).all()}

    linhas = [[
        "CTE",
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
            frete.cte or "",
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
    consulta = db.query(models.Frete).filter(models.Frete.status.in_(["concluido", "Concluida"]))
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
    db.delete(db_frete)
    db.commit()
    return {"mensagem": "Frete excluido"}


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
