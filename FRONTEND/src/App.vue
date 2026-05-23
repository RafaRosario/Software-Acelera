<script setup>
import { computed, nextTick, onMounted, ref } from 'vue'
import axios from 'axios'
import logoAcelera from './assets/logoacelera.png'
import iconFretes from './assets/icon-fretes.png'
import iconCriarFrete from './assets/icon-criar-frete.png'
import iconConcluidos from './assets/icon-concluidos.png'
import iconCadastro from './assets/icon-cadastro.png'
import iconMotorista from './assets/icon-motorista.png'
import iconCaminhao from './assets/icon-caminhao.png'

const API_URL = 'http://127.0.0.1:8000'
const tiposVeiculo = ['Motoboy', 'Fiorino', 'Iveco', '3/4', 'Toco', 'Truk', 'Carreta']
const STATUS_AGUARDANDO = 'Aguardando horario'
const STATUS_CAMINHO_P1 = 'A caminho P1'
const STATUS_COLETADO_P1 = 'coletado P1'
const STATUS_CAMINHO_PONTO_ADICIONAL = 'A caminho ponto adicional'
const STATUS_PONTOS_ADICIONAIS = 'Pontos adicionais'
const STATUS_CAMINHO_DESTINO = 'A caminho destino'
const STATUS_CHEGADA_DESTINO = 'Chegada no destino'
const STATUS_RETORNANDO = 'retornando'
const STATUS_CONCLUIDO = 'concluido'
const STATUS_CANCELADA = 'Cancelada'
const statusFiltroFrete = [
  STATUS_AGUARDANDO,
  STATUS_CAMINHO_P1,
  STATUS_COLETADO_P1,
  STATUS_CAMINHO_PONTO_ADICIONAL,
  STATUS_PONTOS_ADICIONAIS,
  STATUS_CAMINHO_DESTINO,
  STATUS_CHEGADA_DESTINO,
  STATUS_RETORNANDO,
  STATUS_CONCLUIDO,
  STATUS_CANCELADA,
]

const carregando = ref(false)
const erro = ref('')
const aba = ref('fretes')
const cadastroAtivo = ref('motoristas')
const motoristaAberto = ref(null)
const motoristas = ref([])
const motoristasAlocacao = ref([])
const veiculos = ref([])
const empresas = ref([])
const fretes = ref([])
const filtroDataInicioFretes = ref(new Date().toISOString().slice(0, 10))
const filtroDataFimFretes = ref(new Date().toISOString().slice(0, 10))
const filtroStatus = ref('Todos')
const filtroClienteFretes = ref('Todos')
const filtroConcluidos = ref('todos')
const filtroClienteConcluidos = ref('Todos')
const dataInicioConcluidos = ref('')
const dataFimConcluidos = ref('')
const buscaOrigemFrete = ref('')
const buscaEmpresaColeta = ref('')
const buscaDestinoFrete = ref('')
const toast = ref(null)
const freteArrastandoId = ref(null)
const statusDestinoAtivo = ref('')
const freteAbertoId = ref(null)
const menuStatusFrete = ref({ aberto: false, x: 0, y: 0, frete: null })
const filtroSituacaoVeiculo = ref('Todos')
const filtroTipoVeiculo = ref('Todos')
const veiculoIndisponibilidadeAberto = ref(null)
const motivoIndisponibilidadeVeiculo = ref('')
const motoristaEditandoId = ref(null)
const veiculoEditandoId = ref(null)
const empresaEditandoId = ref(null)
const freteEditandoId = ref(null)
const abaRetornoEdicaoFrete = ref('fretes')
const sidebarRecolhida = ref(false)
const menuMobileAberto = ref(false)

const novoMotorista = ref({ nome: '', telefone: '', rg: '', cpf: '', cnh: '', observacoes: '' })
const novoVeiculo = ref({ placa: '', tipo: 'Truk', observacoes: '' })
const novaEmpresa = ref({
  nome: '',
  cnpj: '',
  cliente: false,
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  uf: '',
  endereco: '',
  observacoes: '',
})
const criarFormularioFreteVazio = (dataColeta = new Date().toISOString().slice(0, 10)) => ({
  cliente: '',
  nota_fiscal: '',
  data_coleta: dataColeta,
  horario_coleta: '',
  origem: '',
  empresas_coleta: [],
  destino: '',
  tipo_caminhao_necessario: 'Truk',
  retorno: false,
  tipo_frete: 'principal',
  frete_principal_id: null,
  status: 'Aguardando horario',
  valor_servico: null,
  observacoes: '',
  motorista_id: '',
  veiculo_id: '',
})
const novoFrete = ref(criarFormularioFreteVazio())

const paginas = {
  fretes: {
    titulo: 'Fretes',
    resumo: 'Escala operacional em Kanban.',
  },
  concluidos: {
    titulo: 'Concluidos',
    resumo: 'Fechamento financeiro dos servicos finalizados.',
  },
  caminhoes: {
    titulo: 'Caminhoes',
    resumo: 'Disponibilidade da frota na operacao.',
  },
  relatorios: {
    titulo: 'Motoristas',
    resumo: 'Status, escala e historico dos motoristas.',
  },
  'novo-frete': {
    titulo: 'Novo frete',
    resumo: 'Cadastro rapido para a proxima viagem.',
  },
  cadastros: {
    titulo: 'Cadastros',
    resumo: 'Motoristas, caminhoes e empresas.',
  },
}

const paginaAtual = computed(() => {
  if (aba.value === 'novo-frete' && freteEditandoId.value) {
    return {
      titulo: 'Editar frete',
      resumo: 'Atualize os dados operacionais do frete criado.',
    }
  }
  return paginas[aba.value] || paginas.fretes
})

const abrirPagina = (pagina, cadastro = null) => {
  aba.value = pagina
  if (cadastro) cadastroAtivo.value = cadastro
  menuMobileAberto.value = false
}

const carregarTudo = async () => {
  carregando.value = true
  erro.value = ''
  try {
    const [motoristasResp, alocacaoResp, veiculosResp, empresasResp, fretesResp] = await Promise.all([
      axios.get(`${API_URL}/motoristas/`),
      axios.get(`${API_URL}/motoristas/alocacao/`),
      axios.get(`${API_URL}/veiculos/`),
      axios.get(`${API_URL}/empresas/`),
      axios.get(`${API_URL}/fretes/`),
    ])
    motoristas.value = motoristasResp.data
    motoristasAlocacao.value = alocacaoResp.data
    veiculos.value = veiculosResp.data
    empresas.value = empresasResp.data
    fretes.value = fretesResp.data
  } catch (error) {
    erro.value = 'Nao foi possivel conectar na API. Verifique se o backend esta rodando.'
  } finally {
    carregando.value = false
  }
}

function statusEhConcluido(status) {
  return status === STATUS_CONCLUIDO || status === 'Concluida'
}

function statusEhPontoAdicional(status) {
  return status === STATUS_CAMINHO_PONTO_ADICIONAL || status === STATUS_PONTOS_ADICIONAIS || /^coletado P[2-9]\d*$/.test(status || '')
}

function statusConfereFiltroFrete(status, filtro) {
  if (filtro === 'Todos') return true
  if (filtro === STATUS_CONCLUIDO) return statusEhConcluido(status)
  if (filtro === STATUS_PONTOS_ADICIONAIS) return statusEhPontoAdicional(status) && status !== STATUS_CAMINHO_PONTO_ADICIONAL
  return status === filtro
}

function freteEhRetorno(frete) {
  return frete?.tipo_frete === 'retorno'
}

function dataLocal(valor) {
  return new Date(`${valor}T00:00:00`)
}

function dataConferePeriodoFretes(dataFrete) {
  if (!dataFrete) return true
  const data = dataLocal(dataFrete)
  const inicio = filtroDataInicioFretes.value ? dataLocal(filtroDataInicioFretes.value) : null
  const fim = filtroDataFimFretes.value ? dataLocal(filtroDataFimFretes.value) : null

  if (fim) fim.setHours(23, 59, 59, 999)
  return (!inicio || data >= inicio) && (!fim || data <= fim)
}

const fretesFiltrados = computed(() => {
  return fretes.value.filter((frete) => {
    if (freteEhRetorno(frete)) return false
    const dataConfere = dataConferePeriodoFretes(frete.data_coleta)
    const clienteConfere = filtroClienteFretes.value === 'Todos' || frete.cliente === filtroClienteFretes.value
    const statusConfere = statusConfereFiltroFrete(frete.status, filtroStatus.value)
    return dataConfere && clienteConfere && statusConfere
  })
})

const statusVisualFrete = (status) => {
  if (status === 'Aguardando horario') return 'Aguardando horario'
  if (statusEhConcluido(status)) return 'concluido'
  if (status === 'Cancelada') return 'Cancelada'
  return 'Em andamento'
}

const classeStatusVisualFrete = (status) => statusVisualFrete(status).toLowerCase().replaceAll(' ', '-')

const totais = computed(() => ({
  aguardando: fretesPorData.value.filter((frete) => frete.status === 'Aguardando horario').length,
  andamento: fretesPorData.value.filter((frete) => statusVisualFrete(frete.status) === 'Em andamento').length,
  concluidas: fretesPorData.value.filter((frete) => statusEhConcluido(frete.status)).length,
  retorno: fretesPorData.value.filter((frete) => frete.retorno && !freteEhRetorno(frete)).length,
}))

const fretesEmAberto = computed(() => {
  return fretes.value.filter((frete) => !freteEhRetorno(frete) && !statusEhConcluido(frete.status) && frete.status !== STATUS_CANCELADA)
})

const fretesAbertosPorVeiculo = computed(() => {
  return fretesEmAberto.value.reduce((resultado, frete) => {
    if (!frete.veiculo_id) return resultado
    const chave = Number(frete.veiculo_id)
    resultado[chave] = [...(resultado[chave] || []), frete]
    return resultado
  }, {})
})

const fretesAbertosPorMotorista = computed(() => {
  return fretesEmAberto.value.reduce((resultado, frete) => {
    if (!frete.motorista_id) return resultado
    const chave = Number(frete.motorista_id)
    resultado[chave] = [...(resultado[chave] || []), frete]
    return resultado
  }, {})
})

const situacaoVeiculo = (veiculo) => {
  if (!veiculo.ativo) return 'Indisponivel'
  if ((fretesAbertosPorVeiculo.value[veiculo.id] || []).length > 0) return 'Em uso'
  return 'Disponivel'
}

const classeSituacaoVeiculo = (veiculo) => situacaoVeiculo(veiculo).toLowerCase().replaceAll(' ', '-')

const fretesUsoVeiculo = (veiculo) => fretesAbertosPorVeiculo.value[veiculo.id] || []

const situacaoMotorista = (motorista) => {
  if (!motorista.ativo) return 'Indisponivel'
  if ((fretesAbertosPorMotorista.value[motorista.id] || []).length > 0) return 'Em servico'
  return 'Disponivel'
}

const classeSituacaoMotorista = (motorista) => situacaoMotorista(motorista).toLowerCase().replaceAll(' ', '-')

const fretesUsoMotorista = (motorista) => fretesAbertosPorMotorista.value[motorista.id] || []

const veiculosFiltrados = computed(() => {
  return veiculos.value.filter((veiculo) => {
    const situacaoConfere = filtroSituacaoVeiculo.value === 'Todos' || situacaoVeiculo(veiculo) === filtroSituacaoVeiculo.value
    const tipoConfere = filtroTipoVeiculo.value === 'Todos' || veiculo.tipo === filtroTipoVeiculo.value
    return situacaoConfere && tipoConfere
  })
})

const totaisVeiculos = computed(() => ({
  total: veiculos.value.length,
  disponiveis: veiculos.value.filter((veiculo) => situacaoVeiculo(veiculo) === 'Disponivel').length,
  emUso: veiculos.value.filter((veiculo) => situacaoVeiculo(veiculo) === 'Em uso').length,
  indisponiveis: veiculos.value.filter((veiculo) => situacaoVeiculo(veiculo) === 'Indisponivel').length,
}))

const fretesPorData = computed(() => {
  return fretes.value.filter((frete) => {
    if (freteEhRetorno(frete)) return false
    const dataConfere = dataConferePeriodoFretes(frete.data_coleta)
    const clienteConfere = filtroClienteFretes.value === 'Todos' || frete.cliente === filtroClienteFretes.value
    return dataConfere && clienteConfere
  })
})

const empresasColetaDisponiveis = computed(() => {
  const termo = buscaEmpresaColeta.value.trim().toLowerCase()
  return empresas.value
    .filter((empresa) => !novoFrete.value.empresas_coleta.includes(empresa.nome))
    .filter((empresa) => !termo || empresa.nome.toLowerCase().includes(termo))
    .slice(0, 8)
})

const buscarEmpresasPorTermo = (termo, selecionada = '') => {
  const busca = termo.trim().toLowerCase()
  if (!busca) return []

  return empresas.value
    .filter((empresa) => empresa.nome !== selecionada)
    .filter((empresa) => {
      const dados = [empresa.nome, empresa.cnpj, empresa.cidade, empresa.uf, empresa.bairro].filter(Boolean).join(' ').toLowerCase()
      return dados.includes(busca)
    })
    .slice(0, 8)
}

const empresasOrigemDisponiveis = computed(() => buscarEmpresasPorTermo(buscaOrigemFrete.value, novoFrete.value.origem))
const empresasDestinoDisponiveis = computed(() => buscarEmpresasPorTermo(buscaDestinoFrete.value, novoFrete.value.destino))

const fretesConcluidos = computed(() => {
  return fretes.value.filter((frete) => statusEhConcluido(frete.status) && !freteEhRetorno(frete))
})

const fretesConcluidosFiltrados = computed(() => {
  return fretesConcluidos.value.filter((frete) => {
    if (filtroClienteConcluidos.value !== 'Todos' && frete.cliente !== filtroClienteConcluidos.value) return false
    if (filtroConcluidos.value === 'todos') return true

    const hoje = new Date()
    const dataFrete = new Date(`${frete.data_coleta}T00:00:00`)

    if (filtroConcluidos.value === 'hoje') {
      return frete.data_coleta === hoje.toISOString().slice(0, 10)
    }

    if (filtroConcluidos.value === 'semana') {
      const inicioSemana = new Date(hoje)
      inicioSemana.setDate(hoje.getDate() - hoje.getDay())
      inicioSemana.setHours(0, 0, 0, 0)
      const fimSemana = new Date(inicioSemana)
      fimSemana.setDate(inicioSemana.getDate() + 6)
      fimSemana.setHours(23, 59, 59, 999)
      return dataFrete >= inicioSemana && dataFrete <= fimSemana
    }

    if (filtroConcluidos.value === 'mes') {
      const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
      const fimMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0, 23, 59, 59, 999)
      return dataFrete >= inicioMes && dataFrete <= fimMes
    }

    if (filtroConcluidos.value === 'periodo') {
      const inicio = dataInicioConcluidos.value ? new Date(`${dataInicioConcluidos.value}T00:00:00`) : null
      const fim = dataFimConcluidos.value ? new Date(`${dataFimConcluidos.value}T23:59:59`) : null
      return (!inicio || dataFrete >= inicio) && (!fim || dataFrete <= fim)
    }

    return true
  })
})

const totalConcluido = computed(() => {
  return fretesConcluidosFiltrados.value.reduce((total, frete) => {
    return total + Number(frete.valor_servico || 0) + Number(frete.valor_retorno || 0) + Number(frete.valor_ponto_adicional || 0)
  }, 0)
})

const pontosAdicionaisFrete = (frete) => {
  return (frete.empresas_coleta || '')
    .split(',')
    .map((ponto) => ponto.trim())
    .filter(Boolean)
}

const historicoFretesMotorista = (motoristaId) => {
  return fretes.value
    .filter((frete) => Number(frete.motorista_id) === Number(motoristaId))
    .filter((frete) => statusEhConcluido(frete.status))
    .sort((a, b) => {
      const dataA = `${a.data_coleta || ''} ${a.horario_coleta || ''}`
      const dataB = `${b.data_coleta || ''} ${b.horario_coleta || ''}`
      return dataB.localeCompare(dataA)
    })
    .slice(0, 12)
}

const empresasPorNome = computed(() => {
  return Object.fromEntries(empresas.value.map((empresa) => [empresa.nome, empresa]))
})

const empresasClientes = computed(() => {
  return empresas.value.filter((empresa) => empresa.cliente)
})

const nomeMotorista = (id) => motoristas.value.find((motorista) => motorista.id === id)?.nome || 'Sem motorista'
const telefoneMotorista = (id) => motoristas.value.find((motorista) => motorista.id === id)?.telefone || ''
const placaVeiculo = (id) => veiculos.value.find((veiculo) => veiculo.id === id)?.placa || 'Sem caminhao'
const veiculoPorId = (id) => veiculos.value.find((veiculo) => veiculo.id === id)

const pontosColetaFrete = (frete) => {
  return 1 + pontosAdicionaisFrete(frete).length
}

const statusDisponiveisFrete = (frete) => {
  const status = [STATUS_AGUARDANDO, STATUS_CAMINHO_P1, STATUS_COLETADO_P1]

  if (pontosColetaFrete(frete) > 1) {
    status.push(STATUS_CAMINHO_PONTO_ADICIONAL)
    status.push(STATUS_PONTOS_ADICIONAIS)
  }

  status.push(STATUS_CAMINHO_DESTINO)
  status.push(STATUS_CHEGADA_DESTINO)
  if (frete.retorno) status.push(STATUS_RETORNANDO)
  status.push(STATUS_CONCLUIDO)
  status.push(STATUS_CANCELADA)

  if (frete.status && !status.includes(frete.status)) {
    status.unshift(frete.status)
  }

  return status
}

const colunasKanban = computed(() => {
  if (filtroStatus.value !== 'Todos') {
    return [filtroStatus.value]
  }

  const colunas = [STATUS_AGUARDANDO, STATUS_CAMINHO_P1, STATUS_COLETADO_P1]

  if (fretesFiltrados.value.some((frete) => pontosColetaFrete(frete) > 1 || statusEhPontoAdicional(frete.status))) {
    colunas.push(STATUS_CAMINHO_PONTO_ADICIONAL)
    colunas.push(STATUS_PONTOS_ADICIONAIS)
  }

  colunas.push(STATUS_CAMINHO_DESTINO)
  colunas.push(STATUS_CHEGADA_DESTINO)

  if (fretesFiltrados.value.some((frete) => frete.retorno || frete.status === STATUS_RETORNANDO)) {
    colunas.push(STATUS_RETORNANDO)
  }

  colunas.push(STATUS_CONCLUIDO)
  colunas.push(STATUS_CANCELADA)
  return colunas
})

const fretesPorStatusKanban = (status) => {
  return fretesFiltrados.value.filter((frete) => {
    if (status === STATUS_CONCLUIDO) return statusEhConcluido(frete.status)
    if (status === STATUS_PONTOS_ADICIONAIS) return statusEhPontoAdicional(frete.status) && frete.status !== STATUS_CAMINHO_PONTO_ADICIONAL
    return frete.status === status
  })
}

const rotuloStatusFrete = (status) => {
  if (status === STATUS_COLETADO_P1) return 'aguardando coleta P1'
  if (status === STATUS_CAMINHO_DESTINO) return 'coletado P1, a caminho do destino'
  return status
}

const classeStatusKanban = (status) => status.toLowerCase().replaceAll(' ', '-')

const subtituloStatusKanban = (status) => {
  if (status === STATUS_AGUARDANDO) return 'Ainda nao saiu'
  if (status === STATUS_CAMINHO_P1) return 'Indo para a coleta'
  if (status === STATUS_COLETADO_P1) return 'Aguardando confirmacao da coleta'
  if (status === STATUS_CAMINHO_PONTO_ADICIONAL) return 'Indo para parada extra'
  if (status === STATUS_PONTOS_ADICIONAIS) return 'Paradas extras feitas'
  if (status === STATUS_CAMINHO_DESTINO) return 'Coleta feita, indo para entrega'
  if (status === STATUS_CHEGADA_DESTINO) return 'No destino'
  if (status === STATUS_RETORNANDO) return 'Voltando com retorno'
  if (status === STATUS_CONCLUIDO) return 'Finalizado'
  if (status === STATUS_CANCELADA) return 'Fora da escala'
  return 'Em operacao'
}

const alternarFreteAberto = async (id, event) => {
  const vaiAbrir = freteAbertoId.value !== id
  const card = event?.currentTarget
  freteAbertoId.value = vaiAbrir ? id : null

  if (vaiAbrir) {
    await nextTick()
    const acoes = card?.querySelector('.kanban-card-expanded .actions')
    const areaCards = card?.closest('.kanban-cards')
    if (acoes && areaCards) {
      areaCards.scrollTo({
        top: acoes.offsetTop + acoes.offsetHeight - areaCards.clientHeight + 16,
        behavior: 'smooth',
      })
    }
  }
}

const rotaCompactaFrete = (frete) => {
  return pontosMensagemFrete(frete).join(' -> ')
}

const horarioFrete = (frete) => frete.horario_coleta?.slice(0, 5) || '--:--'

const abrirMenuStatusFrete = (event, frete) => {
  const alvo = event?.currentTarget
  const caixa = alvo?.getBoundingClientRect?.()
  const x = event?.clientX ?? (caixa ? caixa.left + caixa.width / 2 : window.innerWidth / 2)
  const y = event?.clientY ?? (caixa ? caixa.top + caixa.height : window.innerHeight / 2)
  menuStatusFrete.value = {
    aberto: true,
    x: Math.min(x, window.innerWidth - 260),
    y: Math.min(y, window.innerHeight - 320),
    frete,
  }
}

const fecharMenuStatusFrete = () => {
  menuStatusFrete.value = { aberto: false, x: 0, y: 0, frete: null }
}

const moverFreteParaStatus = async (frete, status) => {
  if (!frete) return
  if (!statusDisponiveisFrete(frete).includes(status)) {
    mostrarToast('Este status nao existe para este frete.', 'error')
    fecharMenuStatusFrete()
    return
  }
  if (frete.status === status || (status === STATUS_CONCLUIDO && statusEhConcluido(frete.status))) {
    fecharMenuStatusFrete()
    return
  }

  frete.status = status
  fecharMenuStatusFrete()
  await salvarAlocacao(frete)
}

const resumoStatusEdscha = (frete) => {
  if (frete.status === STATUS_AGUARDANDO) return 'aguardando horario'
  if (frete.status === STATUS_CAMINHO_P1) return `a caminho ${frete.origem}`
  if (frete.status === STATUS_COLETADO_P1) return `aguardando coleta ${frete.origem}`
  if (frete.status === STATUS_CAMINHO_PONTO_ADICIONAL) return 'a caminho ponto adicional'
  if (statusEhPontoAdicional(frete.status)) return 'pontos adicionais coletados'
  if (frete.status === STATUS_CAMINHO_DESTINO) return `coletado ${frete.origem}, a caminho do destino`
  if (frete.status === STATUS_CHEGADA_DESTINO) return `chegada no destino ${frete.destino}`
  if (frete.status === STATUS_RETORNANDO) return 'retornando'
  if (statusEhConcluido(frete.status)) return '✅'
  if (frete.status === STATUS_CANCELADA) return 'cancelado'
  return statusVisualFrete(frete.status).toLowerCase()
}

const linhaAtualizacaoEdscha = (frete) => {
  const pontos = pontosMensagemFrete(frete)
  const rota = pontos.join(' x ')
  return `${frete.tipo_caminhao_necessario} - ${rota}, ${resumoStatusEdscha(frete)}`
}

const gerarAtualizacaoEdscha = () => {
  const fretesAtualizacao = fretesFiltrados.value.filter((frete) => frete.status !== 'Cancelada' && !freteEhRetorno(frete))

  if (fretesAtualizacao.length === 0) {
    mostrarToast('Nao ha fretes para atualizar neste filtro.', 'error')
    return ''
  }

  return fretesAtualizacao.map(linhaAtualizacaoEdscha).join('\n\n')
}

const copiarAtualizacaoEdscha = async () => {
  const mensagem = gerarAtualizacaoEdscha()
  if (!mensagem) return
  await navigator.clipboard.writeText(mensagem)
  mostrarToast('Atualizacao Edscha copiada.')
}

const normalizarAlocacao = (frete) => ({
  motorista_id: frete.motorista_id ? Number(frete.motorista_id) : null,
  veiculo_id: frete.veiculo_id ? Number(frete.veiculo_id) : null,
  status: frete.status,
})

const apenasDigitos = (valor) => String(valor || '').replace(/\D/g, '')

const formatarCpf = (valor) => {
  const digitos = apenasDigitos(valor).slice(0, 11)
  return digitos
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2')
}

const limparRg = (valor) => String(valor || '').replace(/[^0-9xX]/g, '').toUpperCase().slice(0, 9)

const formatarRg = (valor) => {
  const limpo = limparRg(valor)
  if (limpo.length <= 2) return limpo
  if (limpo.length <= 5) return limpo.replace(/^(\w{2})(\w+)/, '$1.$2')
  if (limpo.length <= 8) return limpo.replace(/^(\w{2})(\w{3})(\w+)/, '$1.$2.$3')
  return limpo.replace(/^(\w{2})(\w{3})(\w{3})(\w)/, '$1.$2.$3-$4')
}

const cpfValido = (valor) => {
  const cpf = apenasDigitos(valor)
  if (cpf.length !== 11 || /^(\d)\1{10}$/.test(cpf)) return false

  const calcularDigito = (base) => {
    const soma = base.split('').reduce((total, digito, index) => total + Number(digito) * (base.length + 1 - index), 0)
    const resto = soma % 11
    return resto < 2 ? 0 : 11 - resto
  }

  return calcularDigito(cpf.slice(0, 9)) === Number(cpf[9]) && calcularDigito(cpf.slice(0, 10)) === Number(cpf[10])
}

const rgValido = (valor) => {
  const rg = limparRg(valor)
  return rg.length >= 7 && rg.length <= 9
}

const aplicarMascaraCpfMotorista = () => {
  novoMotorista.value.cpf = formatarCpf(novoMotorista.value.cpf)
}

const aplicarMascaraRgMotorista = () => {
  novoMotorista.value.rg = formatarRg(novoMotorista.value.rg)
}

const mostrarToast = (mensagem, tipo = 'success') => {
  toast.value = { mensagem, tipo }
  window.setTimeout(() => {
    if (toast.value?.mensagem === mensagem) {
      toast.value = null
    }
  }, 3500)
}

const salvarComFeedback = async (mensagem, acao) => {
  try {
    await acao()
    mostrarToast(mensagem)
  } catch (error) {
    mostrarToast('Nao foi possivel salvar. Tente novamente.', 'error')
  }
}

const limparMotorista = () => {
  motoristaEditandoId.value = null
  novoMotorista.value = { nome: '', telefone: '', rg: '', cpf: '', cnh: '', observacoes: '' }
}

const limparVeiculo = () => {
  veiculoEditandoId.value = null
  novoVeiculo.value = { placa: '', tipo: 'Truk', observacoes: '' }
}

const limparEmpresa = () => {
  empresaEditandoId.value = null
  novaEmpresa.value = {
    nome: '',
    cnpj: '',
    cliente: false,
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf: '',
    endereco: '',
    observacoes: '',
  }
}

const limparFormularioFrete = () => {
  freteEditandoId.value = null
  novoFrete.value = criarFormularioFreteVazio(filtroDataInicioFretes.value || new Date().toISOString().slice(0, 10))
  buscaOrigemFrete.value = ''
  buscaEmpresaColeta.value = ''
  buscaDestinoFrete.value = ''
}

const abrirNovoFrete = () => {
  abaRetornoEdicaoFrete.value = 'fretes'
  limparFormularioFrete()
  abrirPagina('novo-frete')
}

const cancelarEdicaoFrete = () => {
  const abaRetorno = abaRetornoEdicaoFrete.value
  limparFormularioFrete()
  abrirPagina(abaRetorno)
}

const editarFrete = (frete) => {
  abaRetornoEdicaoFrete.value = aba.value
  freteEditandoId.value = frete.id
  novoFrete.value = {
    cliente: frete.cliente || '',
    nota_fiscal: frete.nota_fiscal || '',
    data_coleta: frete.data_coleta || new Date().toISOString().slice(0, 10),
    horario_coleta: frete.horario_coleta?.slice(0, 5) || '',
    origem: frete.origem || '',
    empresas_coleta: pontosAdicionaisFrete(frete),
    destino: frete.destino || '',
    tipo_caminhao_necessario: frete.tipo_caminhao_necessario || 'Truk',
    retorno: Boolean(frete.retorno),
    tipo_frete: frete.tipo_frete || 'principal',
    frete_principal_id: frete.frete_principal_id || null,
    status: frete.status || STATUS_AGUARDANDO,
    valor_servico: frete.valor_servico ?? null,
    observacoes: frete.observacoes || '',
    motorista_id: frete.motorista_id || '',
    veiculo_id: frete.veiculo_id || '',
  }
  buscaOrigemFrete.value = ''
  buscaEmpresaColeta.value = ''
  buscaDestinoFrete.value = ''
  freteAbertoId.value = null
  fecharMenuStatusFrete()
  abrirPagina('novo-frete')
}

const editarMotorista = (motorista) => {
  motoristaEditandoId.value = motorista.id
  novoMotorista.value = {
    nome: motorista.nome || '',
    telefone: motorista.telefone || '',
    rg: motorista.rg || '',
    cpf: motorista.cpf || '',
    cnh: motorista.cnh || '',
    observacoes: motorista.observacoes || '',
  }
}

const editarVeiculo = (veiculo) => {
  veiculoEditandoId.value = veiculo.id
  novoVeiculo.value = {
    placa: veiculo.placa || '',
    tipo: veiculo.tipo || 'Truk',
    observacoes: veiculo.observacoes || '',
  }
}

const editarEmpresa = (empresa) => {
  empresaEditandoId.value = empresa.id
  novaEmpresa.value = {
    nome: empresa.nome || '',
    cnpj: empresa.cnpj || '',
    cliente: Boolean(empresa.cliente),
    cep: empresa.cep || '',
    logradouro: empresa.logradouro || '',
    numero: empresa.numero || '',
    complemento: empresa.complemento || '',
    bairro: empresa.bairro || '',
    cidade: empresa.cidade || '',
    uf: empresa.uf || '',
    endereco: empresa.endereco || '',
    observacoes: empresa.observacoes || '',
  }
}

const cadastrarMotorista = async () => {
  aplicarMascaraRgMotorista()
  aplicarMascaraCpfMotorista()

  if (!rgValido(novoMotorista.value.rg)) {
    mostrarToast('RG invalido. Confira o numero informado.', 'error')
    return
  }

  if (!cpfValido(novoMotorista.value.cpf)) {
    mostrarToast('CPF invalido. Confira os digitos.', 'error')
    return
  }

  if (motoristaEditandoId.value) {
    await axios.put(`${API_URL}/motoristas/${motoristaEditandoId.value}`, novoMotorista.value)
    limparMotorista()
    await carregarTudo()
    return
  }

  await axios.post(`${API_URL}/motoristas/`, novoMotorista.value)
  limparMotorista()
  await carregarTudo()
}

const cadastrarVeiculo = async () => {
  if (veiculoEditandoId.value) {
    await axios.put(`${API_URL}/veiculos/${veiculoEditandoId.value}`, novoVeiculo.value)
    limparVeiculo()
    await carregarTudo()
    return
  }

  await axios.post(`${API_URL}/veiculos/`, novoVeiculo.value)
  limparVeiculo()
  await carregarTudo()
}

const cadastrarEmpresa = async () => {
  if (empresaEditandoId.value) {
    await axios.put(`${API_URL}/empresas/${empresaEditandoId.value}`, novaEmpresa.value)
    limparEmpresa()
    await carregarTudo()
    return
  }

  await axios.post(`${API_URL}/empresas/`, novaEmpresa.value)
  limparEmpresa()
  await carregarTudo()
}

const buscarCepEmpresa = async () => {
  const cep = novaEmpresa.value.cep.replace(/\D/g, '')
  if (cep.length !== 8) {
    erro.value = 'Informe um CEP com 8 digitos.'
    return
  }

  erro.value = ''
  const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`)
  const dados = await response.json()

  if (dados.erro) {
    erro.value = 'CEP nao encontrado.'
    return
  }

  novaEmpresa.value.cep = dados.cep || novaEmpresa.value.cep
  novaEmpresa.value.logradouro = dados.logradouro || ''
  novaEmpresa.value.complemento = dados.complemento || ''
  novaEmpresa.value.bairro = dados.bairro || ''
  novaEmpresa.value.cidade = dados.localidade || ''
  novaEmpresa.value.uf = dados.uf || ''
}

const payloadFormularioFrete = () => ({
  cliente: novoFrete.value.cliente,
  nota_fiscal: novoFrete.value.nota_fiscal || null,
  data_coleta: novoFrete.value.data_coleta,
  horario_coleta: novoFrete.value.horario_coleta,
  origem: novoFrete.value.origem,
  destino: novoFrete.value.destino,
  tipo_caminhao_necessario: novoFrete.value.tipo_caminhao_necessario,
  retorno: Boolean(novoFrete.value.retorno),
  observacoes: novoFrete.value.observacoes || null,
  empresas_coleta: Array.isArray(novoFrete.value.empresas_coleta)
    ? novoFrete.value.empresas_coleta.join(', ')
    : novoFrete.value.empresas_coleta,
  motorista_id: novoFrete.value.motorista_id ? Number(novoFrete.value.motorista_id) : null,
  veiculo_id: novoFrete.value.veiculo_id ? Number(novoFrete.value.veiculo_id) : null,
  valor_servico:
    novoFrete.value.valor_servico === '' || novoFrete.value.valor_servico === null
      ? null
      : Number(novoFrete.value.valor_servico),
})

const cadastrarFrete = async () => {
  const payload = payloadFormularioFrete()

  if (freteEditandoId.value) {
    const abaRetorno = abaRetornoEdicaoFrete.value
    await salvarComFeedback('Frete atualizado com sucesso.', async () => {
      await axios.put(`${API_URL}/fretes/${freteEditandoId.value}`, payload)
      limparFormularioFrete()
      abrirPagina(abaRetorno)
      await carregarTudo()
    })
    return
  }

  await axios.post(`${API_URL}/fretes/`, payload)
  limparFormularioFrete()
  aba.value = 'fretes'
  await carregarTudo()
}

const adicionarEmpresaColeta = (empresa) => {
  if (!novoFrete.value.empresas_coleta.includes(empresa.nome)) {
    novoFrete.value.empresas_coleta.push(empresa.nome)
  }
  buscaEmpresaColeta.value = ''
}

const selecionarOrigemFrete = (empresa) => {
  novoFrete.value.origem = empresa.nome
  buscaOrigemFrete.value = ''
}

const selecionarDestinoFrete = (empresa) => {
  novoFrete.value.destino = empresa.nome
  buscaDestinoFrete.value = ''
}

const limparOrigemFrete = () => {
  novoFrete.value.origem = ''
  buscaOrigemFrete.value = ''
}

const limparDestinoFrete = () => {
  novoFrete.value.destino = ''
  buscaDestinoFrete.value = ''
}

const removerEmpresaColeta = (nome) => {
  novoFrete.value.empresas_coleta = novoFrete.value.empresas_coleta.filter((empresa) => empresa !== nome)
}

const salvarAlocacao = async (frete) => {
  await salvarComFeedback('Escala salva com sucesso.', async () => {
    await axios.put(`${API_URL}/fretes/${frete.id}/alocar`, normalizarAlocacao(frete))
    await carregarTudo()
  })
}

const salvarEscalaAutomaticamente = async (frete) => {
  await salvarAlocacao(frete)
}

const iniciarArrastoFrete = (event, frete) => {
  freteArrastandoId.value = frete.id
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', String(frete.id))
}

const encerrarArrastoFrete = () => {
  freteArrastandoId.value = null
  statusDestinoAtivo.value = ''
}

const soltarFreteEmStatus = async (event, status) => {
  const freteId = Number(event.dataTransfer.getData('text/plain'))
  const frete = fretes.value.find((item) => item.id === freteId)
  statusDestinoAtivo.value = ''
  if (!frete) {
    encerrarArrastoFrete()
    return
  }

  if (!statusDisponiveisFrete(frete).includes(status)) {
    mostrarToast('Este status nao existe para este frete.', 'error')
    encerrarArrastoFrete()
    return
  }

  if (frete.status === status || (status === 'concluido' && statusEhConcluido(frete.status))) {
    encerrarArrastoFrete()
    return
  }

  frete.status = status
  await salvarAlocacao(frete)
  encerrarArrastoFrete()
}

const valorFretePayload = (frete) => ({
  valor_servico: frete.valor_servico === '' || frete.valor_servico === null ? null : Number(frete.valor_servico),
  valor_retorno: frete.valor_retorno === '' || frete.valor_retorno === null ? null : Number(frete.valor_retorno),
  valor_ponto_adicional:
    frete.valor_ponto_adicional === '' || frete.valor_ponto_adicional === null ? null : Number(frete.valor_ponto_adicional),
})

const salvarValorFrete = async (frete) => {
  await salvarComFeedback('Valor salvo com sucesso.', async () => {
    await axios.put(`${API_URL}/fretes/${frete.id}/valor`, valorFretePayload(frete))
    await carregarTudo()
  })
}

const salvarValoresConcluidosFiltrados = async () => {
  const fretesComValor = fretesConcluidosFiltrados.value.filter((frete) => {
    const temValorServico = frete.valor_servico !== '' && frete.valor_servico !== null
    const temValorRetorno = frete.valor_retorno !== '' && frete.valor_retorno !== null
    const temValorPontoAdicional = frete.valor_ponto_adicional !== '' && frete.valor_ponto_adicional !== null
    return temValorServico || temValorRetorno || temValorPontoAdicional
  })

  if (fretesComValor.length === 0) {
    mostrarToast('Preencha pelo menos um valor antes de salvar.', 'error')
    return
  }

  await salvarComFeedback(`${fretesComValor.length} valores salvos com sucesso.`, async () => {
    await Promise.all(
      fretesComValor.map((frete) =>
        axios.put(`${API_URL}/fretes/${frete.id}/valor`, valorFretePayload(frete)),
      ),
    )
    await carregarTudo()
  })
}

const salvarDocumentosFrete = async (frete) => {
  await salvarComFeedback('OC salva com sucesso.', async () => {
    await axios.put(`${API_URL}/fretes/${frete.id}/documentos`, {
      cte: frete.cte || null,
      oc: frete.oc || null,
    })
    await carregarTudo()
  })
}

const salvarNotaFiscalFrete = async (frete) => {
  await salvarComFeedback('Nota fiscal salva com sucesso.', async () => {
    await axios.put(`${API_URL}/fretes/${frete.id}/nota-fiscal`, {
      nota_fiscal: frete.nota_fiscal || null,
    })
    await carregarTudo()
  })
}

const valorPreenchido = (valor) => valor !== '' && valor !== null && valor !== undefined
const textoPreenchido = (valor) => String(valor || '').trim().length > 0

const salvarValorPreenchidoFrete = async (frete, campo) => {
  if (!valorPreenchido(frete[campo])) return
  await salvarValorFrete(frete)
}

const salvarDocumentoPreenchidoFrete = async (frete, campo) => {
  if (!textoPreenchido(frete[campo])) return
  if (campo === 'nota_fiscal') {
    await salvarNotaFiscalFrete(frete)
    return
  }
  await salvarDocumentosFrete(frete)
}

const salvarFechamentoFrete = async (frete) => {
  await salvarComFeedback('Fechamento salvo com sucesso.', async () => {
    await Promise.all([
      axios.put(`${API_URL}/fretes/${frete.id}/valor`, valorFretePayload(frete)),
      axios.put(`${API_URL}/fretes/${frete.id}/documentos`, {
        cte: frete.cte || null,
        oc: frete.oc || null,
      }),
      axios.put(`${API_URL}/fretes/${frete.id}/nota-fiscal`, {
        nota_fiscal: frete.nota_fiscal || null,
      }),
    ])
    await carregarTudo()
  })
}

const excluirFrete = async (id) => {
  await axios.delete(`${API_URL}/fretes/${id}`)
  await carregarTudo()
}

const excluirMotorista = async (id) => {
  await axios.delete(`${API_URL}/motoristas/${id}`)
  await carregarTudo()
}

const excluirVeiculo = async (id) => {
  await axios.delete(`${API_URL}/veiculos/${id}`)
  await carregarTudo()
}

const abrirIndisponibilidadeVeiculo = (veiculo) => {
  veiculoIndisponibilidadeAberto.value = veiculo
  motivoIndisponibilidadeVeiculo.value = veiculo.motivo_indisponibilidade || ''
}

const fecharIndisponibilidadeVeiculo = () => {
  veiculoIndisponibilidadeAberto.value = null
  motivoIndisponibilidadeVeiculo.value = ''
}

const confirmarIndisponibilidadeVeiculo = async () => {
  if (!veiculoIndisponibilidadeAberto.value) return
  const motivo = motivoIndisponibilidadeVeiculo.value.trim()
  if (!motivo) {
    mostrarToast('Informe o motivo da indisponibilidade.', 'error')
    return
  }

  await salvarComFeedback('Caminhao marcado como indisponivel.', async () => {
    await axios.put(`${API_URL}/veiculos/${veiculoIndisponibilidadeAberto.value.id}`, {
      ativo: false,
      motivo_indisponibilidade: motivo,
    })
    fecharIndisponibilidadeVeiculo()
    await carregarTudo()
  })
}

const liberarVeiculo = async (veiculo) => {
  await salvarComFeedback('Caminhao liberado para uso.', async () => {
    await axios.put(`${API_URL}/veiculos/${veiculo.id}`, {
      ativo: true,
      motivo_indisponibilidade: '',
    })
    await carregarTudo()
  })
}

const excluirEmpresa = async (id) => {
  await axios.delete(`${API_URL}/empresas/${id}`)
  await carregarTudo()
}

const mensagemWhatsApp = (frete) => {
  const veiculo = veiculoPorId(frete.veiculo_id)
  const pontos = pontosMensagemFrete(frete)
  const origem = pontos[0]
  const destino = pontos[pontos.length - 1]
  const pontosAdicionais = pontos.slice(1, -1)
  const blocosPontos = [
    `Origem : ${origem}\n${enderecoPorNomeEmpresa(origem)}`,
    ...pontosAdicionais.map((ponto, index) => `Ponto adicional ${index + 1} : ${ponto}\n${enderecoPorNomeEmpresa(ponto)}`),
    `Destino\n${destino}\n${enderecoPorNomeEmpresa(destino)}`,
  ]

  return [
    `${veiculo?.tipo || frete.tipo_caminhao_necessario} - ${veiculo?.placa || placaVeiculo(frete.veiculo_id)}`,
    '',
    '',
    '',
    `Coleta *${frete.horario_coleta.slice(0, 5)}*`,
    '',
    blocosPontos.join('\n\n'),
    frete.retorno ? '\n\nretorno: *SIM*' : '',
  ]
    .filter(Boolean)
    .join('\n')
}

const abrirWhatsApp = (frete) => {
  const telefone = telefoneMotorista(frete.motorista_id).replace(/\D/g, '')
  const texto = encodeURIComponent(mensagemWhatsApp(frete))
  const destino = telefone ? `55${telefone}` : ''
  window.open(`https://wa.me/${destino}?text=${texto}`, '_blank')
}

const copiarMensagem = async (frete) => {
  await navigator.clipboard.writeText(mensagemWhatsApp(frete))
}

const formatarData = (data) => {
  if (!data) return ''
  return new Date(`${data}T00:00:00`).toLocaleDateString('pt-BR')
}

const formatarMoeda = (valor) => {
  return Number(valor || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

const periodoExportacaoConcluidos = () => {
  const params = new URLSearchParams()
  const hoje = new Date()

  if (filtroConcluidos.value === 'hoje') {
    params.set('inicio', hoje.toISOString().slice(0, 10))
    params.set('fim', hoje.toISOString().slice(0, 10))
  }

  if (filtroConcluidos.value === 'semana') {
    const inicioSemana = new Date(hoje)
    inicioSemana.setDate(hoje.getDate() - hoje.getDay())
    const fimSemana = new Date(inicioSemana)
    fimSemana.setDate(inicioSemana.getDate() + 6)
    params.set('inicio', inicioSemana.toISOString().slice(0, 10))
    params.set('fim', fimSemana.toISOString().slice(0, 10))
  }

  if (filtroConcluidos.value === 'mes') {
    const inicioMes = new Date(hoje.getFullYear(), hoje.getMonth(), 1)
    const fimMes = new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0)
    params.set('inicio', inicioMes.toISOString().slice(0, 10))
    params.set('fim', fimMes.toISOString().slice(0, 10))
  }

  if (filtroConcluidos.value === 'periodo') {
    if (dataInicioConcluidos.value) params.set('inicio', dataInicioConcluidos.value)
    if (dataFimConcluidos.value) params.set('fim', dataFimConcluidos.value)
  }

  if (filtroClienteConcluidos.value !== 'Todos') {
    params.set('cliente', filtroClienteConcluidos.value)
  }

  return params.toString()
}

const exportarConcluidos = () => {
  const query = periodoExportacaoConcluidos()
  const url = `${API_URL}/fretes/concluidos/exportar${query ? `?${query}` : ''}`
  window.open(url, '_blank')
}

const exportarHistoricoMotoristas = () => {
  const url = `${API_URL}/motoristas/historico/exportar`
  window.open(url, '_blank')
}

const excluirConcluidosFiltrados = async () => {
  const total = fretesConcluidosFiltrados.value.length
  if (total === 0) {
    mostrarToast('Nao ha fretes concluidos neste filtro.', 'error')
    return
  }

  const confirmou = window.confirm(`Voce deseja excluir todos os ${total} fretes concluidos deste filtro?`)
  if (!confirmou) return

  await salvarComFeedback('Fretes concluidos excluidos com sucesso.', async () => {
    const query = periodoExportacaoConcluidos()
    await axios.delete(`${API_URL}/fretes/concluidos${query ? `?${query}` : ''}`)
    await carregarTudo()
  })
}

const enderecoEmpresa = (empresa) => {
  return empresa.endereco || [empresa.logradouro, empresa.numero, empresa.bairro, empresa.cidade, empresa.uf]
    .filter(Boolean)
    .join(', ')
}

const empresaPorNome = (nome) => empresasPorNome.value[nome]

const enderecoPorNomeEmpresa = (nome) => {
  const empresa = empresaPorNome(nome)
  return empresa ? enderecoEmpresa(empresa) : 'Endereco nao cadastrado'
}

const pontosMensagemFrete = (frete) => {
  const adicionais = (frete.empresas_coleta || '')
    .split(',')
    .map((ponto) => ponto.trim())
    .filter(Boolean)

  return [frete.origem, ...adicionais, frete.destino].filter(Boolean)
}

onMounted(carregarTudo)
</script>

<template>
  <main class="app-shell" :class="{ 'sidebar-collapsed': sidebarRecolhida }">
    <div v-if="toast" class="toast" :class="toast.tipo">
      {{ toast.mensagem }}
    </div>

    <aside class="app-sidebar" :class="{ collapsed: sidebarRecolhida, open: menuMobileAberto }">
      <div class="sidebar-brand">
        <img :src="logoAcelera" alt="Acelera Transportes" />
        <div class="sidebar-brand-copy">
          <p>Acelera</p>
          <strong>Transportes</strong>
        </div>
        <button
          class="icon-button sidebar-mobile-close"
          type="button"
          title="Fechar menu"
          aria-label="Fechar menu"
          @click="menuMobileAberto = false"
        >
          x
        </button>
      </div>

      <nav class="sidebar-nav" aria-label="Navegacao principal">
        <button title="Fretes" :class="{ active: aba === 'fretes' }" type="button" @click="abrirPagina('fretes')">
          <span class="nav-icon"><img :src="iconFretes" alt="" /></span>
          <span><strong>Fretes</strong><small>FRETES</small></span>
        </button>
        <button title="Concluidos" :class="{ active: aba === 'concluidos' }" type="button" @click="abrirPagina('concluidos')">
          <span class="nav-icon"><img :src="iconConcluidos" alt="" /></span>
          <span><strong>Concluidos</strong><small>CONCLUIDOS</small></span>
        </button>
        <button title="Caminhoes" :class="{ active: aba === 'caminhoes' }" type="button" @click="abrirPagina('caminhoes')">
          <span class="nav-icon"><img :src="iconCaminhao" alt="" /></span>
          <span><strong>Caminhoes</strong><small>CAMINHAO</small></span>
        </button>
        <button title="Motoristas" :class="{ active: aba === 'relatorios' }" type="button" @click="abrirPagina('relatorios')">
          <span class="nav-icon"><img :src="iconMotorista" alt="" /></span>
          <span><strong>Motoristas</strong><small>MOTORISTA</small></span>
        </button>
        <button title="Novo frete" :class="{ active: aba === 'novo-frete' }" type="button" @click="abrirNovoFrete">
          <span class="nav-icon"><img :src="iconCriarFrete" alt="" /></span>
          <span><strong>Novo frete</strong><small>CRIAR FRETE</small></span>
        </button>
        <button title="Cadastros" :class="{ active: aba === 'cadastros' }" type="button" @click="abrirPagina('cadastros', 'motoristas')">
          <span class="nav-icon"><img :src="iconCadastro" alt="" /></span>
          <span><strong>Cadastros</strong><small>CADASTRO</small></span>
        </button>
      </nav>

      <button
        class="sidebar-collapse"
        type="button"
        :title="sidebarRecolhida ? 'Expandir menu' : 'Recolher menu'"
        :aria-label="sidebarRecolhida ? 'Expandir menu' : 'Recolher menu'"
        @click="sidebarRecolhida = !sidebarRecolhida"
      >
        <span aria-hidden="true">{{ sidebarRecolhida ? '>' : '<' }}</span>
        <strong>{{ sidebarRecolhida ? 'Expandir' : 'Recolher' }}</strong>
      </button>
    </aside>

    <button v-if="menuMobileAberto" class="sidebar-scrim" type="button" aria-label="Fechar menu" @click="menuMobileAberto = false"></button>

    <div class="content-shell">
      <header class="topbar">
        <button class="mobile-menu-button" type="button" @click="menuMobileAberto = true">
          <span aria-hidden="true"></span>
          Menu
        </button>
        <div>
          <p class="eyebrow">{{ paginaAtual.resumo }}</p>
          <h1>{{ paginaAtual.titulo }}</h1>
        </div>
        <button class="ghost-button refresh-button" type="button" @click="carregarTudo">
          Atualizar
        </button>
      </header>

      <section v-if="erro" class="alert">{{ erro }}</section>

    <div v-if="false" class="nav-groups">
      <nav class="tabs" aria-label="Visualizacao e operacao">
        <button :class="{ active: aba === 'fretes' }" type="button" @click="aba = 'fretes'">Fretes</button>
        <button :class="{ active: aba === 'concluidos' }" type="button" @click="aba = 'concluidos'">Concluidos</button>
        <button :class="{ active: aba === 'caminhoes' }" type="button" @click="aba = 'caminhoes'">Caminhões</button>
        <button :class="{ active: aba === 'relatorios' }" type="button" @click="aba = 'relatorios'">Motoristas</button>
      </nav>

      <nav class="tabs create-tabs" aria-label="Criacao e cadastros">
        <button :class="{ active: aba === 'novo-frete' }" type="button" @click="aba = 'novo-frete'">Novo frete</button>
        <button :class="{ active: aba === 'cadastros' }" type="button" @click="aba = 'cadastros'; cadastroAtivo = 'motoristas'">Cadastros</button>
      </nav>
    </div>

    <section v-if="aba === 'fretes'" class="workspace">
      <div class="section-head freight-toolbar">
        <div>
          <h2>Escala diaria</h2>
          <p>Fretes cadastrados, alocacao e status da viagem.</p>
        </div>
        <div class="freight-toolbar-controls">
          <button class="update-button" type="button" @click="copiarAtualizacaoEdscha">
            Copiar atualizacao Edscha
          </button>
          <div class="freight-filters">
            <label class="field compact">
              Data inicio
              <input v-model="filtroDataInicioFretes" type="date" />
            </label>
            <label class="field compact">
              Data fim
              <input v-model="filtroDataFimFretes" type="date" />
            </label>
            <label class="field compact">
              Cliente
              <select v-model="filtroClienteFretes">
                <option value="Todos">Todos</option>
                <option v-for="empresa in empresasClientes" :key="empresa.id" :value="empresa.nome">{{ empresa.nome }}</option>
              </select>
            </label>
            <label class="field compact">
              Status
              <select v-model="filtroStatus">
                <option value="Todos">Todos</option>
                <option v-for="status in statusFiltroFrete" :key="status" :value="status">{{ rotuloStatusFrete(status) }}</option>
              </select>
            </label>
          </div>
        </div>
      </div>

      <div class="metrics">
        <div><strong>{{ totais.aguardando }}</strong><span>Aguardando horário</span></div>
        <div><strong>{{ totais.andamento }}</strong><span>Em andamento</span></div>
        <div><strong>{{ totais.concluidas }}</strong><span>Concluidas</span></div>
        <div><strong>{{ totais.retorno }}</strong><span>Com retorno</span></div>
      </div>

      <div class="kanban-board">
        <section
          v-for="status in colunasKanban"
          :key="status"
          class="kanban-column"
          :class="[classeStatusKanban(status), { 'drop-active': statusDestinoAtivo === status }]"
          @dragover.prevent
          @dragenter.prevent="statusDestinoAtivo = status"
          @drop="soltarFreteEmStatus($event, status)"
        >
          <header class="kanban-column-head">
            <div>
              <h3>{{ rotuloStatusFrete(status) }}</h3>
              <p>{{ subtituloStatusKanban(status) }}</p>
            </div>
            <span>{{ fretesPorStatusKanban(status).length }}</span>
          </header>

          <div class="kanban-cards">
            <article
              v-for="frete in fretesPorStatusKanban(status)"
              :key="frete.id"
              class="freight-card kanban-card"
              :class="{ dragging: freteArrastandoId === frete.id, expanded: freteAbertoId === frete.id }"
              draggable="true"
              role="button"
              tabindex="0"
              @dragstart="iniciarArrastoFrete($event, frete)"
              @dragend="encerrarArrastoFrete"
              @click="alternarFreteAberto(frete.id, $event)"
              @contextmenu.prevent.stop="abrirMenuStatusFrete($event, frete)"
              @keydown.enter.prevent="alternarFreteAberto(frete.id, $event)"
              @keydown.space.prevent="alternarFreteAberto(frete.id, $event)"
            >
              <div class="kanban-card-summary">
                <div class="kanban-time-block">
                  <span class="time">{{ horarioFrete(frete) }}</span>
                  <span class="badge" :class="classeStatusVisualFrete(frete.status)">{{ statusVisualFrete(frete.status) }}</span>
                </div>

                <p class="kanban-route">{{ rotaCompactaFrete(frete) }}</p>

                <div class="kanban-mini-details">
                  <span>{{ frete.tipo_caminhao_necessario }}</span>
                  <span>{{ placaVeiculo(frete.veiculo_id) }}</span>
                  <span v-if="frete.retorno">Gera retorno</span>
                  <span>{{ freteAbertoId === frete.id ? 'Fechar' : 'Detalhes' }}</span>
                </div>
              </div>

              <div v-if="freteAbertoId === frete.id" class="kanban-card-expanded" @click.stop>
                <div class="freight-details">
                  <span>{{ nomeMotorista(frete.motorista_id) }}</span>
                  <span>Valor: {{ formatarMoeda(frete.valor_servico) }}</span>
                  <span>NF: {{ frete.nota_fiscal || 'Sem nota' }}</span>
                </div>

                <div v-if="frete.observacoes" class="note">{{ frete.observacoes }}</div>

                <div class="allocation-grid">
                  <label class="field">
                    Motorista
                    <select v-model="frete.motorista_id" @change="salvarEscalaAutomaticamente(frete)">
                      <option :value="null">Selecionar</option>
                      <option v-for="motorista in motoristas" :key="motorista.id" :value="motorista.id">{{ motorista.nome }}</option>
                    </select>
                  </label>
                  <label class="field">
                    Caminhão
                    <select v-model="frete.veiculo_id" @change="salvarEscalaAutomaticamente(frete)">
                      <option :value="null">Selecionar</option>
                      <option v-for="veiculo in veiculos" :key="veiculo.id" :value="veiculo.id">{{ veiculo.placa }} - {{ veiculo.tipo }}</option>
                    </select>
                  </label>
                  <label class="field">
                    Valor do servico
                    <input v-model="frete.valor_servico" type="number" min="0" step="0.01" placeholder="Opcional" />
                  </label>
                  <label class="field">
                    Nota fiscal
                    <input v-model="frete.nota_fiscal" placeholder="Opcional" />
                  </label>
                </div>

                <div class="actions">
                  <button class="secondary status-move-button" type="button" @click="abrirMenuStatusFrete($event, frete)">Mover status</button>
                  <button class="secondary" type="button" @click="salvarValorFrete(frete)">Salvar valor</button>
                  <button class="secondary" type="button" @click="salvarNotaFiscalFrete(frete)">Salvar NF</button>
                  <button class="secondary" type="button" @click="editarFrete(frete)">Editar frete</button>
                  <button class="secondary" type="button" @click="copiarMensagem(frete)">Copiar mensagem</button>
                  <button class="secondary" type="button" @click="abrirWhatsApp(frete)">WhatsApp</button>
                  <button class="danger" type="button" @click="excluirFrete(frete.id)">Excluir</button>
                </div>
              </div>
            </article>

            <p v-if="fretesPorStatusKanban(status).length === 0" class="kanban-empty">Solte fretes aqui</p>
          </div>
        </section>

        <p v-if="!carregando && fretesFiltrados.length === 0" class="empty">Nenhum frete cadastrado para esta data.</p>
      </div>

      <div v-if="menuStatusFrete.aberto" class="kanban-context-backdrop" @click="fecharMenuStatusFrete" @contextmenu.prevent="fecharMenuStatusFrete">
        <div
          class="kanban-context-menu"
          :style="{ left: `${menuStatusFrete.x}px`, top: `${menuStatusFrete.y}px` }"
          @click.stop
        >
          <div class="kanban-context-head">
            <strong>Mover para</strong>
            <span>{{ menuStatusFrete.frete?.origem }} -> {{ menuStatusFrete.frete?.destino }}</span>
          </div>
          <button
            v-for="status in statusDisponiveisFrete(menuStatusFrete.frete)"
            :key="status"
            type="button"
            :class="{ active: menuStatusFrete.frete?.status === status || (status === STATUS_CONCLUIDO && statusEhConcluido(menuStatusFrete.frete?.status)) }"
            @click="moverFreteParaStatus(menuStatusFrete.frete, status)"
          >
            {{ rotuloStatusFrete(status) }}
          </button>
        </div>
      </div>

      <div v-if="false" class="freight-list">
        <article v-for="frete in fretesFiltrados" :key="frete.id" class="freight-card">
          <div class="freight-main">
            <div>
              <p class="time">{{ frete.horario_coleta.slice(0, 5) }}</p>
              <h3>{{ frete.origem }} → {{ frete.destino }}</h3>
              <p class="muted">{{ frete.empresas_coleta || 'Sem pontos intermediarios' }}</p>
            </div>
            <span class="badge" :class="classeStatusVisualFrete(frete.status)">{{ statusVisualFrete(frete.status) }}</span>
          </div>

          <div class="freight-details">
            <span>{{ frete.tipo_caminhao_necessario }}</span>
            <span>Retorno: {{ frete.retorno ? 'Sim' : 'Nao' }}</span>
            <span>{{ nomeMotorista(frete.motorista_id) }}</span>
            <span>{{ placaVeiculo(frete.veiculo_id) }}</span>
            <span>Valor: {{ formatarMoeda(frete.valor_servico) }}</span>
            <span>NF: {{ frete.nota_fiscal || 'Sem nota' }}</span>
          </div>

          <div v-if="frete.observacoes" class="note">{{ frete.observacoes }}</div>

          <div class="allocation-grid">
            <label class="field">
              Motorista
              <select v-model="frete.motorista_id" @change="salvarEscalaAutomaticamente(frete)">
                <option :value="null">Selecionar</option>
                <option v-for="motorista in motoristas" :key="motorista.id" :value="motorista.id">{{ motorista.nome }}</option>
              </select>
            </label>
            <label class="field">
              Caminhao
              <select v-model="frete.veiculo_id" @change="salvarEscalaAutomaticamente(frete)">
                <option :value="null">Selecionar</option>
                <option v-for="veiculo in veiculos" :key="veiculo.id" :value="veiculo.id">{{ veiculo.placa }} - {{ veiculo.tipo }}</option>
              </select>
            </label>
            <label class="field">
              Status
              <select v-model="frete.status" @change="salvarEscalaAutomaticamente(frete)">
                <option v-for="status in statusDisponiveisFrete(frete)" :key="status" :value="status">{{ status }}</option>
              </select>
            </label>
            <label class="field">
              Valor do servico
              <input v-model="frete.valor_servico" type="number" min="0" step="0.01" placeholder="Opcional" />
            </label>
            <label class="field">
              Nota fiscal
              <input v-model="frete.nota_fiscal" placeholder="Opcional" />
            </label>
          </div>

          <div class="actions">
            <button class="secondary" type="button" @click="salvarValorFrete(frete)">Salvar valor</button>
            <button class="secondary" type="button" @click="salvarNotaFiscalFrete(frete)">Salvar NF</button>
            <button class="secondary" type="button" @click="copiarMensagem(frete)">Copiar mensagem</button>
            <button class="secondary" type="button" @click="abrirWhatsApp(frete)">WhatsApp</button>
            <button class="danger" type="button" @click="excluirFrete(frete.id)">Excluir</button>
          </div>
        </article>

        <p v-if="!carregando && fretesFiltrados.length === 0" class="empty">Nenhum frete cadastrado para esta data.</p>
      </div>
    </section>

    <section v-if="aba === 'concluidos'" class="workspace">
      <div class="section-head">
        <div>
          <h2>Fretes concluidos</h2>
          <p>Fechamento financeiro dos servicos já realizados.</p>
        </div>
      </div>

      <div class="period-filter">
        <label class="field">
          Periodo
          <select v-model="filtroConcluidos">
            <option value="todos">Todos</option>
            <option value="hoje">Hoje</option>
            <option value="semana">Esta semana</option>
            <option value="mes">Este mes</option>
            <option value="periodo">Periodo personalizado</option>
          </select>
        </label>
        <label class="field">
          Cliente
          <select v-model="filtroClienteConcluidos">
            <option value="Todos">Todos</option>
            <option v-for="empresa in empresasClientes" :key="empresa.id" :value="empresa.nome">{{ empresa.nome }}</option>
          </select>
        </label>
        <label class="field" :class="{ disabled: filtroConcluidos !== 'periodo' }">
          Inicio
          <input v-model="dataInicioConcluidos" type="date" :disabled="filtroConcluidos !== 'periodo'" />
        </label>
        <label class="field" :class="{ disabled: filtroConcluidos !== 'periodo' }">
          Fim
          <input v-model="dataFimConcluidos" type="date" :disabled="filtroConcluidos !== 'periodo'" />
        </label>
        <button type="button" @click="exportarConcluidos">Exportar Excel</button>
        <button class="danger" type="button" @click="excluirConcluidosFiltrados">Excluir filtrados</button>
      </div>

      <div class="metrics concluded-metrics">
        <div><strong>{{ fretesConcluidosFiltrados.length }}</strong><span>Fretes concluidos</span></div>
        <div><strong>{{ formatarMoeda(totalConcluido) }}</strong><span>Total informado</span></div>
      </div>

      <div class="concluded-bulk-actions">
        <button type="button" @click="salvarValoresConcluidosFiltrados">Salvar valores preenchidos</button>
      </div>

      <div class="freight-list">
        <article v-for="frete in fretesConcluidosFiltrados" :key="frete.id" class="freight-card concluded-card">
          <div class="freight-main">
            <div>
              <p class="time">{{ formatarData(frete.data_coleta) }} - {{ frete.horario_coleta.slice(0, 5) }}</p>
              <h3>{{ frete.origem }} → {{ frete.destino }}</h3>
              <p class="muted">{{ nomeMotorista(frete.motorista_id) }} • {{ placaVeiculo(frete.veiculo_id) }} • NF: {{ frete.nota_fiscal || 'Sem nota' }}</p>
            </div>
            <span class="badge concluida">concluido</span>
          </div>

          <div class="billing-grid">
            <label class="field billing-field">
              Nota fiscal
              <input
                v-model="frete.nota_fiscal"
                placeholder="Numero da nota fiscal"
                @change="salvarDocumentoPreenchidoFrete(frete, 'nota_fiscal')"
              />
            </label>
            <label class="field billing-field">
              OC
              <input v-model="frete.oc" placeholder="Numero da OC" @change="salvarDocumentoPreenchidoFrete(frete, 'oc')" />
            </label>
            <label class="field billing-field">
              Valor do servico
              <input
                v-model="frete.valor_servico"
                type="number"
                min="0"
                step="0.01"
                placeholder="0,00"
                @change="salvarValorPreenchidoFrete(frete, 'valor_servico')"
              />
            </label>
            <label v-if="frete.retorno" class="field billing-field">
              Valor do retorno
              <input
                v-model="frete.valor_retorno"
                type="number"
                min="0"
                step="0.01"
                placeholder="0,00"
                @change="salvarValorPreenchidoFrete(frete, 'valor_retorno')"
              />
            </label>
            <label v-if="pontosAdicionaisFrete(frete).length > 0" class="field billing-field">
              Valor do ponto adicional
              <input
                v-model="frete.valor_ponto_adicional"
                type="number"
                min="0"
                step="0.01"
                placeholder="0,00"
                @change="salvarValorPreenchidoFrete(frete, 'valor_ponto_adicional')"
              />
            </label>
          </div>

          <div class="concluded-card-footer">
            <div class="billing-summary">
              <span>Servico: {{ formatarMoeda(frete.valor_servico) }}</span>
              <span v-if="frete.retorno">Retorno: {{ formatarMoeda(frete.valor_retorno) }}</span>
              <span v-if="pontosAdicionaisFrete(frete).length > 0">Ponto: {{ formatarMoeda(frete.valor_ponto_adicional) }}</span>
            </div>
            <div class="concluded-card-actions">
              <button class="secondary" type="button" @click="editarFrete(frete)">Editar frete</button>
              <button type="button" @click="salvarFechamentoFrete(frete)">Salvar fechamento</button>
            </div>
          </div>
        </article>

        <p v-if="fretesConcluidosFiltrados.length === 0" class="empty">Nenhum frete concluido para este periodo.</p>
      </div>
    </section>

    <section v-if="aba === 'caminhoes'" class="workspace">
      <div class="section-head">
        <div>
          <h2>Controle de caminhoes</h2>
          <p>Disponibilidade da frota e uso em fretes abertos.</p>
        </div>
        <label class="field compact">
          Situacao
          <select v-model="filtroSituacaoVeiculo">
            <option value="Todos">Todos</option>
            <option value="Disponivel">Disponiveis</option>
            <option value="Em uso">Em uso</option>
            <option value="Indisponivel">Indisponiveis</option>
          </select>
        </label>
        <label class="field compact">
          Tipo
          <select v-model="filtroTipoVeiculo">
            <option value="Todos">Todos</option>
            <option v-for="tipo in tiposVeiculo" :key="tipo" :value="tipo">{{ tipo }}</option>
          </select>
        </label>
      </div>

      <div class="metrics fleet-metrics">
        <div><strong>{{ totaisVeiculos.total }}</strong><span>Cadastrados</span></div>
        <div><strong>{{ totaisVeiculos.disponiveis }}</strong><span>Disponiveis</span></div>
        <div><strong>{{ totaisVeiculos.emUso }}</strong><span>Em uso</span></div>
        <div><strong>{{ totaisVeiculos.indisponiveis }}</strong><span>Indisponiveis</span></div>
      </div>

      <div class="vehicle-grid">
        <article v-for="veiculo in veiculosFiltrados" :key="veiculo.id" class="vehicle-card" :class="classeSituacaoVeiculo(veiculo)">
          <div class="vehicle-card-head">
            <div>
              <h3>{{ veiculo.tipo }}</h3>
              <p>{{ veiculo.placa }}</p>
              <small v-if="veiculo.observacoes" class="vehicle-feature">{{ veiculo.observacoes }}</small>
            </div>
            <span class="vehicle-status">{{ situacaoVeiculo(veiculo) }}</span>
          </div>

          <div v-if="fretesUsoVeiculo(veiculo).length > 0" class="vehicle-usage">
            <strong>Fretes abertos</strong>
            <div v-for="frete in fretesUsoVeiculo(veiculo)" :key="frete.id" class="vehicle-usage-row">
              <span>{{ formatarData(frete.data_coleta) }} - {{ horarioFrete(frete) }}</span>
              <small>{{ frete.cliente }} | {{ frete.origem }} -> {{ frete.destino }}</small>
              <small>{{ frete.status }}</small>
            </div>
          </div>

          <div v-if="!veiculo.ativo" class="vehicle-unavailable-reason">
            <strong>Motivo da indisponibilidade</strong>
            <p>{{ veiculo.motivo_indisponibilidade || 'Sem motivo informado' }}</p>
          </div>

          <div class="actions vehicle-actions">
            <button v-if="veiculo.ativo" class="danger" type="button" @click="abrirIndisponibilidadeVeiculo(veiculo)">
              Marcar indisponivel
            </button>
            <button v-else type="button" @click="liberarVeiculo(veiculo)">
              Liberar para uso
            </button>
          </div>
        </article>

        <p v-if="veiculosFiltrados.length === 0" class="empty">Nenhum caminhão nesta situacao.</p>
      </div>

      <div v-if="veiculoIndisponibilidadeAberto" class="modal-backdrop" @click.self="fecharIndisponibilidadeVeiculo">
        <div class="modal-panel">
          <div>
            <h3>Indisponibilizar caminhao</h3>
            <p>{{ veiculoIndisponibilidadeAberto.placa }} - {{ veiculoIndisponibilidadeAberto.tipo }}</p>
          </div>

          <label class="field">
            Motivo
            <textarea v-model="motivoIndisponibilidadeVeiculo" rows="4" placeholder="Ex: conserto, revisao, reservado"></textarea>
          </label>

          <div class="actions">
            <button class="secondary" type="button" @click="fecharIndisponibilidadeVeiculo">Cancelar</button>
            <button class="danger" type="button" @click="confirmarIndisponibilidadeVeiculo">Confirmar</button>
          </div>
        </div>
      </div>
    </section>

    <section v-if="aba === 'novo-frete'" class="workspace">
      <div class="section-head">
        <div>
          <h2>{{ freteEditandoId ? 'Editar frete' : 'Cadastrar frete' }}</h2>
          <p>{{ freteEditandoId ? 'Ajuste os dados do frete e salve as alteracoes.' : 'Use para fretes recebidos por planilha ou WhatsApp.' }}</p>
        </div>
      </div>

      <form class="form-grid" @submit.prevent="cadastrarFrete">
        <label class="field">
          Cliente
          <select v-model="novoFrete.cliente" required>
            <option value="" disabled></option>
            <option v-for="empresa in empresasClientes" :key="empresa.id" :value="empresa.nome">{{ empresa.nome }}</option>
          </select>
        </label>
        <label class="field">Data<input v-model="novoFrete.data_coleta" type="date" required /></label>
        <label class="field">Horário<input v-model="novoFrete.horario_coleta" type="time" required /></label>
        <label class="field">Nota fiscal<input v-model="novoFrete.nota_fiscal" placeholder="Opcional" /></label>
        <div class="field company-picker">
          <span>Origem</span>
          <input v-model="buscaOrigemFrete" :placeholder="novoFrete.origem || 'Buscar empresa de origem'" />
          <div v-if="buscaOrigemFrete" class="picker-results">
            <button v-for="empresa in empresasOrigemDisponiveis" :key="empresa.id" class="picker-option" type="button" @click="selecionarOrigemFrete(empresa)">
              {{ empresa.nome }}<small>{{ empresa.cnpj || 'CNPJ nao informado' }}</small>
            </button>
            <p v-if="empresasOrigemDisponiveis.length === 0">Nenhuma empresa encontrada.</p>
          </div>
          <div v-if="novoFrete.origem" class="selected-company">
            <span>{{ novoFrete.origem }}</span>
            <button type="button" @click="limparOrigemFrete">Trocar</button>
          </div>
          <input v-model="novoFrete.origem" class="hidden-required-input" required tabindex="-1" aria-hidden="true" />
        </div>
        <div class="field wide company-picker">
          <span>Empresas de coleta/passagem</span>
          <input v-model="buscaEmpresaColeta" placeholder="Buscar empresa para adicionar" />
          <div v-if="buscaEmpresaColeta" class="picker-results">
            <button v-for="empresa in empresasColetaDisponiveis" :key="empresa.id" class="picker-option" type="button" @click="adicionarEmpresaColeta(empresa)">
              {{ empresa.nome }}
            </button>
            <p v-if="empresasColetaDisponiveis.length === 0">Nenhuma empresa encontrada.</p>
          </div>
          <div class="chips">
            <button v-for="empresa in novoFrete.empresas_coleta" :key="empresa" type="button" @click="removerEmpresaColeta(empresa)">
              {{ empresa }} ×
            </button>
          </div>
          <small v-if="empresas.length === 0">Cadastre empresas antes de criar fretes.</small>
        </div>
        <div class="field company-picker">
          <span>Destino</span>
          <input v-model="buscaDestinoFrete" :placeholder="novoFrete.destino || 'Buscar empresa de destino'" />
          <div v-if="buscaDestinoFrete" class="picker-results">
            <button v-for="empresa in empresasDestinoDisponiveis" :key="empresa.id" class="picker-option" type="button" @click="selecionarDestinoFrete(empresa)">
              {{ empresa.nome }}<small>{{ empresa.cnpj || 'CNPJ nao informado' }}</small>
            </button>
            <p v-if="empresasDestinoDisponiveis.length === 0">Nenhuma empresa encontrada.</p>
          </div>
          <div v-if="novoFrete.destino" class="selected-company">
            <span>{{ novoFrete.destino }}</span>
            <button type="button" @click="limparDestinoFrete">Trocar</button>
          </div>
          <input v-model="novoFrete.destino" class="hidden-required-input" required tabindex="-1" aria-hidden="true" />
        </div>
        <label class="field">
          Tipo de veículo requisitado
          <select v-model="novoFrete.tipo_caminhao_necessario" required>
            <option v-for="tipo in tiposVeiculo" :key="tipo" :value="tipo">{{ tipo }}</option>
          </select>
        </label>
        <label class="field">Valor do servico<input v-model="novoFrete.valor_servico" type="number" min="0" step="0.01" placeholder="Opcional" /></label>
        <label class="check-field"><input v-model="novoFrete.retorno" type="checkbox" /> Criar retorno para cobranca</label>
        <label class="field">Motorista<select v-model="novoFrete.motorista_id" required><option value="" disabled></option><option v-for="motorista in motoristas" :key="motorista.id" :value="motorista.id">{{ motorista.nome }}</option></select></label>
        <label class="field">Caminhao<select v-model="novoFrete.veiculo_id" required><option value="" disabled></option><option v-for="veiculo in veiculos" :key="veiculo.id" :value="veiculo.id">{{ veiculo.placa }} - {{ veiculo.tipo }}</option></select></label>
        <label class="field wide">Observacoes<textarea v-model="novoFrete.observacoes" rows="3"></textarea></label>
        <div class="form-actions freight-form-actions">
          <button type="submit">{{ freteEditandoId ? 'Salvar alteracoes' : 'Cadastrar frete' }}</button>
          <button v-if="freteEditandoId" class="secondary" type="button" @click="cancelarEdicaoFrete">Cancelar edicao</button>
        </div>
      </form>
    </section>

    <section v-if="aba === 'cadastros'" class="workspace">
      <div class="section-head">
        <div>
          <h2>Cadastros</h2>
          <p>Escolha o tipo de cadastro que deseja criar ou consultar.</p>
        </div>
      </div>

      <div class="cadastro-switch">
        <button :class="{ active: cadastroAtivo === 'motoristas' }" type="button" @click="cadastroAtivo = 'motoristas'">Motoristas</button>
        <button :class="{ active: cadastroAtivo === 'veiculos' }" type="button" @click="cadastroAtivo = 'veiculos'">Caminhões</button>
        <button :class="{ active: cadastroAtivo === 'empresas' }" type="button" @click="cadastroAtivo = 'empresas'">Empresas</button>
      </div>

      <div v-if="cadastroAtivo === 'motoristas'">
        <h2>Motoristas</h2>
        <form class="stack-form" @submit.prevent="cadastrarMotorista">
          <input v-model="novoMotorista.nome" placeholder="Nome" required />
          <input v-model="novoMotorista.telefone" placeholder="Telefone/WhatsApp" required />
          <input v-model="novoMotorista.rg" placeholder="RG" required maxlength="12" @input="aplicarMascaraRgMotorista" />
          <input v-model="novoMotorista.cpf" placeholder="CPF" required maxlength="14" @input="aplicarMascaraCpfMotorista" />
          <input v-model="novoMotorista.cnh" placeholder="CNH" />
          <textarea v-model="novoMotorista.observacoes" placeholder="Observacoes" rows="3"></textarea>
          <div class="form-actions">
            <button type="submit">{{ motoristaEditandoId ? 'Salvar motorista' : 'Cadastrar motorista' }}</button>
            <button v-if="motoristaEditandoId" class="secondary" type="button" @click="limparMotorista">Cancelar edição</button>
          </div>
        </form>
        <ul class="simple-list">
          <li v-for="motorista in motoristas" :key="motorista.id">
            <span>
              {{ motorista.nome }}
              <small>{{ motorista.telefone }}</small>
              <small v-if="motorista.observacoes" class="registry-note">Obs: {{ motorista.observacoes }}</small>
            </span>
            <div class="registry-actions">
              <button class="secondary compact-button" type="button" @click="editarMotorista(motorista)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirMotorista(motorista.id)">Excluir</button>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="cadastroAtivo === 'veiculos'">
        <h2>Caminhoes</h2>
        <form class="stack-form" @submit.prevent="cadastrarVeiculo">
          <input v-model="novoVeiculo.placa" placeholder="Placa" required />
          <select v-model="novoVeiculo.tipo" required>
            <option v-for="tipo in tiposVeiculo" :key="tipo" :value="tipo">{{ tipo }}</option>
          </select>
          <textarea v-model="novoVeiculo.observacoes" placeholder="Observacoes" rows="3"></textarea>
          <div class="form-actions">
            <button type="submit">{{ veiculoEditandoId ? 'Salvar caminhao' : 'Cadastrar caminhao' }}</button>
            <button v-if="veiculoEditandoId" class="secondary" type="button" @click="limparVeiculo">Cancelar edição</button>
          </div>
        </form>
        <ul class="simple-list">
          <li v-for="veiculo in veiculos" :key="veiculo.id">
            <span>
              {{ veiculo.placa }}
              <small>{{ veiculo.tipo }}</small>
              <small v-if="veiculo.observacoes" class="registry-note">Obs: {{ veiculo.observacoes }}</small>
            </span>
            <div class="registry-actions">
              <button class="secondary compact-button" type="button" @click="editarVeiculo(veiculo)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirVeiculo(veiculo.id)">Excluir</button>
            </div>
          </li>
        </ul>
      </div>

      <div v-if="cadastroAtivo === 'empresas'">
        <h2>Empresas</h2>
        <form class="stack-form" @submit.prevent="cadastrarEmpresa">
          <input v-model="novaEmpresa.nome" placeholder="Nome da empresa" required />
          <input v-model="novaEmpresa.cnpj" placeholder="CNPJ" required />
          <label class="check-field compact-check"><input v-model="novaEmpresa.cliente" type="checkbox" />Cliente</label>
          <div class="cep-row">
            <input v-model="novaEmpresa.cep" placeholder="CEP" required @blur="buscarCepEmpresa" />
            <button class="secondary" type="button" @click="buscarCepEmpresa">Buscar CEP</button>
          </div>
          <input v-model="novaEmpresa.logradouro" placeholder="Rua / avenida" required />
          <div class="address-grid">
            <input v-model="novaEmpresa.numero" placeholder="Numero" required />
            <input v-model="novaEmpresa.complemento" placeholder="Complemento" />
          </div>
          <input v-model="novaEmpresa.bairro" placeholder="Bairro" required />
          <div class="address-grid">
            <input v-model="novaEmpresa.cidade" placeholder="Cidade" required />
            <input v-model="novaEmpresa.uf" placeholder="UF" maxlength="2" required />
          </div>
          <textarea v-model="novaEmpresa.observacoes" placeholder="Observacoes" rows="3"></textarea>
          <div class="form-actions">
            <button type="submit">{{ empresaEditandoId ? 'Salvar empresa' : 'Cadastrar empresa' }}</button>
            <button v-if="empresaEditandoId" class="secondary" type="button" @click="limparEmpresa">Cancelar edição</button>
          </div>
        </form>
        <ul class="simple-list">
          <li v-for="empresa in empresas" :key="empresa.id">
            <span>
              {{ empresa.nome }}
              <small>{{ empresa.cnpj }} - {{ enderecoEmpresa(empresa) }}</small>
              <small v-if="empresa.cliente" class="registry-note">Cliente</small>
              <small v-if="empresa.observacoes" class="registry-note">Obs: {{ empresa.observacoes }}</small>
            </span>
            <div class="registry-actions">
              <button class="secondary compact-button" type="button" @click="editarEmpresa(empresa)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirEmpresa(empresa.id)">Excluir</button>
            </div>
          </li>
        </ul>
      </div>
    </section>

    <section v-if="aba === 'relatorios'" class="workspace">
      <div class="section-head">
        <div>
          <h2>Status dos motoristas</h2>
          <p>Cores indicam quem esta em servico, disponivel ou indisponivel.</p>
        </div>
        <button type="button" @click="exportarHistoricoMotoristas">Exportar historico Excel</button>
      </div>

      <div class="driver-cards">
        <article v-for="motorista in motoristasAlocacao" :key="motorista.id" class="driver-card" :class="classeSituacaoMotorista(motorista)">
          <div class="driver-card-head">
            <div>
              <h3>{{ motorista.nome }}</h3>
              <p v-if="motorista.observacoes">{{ motorista.observacoes }}</p>
            </div>
            <span class="driver-status">{{ situacaoMotorista(motorista) }}</span>
          </div>
          <div class="driver-stats">
            <span><strong>{{ motorista.viagens_dia }}</strong>Hoje</span>
            <span><strong>{{ motorista.viagens_semana }}</strong>Semana</span>
          </div>
          <div v-if="fretesUsoMotorista(motorista).length > 0" class="driver-active-freights">
            <strong>Fretes em aberto</strong>
            <div v-for="frete in fretesUsoMotorista(motorista)" :key="frete.id" class="driver-active-row">
              <span>{{ formatarData(frete.data_coleta) }} - {{ horarioFrete(frete) }}</span>
              <small>{{ frete.cliente }} | {{ frete.origem }} -> {{ frete.destino }}</small>
              <small>{{ frete.status }}</small>
            </div>
          </div>
          <button class="secondary" type="button" @click="motoristaAberto = motoristaAberto === motorista.id ? null : motorista.id">
            {{ motoristaAberto === motorista.id ? 'Ocultar dados' : 'Ver dados' }}
          </button>
          <div v-if="motoristaAberto === motorista.id" class="driver-data">
            <span>Telefone: {{ motorista.telefone }}</span>
            <span>RG: {{ formatarRg(motorista.rg) }}</span>
            <span>CPF: {{ formatarCpf(motorista.cpf) }}</span>

            <div class="driver-history">
              <strong>Historico de fretes</strong>
              <div v-for="frete in historicoFretesMotorista(motorista.id)" :key="frete.id" class="driver-history-row">
                <div>
                  <span>{{ formatarData(frete.data_coleta) }}</span>
                  <small>{{ frete.origem }} -> {{ frete.destino }}</small>
                </div>
                <p v-if="pontosAdicionaisFrete(frete).length > 0">
                  Pontos adicionais: {{ pontosAdicionaisFrete(frete).join(', ') }}
                </p>
                <p v-if="frete.observacoes">Obs: {{ frete.observacoes }}</p>
              </div>
              <p v-if="historicoFretesMotorista(motorista.id).length === 0" class="driver-history-empty">
                Nenhum frete concluido encontrado.
              </p>
            </div>
          </div>
        </article>
      </div>
    </section>
    </div>
  </main>
</template>
