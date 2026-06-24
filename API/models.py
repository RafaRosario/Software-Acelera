from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, Date, Time, DateTime, ForeignKey, Text, Float, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Motorista(Base):
    __tablename__ = "motoristas"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=False)
    rg = Column(String, nullable=False)
    cpf = Column(String, nullable=False)
    cnh = Column(String, nullable=True)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (UniqueConstraint("email", name="uq_usuarios_email"),)

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True, unique=True)
    senha_hash = Column(String, nullable=True)
    cargo = Column(String, nullable=False, default="controle")
    google_sub = Column(String, nullable=True, unique=True)
    avatar_url = Column(String, nullable=True)
    ativo = Column(Boolean, default=True)
    motorista_id = Column(Integer, ForeignKey("motoristas.id"), nullable=True, unique=True)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    motorista = relationship("Motorista")

class Veiculo(Base):
    __tablename__ = "veiculos"
    __table_args__ = (UniqueConstraint("placa", "tipo", name="uq_veiculos_placa_tipo"),)
    
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    observacoes = Column(Text, nullable=True)
    observacao_estado = Column(Text, nullable=True)
    motivo_indisponibilidade = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)

class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    cnpj = Column(String, nullable=False)
    cliente = Column(Boolean, default=False)
    cep = Column(String, nullable=True)
    logradouro = Column(String, nullable=True)
    numero = Column(String, nullable=True)
    complemento = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    cidade = Column(String, nullable=True)
    uf = Column(String, nullable=True)
    endereco = Column(Text, nullable=False)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)

class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=True)
    cep = Column(String, nullable=True)
    logradouro = Column(String, nullable=True)
    numero = Column(String, nullable=True)
    complemento = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    endereco = Column(Text, nullable=False)
    cidade = Column(String, nullable=False)
    uf = Column(String, nullable=True)
    marca = Column(String, nullable=False)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)

class PrestadorServico(Base):
    __tablename__ = "prestadores_servicos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    telefone = Column(String, nullable=True)
    cep = Column(String, nullable=True)
    logradouro = Column(String, nullable=True)
    rua = Column(String, nullable=False)
    numero = Column(String, nullable=True)
    complemento = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    cidade = Column(String, nullable=False)
    uf = Column(String, nullable=True)
    endereco = Column(Text, nullable=False, default="")
    tipo = Column(String, nullable=False)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)

class Frete(Base):
    __tablename__ = "fretes"
    
    id = Column(Integer, primary_key=True, index=True)
    cliente = Column(String, nullable=False, default="Edscha")
    cte = Column(String, nullable=True)
    oc = Column(String, nullable=True)
    nota_fiscal = Column(String, nullable=True)
    data_coleta = Column(Date, nullable=False)
    horario_coleta = Column(Time, nullable=False)
    origem = Column(String, nullable=False, default="Edscha")
    empresas_coleta = Column(Text, nullable=True)
    destino = Column(String, nullable=False, default="")
    rota = Column(String, nullable=False, default="")
    tipo_caminhao_necessario = Column(String, nullable=False)
    retorno = Column(Boolean, default=False)
    tipo_frete = Column(String, nullable=False, default="principal")
    frete_principal_id = Column(Integer, ForeignKey("fretes.id"), nullable=True)
    status = Column(String, default="Aguardando horario")
    valor_servico = Column(Float, nullable=True)
    valor_retorno = Column(Float, nullable=True)
    valor_ponto_adicional = Column(Float, nullable=True)
    observacoes = Column(Text, nullable=True)
    pontoAdicional = Column(Boolean, default=False)
    checklist_token = Column(String, nullable=True, index=True)
    checklist_tacografo = Column(Boolean, default=False)
    checklist_pneus = Column(Boolean, default=False)
    checklist_oleo = Column(Boolean, default=False)
    checklist_avarias_externas = Column(Boolean, default=False)
    checklist_avarias_internas = Column(Boolean, default=False)
    checklist_luzes = Column(Boolean, default=False)
    checklist_confirmado = Column(Boolean, default=False)
    checklist_confirmado_em = Column(DateTime, nullable=True)
    checklist_observacoes = Column(Text, nullable=True)
    ultima_notificacao_push = Column(DateTime, nullable=True)

    motorista_id = Column(Integer, ForeignKey("motoristas.id"), nullable=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=True)
    
    motorista = relationship("Motorista")
    veiculo = relationship("Veiculo")
    frete_principal = relationship("Frete", remote_side=[id])


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)

    usuario = relationship("Usuario")


class FreteTemplateValor(Base):
    __tablename__ = "fretes_templates_valores"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "caminhao_contratado_id",
            "origem_id",
            "destino_id",
            "tem_retorno",
            "tem_ponto_adicional",
            name="uq_frete_template_chave",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(String, nullable=False)
    caminhao_contratado_id = Column(String, nullable=False)
    origem_id = Column(String, nullable=False)
    destino_id = Column(String, nullable=False)
    tem_retorno = Column(Boolean, nullable=False, default=False)
    tem_ponto_adicional = Column(Boolean, nullable=False, default=False)
    valor_padrao = Column(Float, nullable=True)
    valor_retorno = Column(Float, nullable=True)
    valor_ponto_adicional = Column(Float, nullable=True)
    fonte = Column(String, nullable=False, default="manual_confirmado")
    qtd_usos = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
