from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class MotoristaBase(BaseModel):
    nome: str
    telefone: str
    rg: str
    cpf: str
    cnh: Optional[str] = None
    observacoes: Optional[str] = None

class MotoristaCreate(MotoristaBase):
    pass

class MotoristaResponse(MotoristaBase):
    id: int
    ativo: bool

    class Config:
        from_attributes = True

class VeiculoBase(BaseModel):
    placa: str
    tipo: str
    observacoes: Optional[str] = None

class VeiculoCreate(VeiculoBase):
    pass

class VeiculoResponse(VeiculoBase):
    id: int
    ativo: bool

    class Config:
        from_attributes = True

class EmpresaBase(BaseModel):
    nome: str
    cnpj: str
    cliente: bool = False
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    observacoes: Optional[str] = None

class EmpresaCreate(EmpresaBase):
    pass

class EmpresaResponse(EmpresaBase):
    id: int
    ativo: bool

    class Config:
        from_attributes = True

class FreteBase(BaseModel):
    cliente: str = "Edscha"
    cte: Optional[str] = None
    oc: Optional[str] = None
    nota_fiscal: Optional[str] = None
    data_coleta: date
    horario_coleta: time
    origem: str
    empresas_coleta: Optional[str] = None
    destino: str
    tipo_caminhao_necessario: str
    retorno: bool = False
    status: str = "Aguardando horario"
    valor_servico: Optional[float] = None
    observacoes: Optional[str] = None
    motorista_id: Optional[int] = None
    veiculo_id: Optional[int] = None
    pontoAdicional: bool = False

class FreteCreate(FreteBase):
    pass

class FreteResponse(FreteBase):
    id: int

    class Config:
        from_attributes = True

class FreteUpdate(BaseModel):
    cliente: Optional[str] = None
    cte: Optional[str] = None
    oc: Optional[str] = None
    nota_fiscal: Optional[str] = None
    data_coleta: Optional[date] = None
    horario_coleta: Optional[time] = None
    origem: Optional[str] = None
    empresas_coleta: Optional[str] = None
    destino: Optional[str] = None
    tipo_caminhao_necessario: Optional[str] = None
    retorno: Optional[bool] = None
    status: Optional[str] = None
    valor_servico: Optional[float] = None
    observacoes: Optional[str] = None
    motorista_id: Optional[int] = None
    veiculo_id: Optional[int] = None

class FreteValorUpdate(BaseModel):
    valor_servico: Optional[float] = None

class FreteDocumentosUpdate(BaseModel):
    cte: Optional[str] = None
    oc: Optional[str] = None

class FreteNotaFiscalUpdate(BaseModel):
    nota_fiscal: Optional[str] = None

class MotoristaComContagem(MotoristaResponse):
    viagens_dia: int
    viagens_semana: int
