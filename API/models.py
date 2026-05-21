from sqlalchemy import Column, Integer, String, Boolean, Date, Time, ForeignKey, Text, Float
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

class Veiculo(Base):
    __tablename__ = "veiculos"
    
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, unique=True, nullable=False)
    tipo = Column(String, nullable=False)
    observacoes = Column(Text, nullable=True)
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
    
    motorista_id = Column(Integer, ForeignKey("motoristas.id"), nullable=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=True)
    
    motorista = relationship("Motorista")
    veiculo = relationship("Veiculo")
    frete_principal = relationship("Frete", remote_side=[id])
