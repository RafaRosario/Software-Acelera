import re

from pydantic import BaseModel, field_validator, model_validator
from datetime import date, datetime, time
from typing import Literal, Optional

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
    observacao_estado: Optional[str] = None
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
    observacao_estado: Optional[str] = None
    motivo_indisponibilidade: Optional[str] = None


class OcorrenciaVeiculoBase(BaseModel):
    veiculo_id: int
    categoria: str
    descricao: str
    urgencia: str = "Baixa"
    reportado_por: Optional[str] = None


class OcorrenciaVeiculoCreate(OcorrenciaVeiculoBase):
    pass


class OcorrenciaVeiculoUpdate(BaseModel):
    categoria: Optional[str] = None
    descricao: Optional[str] = None
    urgencia: Optional[str] = None
    reportado_por: Optional[str] = None
    status: Optional[str] = None
    resolucao: Optional[str] = None


class OcorrenciaVeiculoResponse(OcorrenciaVeiculoBase):
    id: int
    status: str
    resolucao: Optional[str] = None
    criado_em: datetime
    resolvido_em: Optional[datetime] = None

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

class FornecedorBase(BaseModel):
    nome: str
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    marca: str
    observacoes: Optional[str] = None

class FornecedorCreate(FornecedorBase):
    pass

class FornecedorUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    marca: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None

class FornecedorResponse(FornecedorBase):
    id: int
    ativo: bool

    class Config:
        from_attributes = True

class PrestadorServicoBase(BaseModel):
    nome: str
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    tipo: str
    observacoes: Optional[str] = None

class PrestadorServicoCreate(PrestadorServicoBase):
    pass

class PrestadorServicoUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    cep: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None
    endereco: Optional[str] = None
    tipo: Optional[str] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None

class PrestadorServicoResponse(PrestadorServicoBase):
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
    checklist_token: Optional[str] = None
    checklist_tacografo: bool = False
    checklist_pneus: bool = False
    checklist_oleo: bool = False
    checklist_avarias_externas: bool = False
    checklist_avarias_internas: bool = False
    checklist_luzes: bool = False
    checklist_confirmado: bool = False
    checklist_confirmado_em: Optional[datetime] = None
    checklist_observacoes: Optional[str] = None

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


class FreteSugestaoValorResponse(BaseModel):
    possui_sugestao: bool
    fonte: Optional[str] = None
    qtd_usos: int = 0
    valor_servico: Optional[float] = None
    valor_retorno: Optional[float] = None
    valor_ponto_adicional: Optional[float] = None


class FreteTemplateValorResponse(BaseModel):
    id: int
    empresa_id: str
    caminhao_contratado_id: str
    origem_id: str
    destino_id: str
    tem_retorno: bool
    tem_ponto_adicional: bool
    valor_padrao: Optional[float] = None
    valor_retorno: Optional[float] = None
    valor_ponto_adicional: Optional[float] = None
    fonte: str
    qtd_usos: int
    updated_at: datetime

    class Config:
        from_attributes = True


class FreteTemplateValorUpdate(BaseModel):
    valor_padrao: Optional[float] = None
    valor_retorno: Optional[float] = None
    valor_ponto_adicional: Optional[float] = None

class ChecklistFreteResponse(BaseModel):
    token: str
    frete_id: int
    caminhao: str
    placa: str
    motorista: str
    origem: str
    destino: str
    data_coleta: date
    horario_coleta: time
    tacografo: bool = False
    pneus: bool = False
    oleo: bool = False
    avarias_externas: bool = False
    avarias_internas: bool = False
    luzes: bool = False
    confirmado: bool = False
    confirmado_em: Optional[datetime] = None
    observacoes: Optional[str] = None

class ChecklistFreteUpdate(BaseModel):
    tacografo: bool = False
    pneus: bool = False
    oleo: bool = False
    avarias_externas: bool = False
    avarias_internas: bool = False
    luzes: bool = False
    observacoes: Optional[str] = None

class MotoristaComContagem(MotoristaResponse):
    viagens_dia: int
    viagens_semana: int


CargoUsuario = Literal["admin", "controle", "motorista"]


def _normalizar_email(valor: str) -> str:
    return (valor or "").strip().lower()


def _validar_email_simples(valor: str) -> str:
    if "@" not in valor or valor.startswith("@") or valor.endswith("@"):
        raise ValueError("Email invalido")
    return valor


class UsuarioSessao(BaseModel):
    id: int
    nome: str
    email: str
    cargo: CargoUsuario
    motorista_id: Optional[int] = None
    avatar_url: Optional[str] = None


class AuthLoginRequest(BaseModel):
    email: str
    senha: str
    nome: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        email = _normalizar_email(valor)
        return _validar_email_simples(email)

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, valor: str) -> str:
        senha = (valor or "").strip()
        if len(senha) < 6:
            raise ValueError("Senha deve ter no minimo 6 caracteres")
        return senha

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        nome = valor.strip()
        if nome and len(nome) < 2:
            raise ValueError("Nome invalido")
        return nome or None


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioSessao


class UsuarioSistemaBase(BaseModel):
    nome: str
    email: str
    cargo: CargoUsuario = "controle"
    motorista_id: Optional[int] = None
    ativo: bool = True

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: str) -> str:
        nome = (valor or "").strip()
        if len(nome) < 2:
            raise ValueError("Nome invalido")
        return nome

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: str) -> str:
        email = _normalizar_email(valor)
        return _validar_email_simples(email)

    @model_validator(mode="after")
    def validar_motorista(self):
        if self.cargo == "motorista" and not self.motorista_id:
            raise ValueError("Usuario motorista precisa estar vinculado a um motorista cadastrado")
        return self


class UsuarioSistemaCreate(UsuarioSistemaBase):
    senha: str

    @field_validator("senha")
    @classmethod
    def validar_senha(cls, valor: str) -> str:
        senha = (valor or "").strip()
        if len(senha) < 6:
            raise ValueError("Senha deve ter no minimo 6 caracteres")
        return senha


class UsuarioSistemaUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    cargo: Optional[CargoUsuario] = None
    motorista_id: Optional[int] = None
    ativo: Optional[bool] = None
    nova_senha: Optional[str] = None

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        nome = valor.strip()
        if len(nome) < 2:
            raise ValueError("Nome invalido")
        return nome

    @field_validator("email")
    @classmethod
    def validar_email(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        email = _normalizar_email(valor)
        return _validar_email_simples(email)

    @field_validator("nova_senha")
    @classmethod
    def validar_nova_senha(cls, valor: Optional[str]) -> Optional[str]:
        if valor is None:
            return valor
        senha = valor.strip()
        if not senha:
            return None
        if len(senha) < 6:
            raise ValueError("Senha deve ter no minimo 6 caracteres")
        return senha


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class UsuarioSistemaResponse(BaseModel):
    id: int
    nome: str
    email: str
    cargo: CargoUsuario
    ativo: bool
    motorista_id: Optional[int] = None
    motorista_nome: Optional[str] = None
    avatar_url: Optional[str] = None
    criado_em: datetime
    atualizado_em: datetime


class ChatMensagem(BaseModel):
    papel: Literal["user", "assistant"]
    texto: str

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        texto = (valor or "").strip()
        if not texto:
            raise ValueError("Mensagem vazia")
        if len(texto) > 4000:
            raise ValueError("Mensagem muito longa")
        return texto


class ChatRequest(BaseModel):
    mensagens: list[ChatMensagem]

    @field_validator("mensagens")
    @classmethod
    def validar_mensagens(cls, valor: list) -> list:
        if not valor:
            raise ValueError("Nenhuma mensagem enviada")
        return valor[-20:]
