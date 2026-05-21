import re

from pydantic import BaseModel, field_validator
from datetime import date, time
from typing import Optional

class MotoristaBase(BaseModel):
    nome: str
    telefone: str
    rg: str
    cpf: str
    cnh: Optional[str] = None
    observacoes: Optional[str] = None

    @field_validator("rg")
    @classmethod
    def validar_rg(cls, valor: str) -> str:
        limpo = re.sub(r"[^0-9xX]", "", valor or "").upper()
        if not 7 <= len(limpo) <= 9:
            raise ValueError("RG invalido")
        return valor

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: str) -> str:
        cpf = re.sub(r"\D", "", valor or "")
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            raise ValueError("CPF invalido")

        def digito(base: str) -> int:
            soma = sum(int(numero) * (len(base) + 1 - indice) for indice, numero in enumerate(base))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto

        if digito(cpf[:9]) != int(cpf[9]) or digito(cpf[:10]) != int(cpf[10]):
            raise ValueError("CPF invalido")

        return valor

class MotoristaCreate(MotoristaBase):
    pass

class MotoristaUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    rg: Optional[str] = None
    cpf: Optional[str] = None
    cnh: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None

    @field_validator("rg")
    @classmethod
    def validar_rg(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        limpo = re.sub(r"[^0-9xX]", "", valor or "").upper()
        if not 7 <= len(limpo) <= 9:
            raise ValueError("RG invalido")
        return valor

    @field_validator("cpf")
    @classmethod
    def validar_cpf(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        cpf = re.sub(r"\D", "", valor or "")
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            raise ValueError("CPF invalido")

        def digito(base: str) -> int:
            soma = sum(int(numero) * (len(base) + 1 - indice) for indice, numero in enumerate(base))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto

        if digito(cpf[:9]) != int(cpf[9]) or digito(cpf[:10]) != int(cpf[10]):
            raise ValueError("CPF invalido")

        return valor

class MotoristaResponse(MotoristaBase):
    id: int
    ativo: bool

    class Config:
        from_attributes = True

class VeiculoBase(BaseModel):
    placa: str
    tipo: str
    observacoes: Optional[str] = None
    motivo_indisponibilidade: Optional[str] = None

class VeiculoCreate(VeiculoBase):
    pass

class VeiculoResponse(VeiculoBase):
    id: int
    ativo: bool

    class Config:
        from_attributes = True

class VeiculoUpdate(BaseModel):
    placa: Optional[str] = None
    tipo: Optional[str] = None
    ativo: Optional[bool] = None
    observacoes: Optional[str] = None
    motivo_indisponibilidade: Optional[str] = None

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

class EmpresaUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    cliente: Optional[bool] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None

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
    tipo_frete: str = "principal"
    frete_principal_id: Optional[int] = None
    status: str = "Aguardando horario"
    valor_servico: Optional[float] = None
    valor_retorno: Optional[float] = None
    valor_ponto_adicional: Optional[float] = None
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
    tipo_frete: Optional[str] = None
    frete_principal_id: Optional[int] = None
    status: Optional[str] = None
    valor_servico: Optional[float] = None
    valor_retorno: Optional[float] = None
    valor_ponto_adicional: Optional[float] = None
    observacoes: Optional[str] = None
    motorista_id: Optional[int] = None
    veiculo_id: Optional[int] = None

class FreteValorUpdate(BaseModel):
    valor_servico: Optional[float] = None
    valor_retorno: Optional[float] = None
    valor_ponto_adicional: Optional[float] = None

class FreteDocumentosUpdate(BaseModel):
    cte: Optional[str] = None
    oc: Optional[str] = None

class FreteNotaFiscalUpdate(BaseModel):
    nota_fiscal: Optional[str] = None

class MotoristaComContagem(MotoristaResponse):
    viagens_dia: int
    viagens_semana: int
