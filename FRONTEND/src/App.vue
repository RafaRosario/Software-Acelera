<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import axios from 'axios'
import { useRoute, useRouter } from 'vue-router'
import logoAcelera from './assets/logoacelera.png'
import iconFretes from './assets/icon-fretes.png'
import iconCriarFrete from './assets/icon-criar-frete.png'
import iconConcluidos from './assets/icon-concluidos.png'
import iconCadastro from './assets/icon-cadastro.png'
import iconMotorista from './assets/icon-motorista.png'
import iconCaminhao from './assets/icon-caminhao.png'
import iconFornecedores from './assets/icon-fornecedores.png'
import iconPrestadores from './assets/icon-prestadores.png'
import ChecklistPublicView from './views/ChecklistPublicView.vue'

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
]

const router = useRouter()
const route = useRoute()

const paginaPorRota = {
  '/fretes': 'fretes',
  '/concluidos': 'concluidos',
  '/caminhoes': 'caminhoes',
  '/motoristas': 'relatorios',
  '/novo-frete': 'novo-frete',
  '/cadastros': 'cadastros',
  '/fornecedores': 'fornecedores',
  '/prestadores-servicos': 'prestadores-servicos',
}

const rotaPorPagina = Object.fromEntries(Object.entries(paginaPorRota).map(([rota, pagina]) => [pagina, rota]))

const carregando = ref(false)
const erro = ref('')
const aba = ref('fretes')
const cadastroAtivo = ref('motoristas')
const motoristaAberto = ref(null)
const motoristas = ref([])
const motoristasAlocacao = ref([])
const veiculos = ref([])
const empresas = ref([])
const fornecedores = ref([])
const prestadoresServicos = ref([])
const fretes = ref([])
const filtroDataInicioFretes = ref(new Date().toISOString().slice(0, 10))
const filtroDataFimFretes = ref(new Date().toISOString().slice(0, 10))
const filtroStatus = ref('Todos')
const filtroClienteFretes = ref('Todos')
const filtroPendenciasAntigas = ref(false)
const filtroConcluidos = ref('todos')
const filtroClienteConcluidos = ref('Todos')
const dataInicioConcluidos = ref('')
const dataFimConcluidos = ref('')
const buscaOrigemFrete = ref('')
const buscaEmpresaColeta = ref('')
const buscaDestinoFrete = ref('')
const buscaMotoristasCadastro = ref('')
const buscaVeiculosCadastro = ref('')
const buscaEmpresasCadastro = ref('')
const toast = ref(null)
const freteArrastandoId = ref(null)
const statusDestinoAtivo = ref('')
const freteAbertoId = ref(null)
const menuStatusFrete = ref({ aberto: false, x: 0, y: 0, maxHeight: 420, frete: null })
const filtroSituacaoVeiculo = ref('Todos')
const filtroTipoVeiculo = ref('Todos')
const veiculoIndisponibilidadeAberto = ref(null)
const motivoIndisponibilidadeVeiculo = ref('')
const motoristaEditandoId = ref(null)
const veiculoEditandoId = ref(null)
const empresaEditandoId = ref(null)
const fornecedorEditandoId = ref(null)
const prestadorEditandoId = ref(null)
const freteEditandoId = ref(null)
const abaRetornoEdicaoFrete = ref('fretes')
const sidebarRecolhida = ref(false)
const menuMobileAberto = ref(false)
const avisoPendenciasMostrado = ref(false)
const checklistToken = computed(() => String(route.params.token || ''))
const modoChecklist = computed(() => Boolean(checklistToken.value))
const checklistCarregando = ref(false)
const checklistSalvando = ref(false)
const checklistErro = ref('')
const checklistSucesso = ref('')
const checklistPublico = ref(null)
const checklistResposta = ref({
  tacografo: null,
  pneus: null,
  oleo: null,
  avarias_externas: null,
  avarias_internas: null,
  observacoes: '',
})
const itensChecklistCaminhao = [
  { chave: 'tacografo', rotulo: 'Tacógrafo' },
  { chave: 'pneus', rotulo: 'Pneus' },
  { chave: 'oleo', rotulo: 'Óleo' },
  { chave: 'avarias_externas', rotulo: 'Avarias externas' },
  { chave: 'avarias_internas', rotulo: 'Avarias internas' },
]
const respostaChecklistVazia = () => ({
  tacografo: null,
  pneus: null,
  oleo: null,
  avarias_externas: null,
  avarias_internas: null,
  observacoes: '',
})

const novoMotorista = ref({ nome: '', telefone: '', rg: '', cpf: '', cnh: '', observacoes: '' })
const novoVeiculo = ref({ placa: '', tipo: 'Truk', observacoes: '', observacao_estado: '' })
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
const novoFornecedor = ref({
  nome: '',
  telefone: '',
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  endereco: '',
  cidade: '',
  uf: '',
  marca: '',
  observacoes: '',
})
const tiposPrestadorServico = ['valvula', 'mecanicos', 'bombistas']
const novoPrestadorServico = ref({
  nome: '',
  telefone: '',
  cep: '',
  logradouro: '',
  numero: '',
  complemento: '',
  bairro: '',
  cidade: '',
  uf: '',
  endereco: '',
  tipo: tiposPrestadorServico[0],
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
    resumo: 'FRETES',
  },
  concluidos: {
    titulo: 'Concluídos',
    resumo: 'CONCLUÍDOS',
  },
  caminhoes: {
    titulo: 'Caminhões',
    resumo: 'CAMINHÃO',
  },
  relatorios: {
    titulo: 'Motoristas',
    resumo: 'MOTORISTA',
  },
  'novo-frete': {
    titulo: 'Novo frete',
    resumo: 'CRIAR FRETE',
  },
  cadastros: {
    titulo: 'Cadastros',
    resumo: 'CADASTRO',
  },
  fornecedores: {
    titulo: 'Fornecedores',
    resumo: 'FORNECEDORES',
  },
  'prestadores-servicos': {
    titulo: 'Prestadores de serviços',
    resumo: 'PRESTADORES',
  },
}

const paginaAtual = computed(() => {
  if (aba.value === 'novo-frete' && freteEditandoId.value) {
    return {
      titulo: 'Editar frete',
      resumo: 'CRIAR FRETE',
    }
  }
  return paginas[aba.value] || paginas.fretes
})

const navegarParaPagina = (pagina, cadastro = null, substituir = false) => {
  if (modoChecklist.value) return

  const path = rotaPorPagina[pagina] || '/fretes'
  const query = pagina === 'cadastros' ? { cadastro: cadastro || cadastroAtivo.value || 'motoristas' } : undefined
  const queryAtual = typeof route.query.cadastro === 'string' ? route.query.cadastro : null
  const queryDestino = query?.cadastro || null

  if (route.path === path && queryAtual === queryDestino) return

  const navegar = substituir ? router.replace : router.push
  navegar({ path, query }).catch(() => {})
}

const selecionarCadastroAtivo = (cadastro) => {
  cadastroAtivo.value = cadastro
  if (aba.value === 'cadastros') navegarParaPagina('cadastros', cadastro, true)
}

const sincronizarRotaComEstado = () => {
  if (modoChecklist.value) return

  const pagina = paginaPorRota[route.path] || 'fretes'
  if (aba.value !== pagina) aba.value = pagina

  if (pagina === 'cadastros') {
    const cadastro = String(route.query.cadastro || 'motoristas')
    if (['motoristas', 'veiculos', 'empresas'].includes(cadastro)) {
      cadastroAtivo.value = cadastro
    }
  }
}

const abrirPagina = (pagina, cadastro = null) => {
  aba.value = pagina
  if (cadastro) cadastroAtivo.value = cadastro
  menuMobileAberto.value = false
  navegarParaPagina(pagina, cadastro)
}

const carregarTudo = async () => {
  carregando.value = true
  erro.value = ''
  try {
    const [motoristasResp, alocacaoResp, veiculosResp, empresasResp, fretesResp, fornecedoresResp, prestadoresResp] = await Promise.all([
      axios.get(`${API_URL}/motoristas/`),
      axios.get(`${API_URL}/motoristas/alocacao/`),
      axios.get(`${API_URL}/veiculos/`),
      axios.get(`${API_URL}/empresas/`),
      axios.get(`${API_URL}/fretes/`),
      axios.get(`${API_URL}/fornecedores/`),
      axios.get(`${API_URL}/prestadores-servicos/`),
    ])
    motoristas.value = motoristasResp.data
    motoristasAlocacao.value = alocacaoResp.data
    veiculos.value = veiculosResp.data
    empresas.value = empresasResp.data
    fretes.value = fretesResp.data
    fornecedores.value = fornecedoresResp.data
    prestadoresServicos.value = prestadoresResp.data
    if (!avisoPendenciasMostrado.value && fretesResp.data.some(freteEstaAtrasado)) {
      avisoPendenciasMostrado.value = true
      mostrarToast('Existem fretes antigos em aberto. Revise as pendências.', 'error')
    }
  } catch (error) {
    erro.value = 'Não foi possível conectar na API. Verifique se o backend está rodando.'
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

function hojeLocal() {
  const agora = new Date()
  return new Date(agora.getFullYear(), agora.getMonth(), agora.getDate())
}

function diasAbertoFrete(frete) {
  if (!frete?.data_coleta) return 0
  return Math.max(0, Math.floor((hojeLocal() - dataLocal(frete.data_coleta)) / 86400000))
}

function freteEstaAtrasado(frete) {
  return Boolean(
    frete?.data_coleta &&
      !freteEhRetorno(frete) &&
      frete.status !== STATUS_CANCELADA &&
      !statusEhConcluido(frete.status) &&
      dataLocal(frete.data_coleta) < hojeLocal(),
  )
}

const textoAtrasoFrete = (frete) => {
  const dias = diasAbertoFrete(frete)
  return dias === 1 ? 'Aberto há 1 dia' : `Aberto há ${dias} dias`
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
    if (frete.status === STATUS_CANCELADA) return false
    if (filtroPendenciasAntigas.value && !freteEstaAtrasado(frete)) return false
    const dataConfere = filtroPendenciasAntigas.value ? true : dataConferePeriodoFretes(frete.data_coleta)
    const clienteConfere = filtroClienteFretes.value === 'Todos' || frete.cliente === filtroClienteFretes.value
    const statusConfere = statusConfereFiltroFrete(frete.status, filtroStatus.value)
    return dataConfere && clienteConfere && statusConfere
  })
})

const fretesAtrasados = computed(() => {
  return fretes.value
    .filter(freteEstaAtrasado)
    .sort((a, b) => {
      const dataA = `${a.data_coleta || ''} ${a.horario_coleta || ''}`
      const dataB = `${b.data_coleta || ''} ${b.horario_coleta || ''}`
      return dataA.localeCompare(dataB)
    })
})

const maiorAtrasoDias = computed(() => Math.max(0, ...fretesAtrasados.value.map(diasAbertoFrete)))

const ativarFiltroPendenciasAntigas = () => {
  filtroPendenciasAntigas.value = true
  filtroStatus.value = 'Todos'
  freteAbertoId.value = null
}

const limparFiltroPendenciasAntigas = () => {
  filtroPendenciasAntigas.value = false
}

const statusVisualFrete = (status) => {
  if (status === 'Aguardando horario') return 'Aguardando horário'
  if (statusEhConcluido(status)) return 'Concluído'
  return 'Em andamento'
}

const classeStatusVisualFrete = (status) =>
  statusVisualFrete(status)
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replaceAll(' ', '-')

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
    if (frete.status === STATUS_CANCELADA) return false
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

const normalizarTextoBusca = (valor) => {
  return String(valor || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

const motoristasCadastroFiltrados = computed(() => {
  const termo = normalizarTextoBusca(buscaMotoristasCadastro.value)
  if (!termo) return motoristas.value

  return motoristas.value.filter((motorista) => {
    const dados = [
      motorista.nome,
      motorista.telefone,
      motorista.cpf,
      motorista.rg,
      motorista.cnh,
      motorista.observacoes,
    ]
      .filter(Boolean)
      .join(' ')

    return normalizarTextoBusca(dados).includes(termo)
  })
})

const veiculosCadastroFiltrados = computed(() => {
  const termo = normalizarTextoBusca(buscaVeiculosCadastro.value)
  if (!termo) return veiculos.value

  return veiculos.value.filter((veiculo) => {
    const dados = [veiculo.placa, veiculo.tipo, veiculo.observacoes, veiculo.observacao_estado, veiculo.motivo_indisponibilidade]
      .filter(Boolean)
      .join(' ')

    return normalizarTextoBusca(dados).includes(termo)
  })
})

const empresasCadastroFiltradas = computed(() => {
  const termo = normalizarTextoBusca(buscaEmpresasCadastro.value)
  if (!termo) return empresas.value

  return empresas.value.filter((empresa) => {
    const dados = [
      empresa.nome,
      empresa.cnpj,
      empresa.cep,
      empresa.logradouro,
      empresa.numero,
      empresa.complemento,
      empresa.bairro,
      empresa.cidade,
      empresa.uf,
      empresa.endereco,
      empresa.observacoes,
    ]
      .filter(Boolean)
      .join(' ')

    return normalizarTextoBusca(dados).includes(termo)
  })
})

const nomeMotorista = (id) => motoristas.value.find((motorista) => motorista.id === id)?.nome || 'Sem motorista'
const telefoneMotorista = (id) => motoristas.value.find((motorista) => motorista.id === id)?.telefone || ''
const placaVeiculo = (id) => veiculos.value.find((veiculo) => veiculo.id === id)?.placa || 'Sem caminhão'
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

  if (frete.status && frete.status !== STATUS_CANCELADA && !status.includes(frete.status)) {
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
  return colunas
})

const fretesPorStatusKanban = (status) => {
  return fretesFiltrados.value.filter((frete) => {
    if (status === STATUS_CONCLUIDO) return statusEhConcluido(frete.status)
    if (status === STATUS_PONTOS_ADICIONAIS) return statusEhPontoAdicional(frete.status) && frete.status !== STATUS_CAMINHO_PONTO_ADICIONAL
    return frete.status === status
  }).sort((a, b) => {
    const atraso = Number(freteEstaAtrasado(b)) - Number(freteEstaAtrasado(a))
    if (atraso !== 0) return atraso
    const dataA = `${a.data_coleta || ''} ${a.horario_coleta || ''}`
    const dataB = `${b.data_coleta || ''} ${b.horario_coleta || ''}`
    return dataA.localeCompare(dataB)
  })
}

const freteDetalhe = computed(() => fretes.value.find((frete) => frete.id === freteAbertoId.value))

const rotuloStatusFrete = (status) => {
  if (status === STATUS_AGUARDANDO) return 'Aguardando horário'
  if (status === STATUS_CAMINHO_P1) return 'A caminho do P1'
  if (status === STATUS_COLETADO_P1) return 'Aguardando coleta no P1'
  if (status === STATUS_CAMINHO_PONTO_ADICIONAL) return 'A caminho do ponto adicional'
  if (status === STATUS_PONTOS_ADICIONAIS) return 'Pontos adicionais'
  if (status === STATUS_CAMINHO_DESTINO) return 'Coletado no P1, a caminho do destino'
  if (status === STATUS_CHEGADA_DESTINO) return 'Chegada ao destino'
  if (status === STATUS_RETORNANDO) return 'Retornando'
  if (statusEhConcluido(status)) return 'Concluído'
  return status
}

const classeStatusKanban = (status) => status.toLowerCase().replaceAll(' ', '-')

const subtituloStatusKanban = (status) => {
  if (status === STATUS_AGUARDANDO) return 'Ainda não saiu'
  if (status === STATUS_CAMINHO_P1) return 'Indo para a coleta'
  if (status === STATUS_COLETADO_P1) return 'Aguardando confirmação da coleta'
  if (status === STATUS_CAMINHO_PONTO_ADICIONAL) return 'Indo para parada extra'
  if (status === STATUS_PONTOS_ADICIONAIS) return 'Paradas extras feitas'
  if (status === STATUS_CAMINHO_DESTINO) return 'Coleta feita, indo para entrega'
  if (status === STATUS_CHEGADA_DESTINO) return 'No destino'
  if (status === STATUS_RETORNANDO) return 'Voltando com retorno'
  if (status === STATUS_CONCLUIDO) return 'Finalizado'
  return 'Em operação'
}

const abrirFreteDetalhe = (id) => {
  freteAbertoId.value = id
}

const fecharFreteDetalhe = () => {
  freteAbertoId.value = null
}

const rotaCompactaFrete = (frete) => {
  return pontosMensagemFrete(frete).join(' -> ')
}

const horarioFrete = (frete) => frete.horario_coleta?.slice(0, 5) || '--:--'

const abrirMenuStatusFrete = (event, frete) => {
  const alvo = event?.currentTarget
  const caixa = alvo?.getBoundingClientRect?.()
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight
  const larguraMenu = 250
  const margemMenu = 16
  const totalStatus = statusDisponiveisFrete(frete).length
  const alturaNatural = Math.min(420, 88 + totalStatus * 38)
  const ehTelaMenor = window.matchMedia?.('(max-width: 860px)').matches ?? viewportWidth <= 860
  const maxHeight = ehTelaMenor
    ? Math.round(Math.min(560, viewportHeight * 0.78))
    : Math.min(alturaNatural, Math.max(180, viewportHeight - margemMenu * 2))
  const x = event?.clientX ?? (caixa ? caixa.left + caixa.width / 2 : window.innerWidth / 2)
  const y = event?.clientY ?? (caixa ? caixa.top + caixa.height : window.innerHeight / 2)
  const xMaximo = Math.max(margemMenu, viewportWidth - larguraMenu - margemMenu)
  const yMaximo = Math.max(margemMenu, viewportHeight - maxHeight - margemMenu)

  menuStatusFrete.value = {
    aberto: true,
    x: Math.max(margemMenu, Math.min(x, xMaximo)),
    y: Math.max(margemMenu, Math.min(y, yMaximo)),
    maxHeight,
    frete,
  }
}

const fecharMenuStatusFrete = () => {
  menuStatusFrete.value = { aberto: false, x: 0, y: 0, maxHeight: 420, frete: null }
}

const moverFreteParaStatus = async (frete, status) => {
  if (!frete) return
  if (!statusDisponiveisFrete(frete).includes(status)) {
    mostrarToast('Este status não existe para este frete.', 'error')
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
  if (frete.status === STATUS_AGUARDANDO) return 'aguardando horário'
  if (frete.status === STATUS_CAMINHO_P1) return `a caminho ${frete.origem}`
  if (frete.status === STATUS_COLETADO_P1) return `aguardando coleta ${frete.origem}`
  if (frete.status === STATUS_CAMINHO_PONTO_ADICIONAL) return 'coleta realizada, a caminho ponto adicional'
  if (statusEhPontoAdicional(frete.status)) return 'pontos adicionais coletados, em direção ao destino final'
  if (frete.status === STATUS_CAMINHO_DESTINO) return `coletado ${frete.origem}, a caminho do destino`
  if (frete.status === STATUS_CHEGADA_DESTINO) return `aguardando para descarregar ${frete.destino}`
  if (frete.status === STATUS_RETORNANDO) return 'retornando'
  if (statusEhConcluido(frete.status)) return '✅'
  return statusVisualFrete(frete.status).toLowerCase()
}

const linhaAtualizacaoEdscha = (frete) => {
  const pontos = pontosMensagemFrete(frete)
  const rota = pontos.join(' x ')
  return `${frete.tipo_caminhao_necessario} - ${rota}, ${resumoStatusEdscha(frete)}`
}

const gerarAtualizacaoEdscha = () => {
  const fretesAtualizacao = fretesFiltrados.value.filter((frete) => frete.status !== STATUS_CANCELADA && !freteEhRetorno(frete))

  if (fretesAtualizacao.length === 0) {
    mostrarToast('Não há fretes para atualizar neste filtro.', 'error')
    return ''
  }

  return fretesAtualizacao.map(linhaAtualizacaoEdscha).join('\n\n')
}

const copiarAtualizacaoEdscha = async () => {
  const mensagem = gerarAtualizacaoEdscha()
  if (!mensagem) return
  await navigator.clipboard.writeText(mensagem)
  mostrarToast('Atualização Edscha copiada.')
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
    mostrarToast('Não foi possível salvar. Tente novamente.', 'error')
  }
}

const limparMotorista = () => {
  motoristaEditandoId.value = null
  novoMotorista.value = { nome: '', telefone: '', rg: '', cpf: '', cnh: '', observacoes: '' }
}

const limparVeiculo = () => {
  veiculoEditandoId.value = null
  novoVeiculo.value = { placa: '', tipo: 'Truk', observacoes: '', observacao_estado: '' }
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

const limparFornecedor = () => {
  fornecedorEditandoId.value = null
  novoFornecedor.value = {
    nome: '',
    telefone: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    endereco: '',
    cidade: '',
    uf: '',
    marca: '',
    observacoes: '',
  }
}

const limparPrestadorServico = () => {
  prestadorEditandoId.value = null
  novoPrestadorServico.value = {
    nome: '',
    telefone: '',
    cep: '',
    logradouro: '',
    numero: '',
    complemento: '',
    bairro: '',
    cidade: '',
    uf: '',
    endereco: '',
    tipo: tiposPrestadorServico[0],
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
    observacao_estado: veiculo.observacao_estado || '',
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

const editarFornecedor = (fornecedor) => {
  fornecedorEditandoId.value = fornecedor.id
  novoFornecedor.value = {
    nome: fornecedor.nome || '',
    telefone: fornecedor.telefone || '',
    cep: fornecedor.cep || '',
    logradouro: fornecedor.logradouro || '',
    numero: fornecedor.numero || '',
    complemento: fornecedor.complemento || '',
    bairro: fornecedor.bairro || '',
    endereco: fornecedor.endereco || '',
    cidade: fornecedor.cidade || '',
    uf: fornecedor.uf || '',
    marca: fornecedor.marca || '',
    observacoes: fornecedor.observacoes || '',
  }
}

const editarPrestadorServico = (prestador) => {
  prestadorEditandoId.value = prestador.id
  novoPrestadorServico.value = {
    nome: prestador.nome || '',
    telefone: prestador.telefone || '',
    cep: prestador.cep || '',
    logradouro: prestador.logradouro || prestador.rua || '',
    numero: prestador.numero || '',
    complemento: prestador.complemento || '',
    bairro: prestador.bairro || '',
    cidade: prestador.cidade || '',
    uf: prestador.uf || '',
    endereco: prestador.endereco || '',
    tipo: prestador.tipo || tiposPrestadorServico[0],
    observacoes: prestador.observacoes || '',
  }
}

const cadastrarMotorista = async () => {
  aplicarMascaraRgMotorista()
  aplicarMascaraCpfMotorista()

  if (!rgValido(novoMotorista.value.rg)) {
    mostrarToast('RG inválido. Confira o número informado.', 'error')
    return
  }

  if (!cpfValido(novoMotorista.value.cpf)) {
    mostrarToast('CPF inválido. Confira os dígitos.', 'error')
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
  const payload = {
    ...novoVeiculo.value,
    placa: novoVeiculo.value.placa.trim(),
    observacao_estado: (novoVeiculo.value.observacao_estado || '').trim(),
  }

  try {
    if (veiculoEditandoId.value) {
      await axios.put(`${API_URL}/veiculos/${veiculoEditandoId.value}`, payload)
      limparVeiculo()
      await carregarTudo()
      mostrarToast('Caminhão atualizado com sucesso.')
      return
    }

    await axios.post(`${API_URL}/veiculos/`, payload)
    limparVeiculo()
    await carregarTudo()
    mostrarToast('Caminhão cadastrado com sucesso.')
  } catch (error) {
    mostrarToast(error.response?.data?.detail || 'Não foi possível salvar o caminhão.', 'error')
  }
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

const cadastrarFornecedor = async () => {
  const payload = {
    nome: (novoFornecedor.value.nome || '').trim(),
    telefone: (novoFornecedor.value.telefone || '').trim(),
    cep: (novoFornecedor.value.cep || '').trim(),
    logradouro: (novoFornecedor.value.logradouro || '').trim(),
    numero: (novoFornecedor.value.numero || '').trim(),
    complemento: (novoFornecedor.value.complemento || '').trim(),
    bairro: (novoFornecedor.value.bairro || '').trim(),
    cidade: (novoFornecedor.value.cidade || '').trim(),
    uf: (novoFornecedor.value.uf || '').trim(),
    endereco: (novoFornecedor.value.endereco || '').trim(),
    marca: (novoFornecedor.value.marca || '').trim(),
    observacoes: (novoFornecedor.value.observacoes || '').trim(),
  }

  if (!payload.nome || !payload.cep || !payload.cidade || !payload.marca) {
    mostrarToast('Nome, CEP, cidade e marca do fornecedor são obrigatórios.', 'error')
    return
  }

  try {
    if (fornecedorEditandoId.value) {
      await axios.put(`${API_URL}/fornecedores/${fornecedorEditandoId.value}`, payload)
      limparFornecedor()
      await carregarTudo()
      mostrarToast('Fornecedor atualizado com sucesso.')
      return
    }

    await axios.post(`${API_URL}/fornecedores/`, payload)
    limparFornecedor()
    await carregarTudo()
    mostrarToast('Fornecedor cadastrado com sucesso.')
  } catch (error) {
    mostrarToast(error.response?.data?.detail || 'Não foi possível salvar o fornecedor.', 'error')
  }
}

const cadastrarPrestadorServico = async () => {
  const payload = {
    nome: (novoPrestadorServico.value.nome || '').trim(),
    telefone: (novoPrestadorServico.value.telefone || '').trim(),
    cep: (novoPrestadorServico.value.cep || '').trim(),
    logradouro: (novoPrestadorServico.value.logradouro || '').trim(),
    numero: (novoPrestadorServico.value.numero || '').trim(),
    complemento: (novoPrestadorServico.value.complemento || '').trim(),
    bairro: (novoPrestadorServico.value.bairro || '').trim(),
    cidade: (novoPrestadorServico.value.cidade || '').trim(),
    uf: (novoPrestadorServico.value.uf || '').trim(),
    endereco: (novoPrestadorServico.value.endereco || '').trim(),
    tipo: (novoPrestadorServico.value.tipo || '').trim(),
    observacoes: (novoPrestadorServico.value.observacoes || '').trim(),
  }

  if (!payload.nome || !payload.cep || !payload.cidade || !payload.tipo) {
    mostrarToast('Nome, CEP, cidade e tipo do prestador são obrigatórios.', 'error')
    return
  }

  try {
    if (prestadorEditandoId.value) {
      await axios.put(`${API_URL}/prestadores-servicos/${prestadorEditandoId.value}`, payload)
      limparPrestadorServico()
      await carregarTudo()
      mostrarToast('Prestador atualizado com sucesso.')
      return
    }

    await axios.post(`${API_URL}/prestadores-servicos/`, payload)
    limparPrestadorServico()
    await carregarTudo()
    mostrarToast('Prestador cadastrado com sucesso.')
  } catch (error) {
    mostrarToast(error.response?.data?.detail || 'Não foi possível salvar o prestador.', 'error')
  }
}

const buscarCepEmpresa = async () => {
  const cep = novaEmpresa.value.cep.replace(/\D/g, '')
  if (cep.length !== 8) {
    erro.value = 'Informe um CEP com 8 dígitos.'
    return
  }

  erro.value = ''
  const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`)
  const dados = await response.json()

  if (dados.erro) {
    erro.value = 'CEP não encontrado.'
    return
  }

  novaEmpresa.value.cep = dados.cep || novaEmpresa.value.cep
  novaEmpresa.value.logradouro = dados.logradouro || ''
  novaEmpresa.value.complemento = dados.complemento || ''
  novaEmpresa.value.bairro = dados.bairro || ''
  novaEmpresa.value.cidade = dados.localidade || ''
  novaEmpresa.value.uf = dados.uf || ''
}

const buscarCepFornecedor = async () => {
  const cep = (novoFornecedor.value.cep || '').replace(/\D/g, '')
  if (cep.length !== 8) {
    erro.value = 'Informe um CEP com 8 dígitos.'
    return
  }

  erro.value = ''
  const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`)
  const dados = await response.json()

  if (dados.erro) {
    erro.value = 'CEP não encontrado.'
    return
  }

  novoFornecedor.value.cep = dados.cep || novoFornecedor.value.cep
  novoFornecedor.value.logradouro = dados.logradouro || ''
  novoFornecedor.value.complemento = dados.complemento || ''
  novoFornecedor.value.bairro = dados.bairro || ''
  novoFornecedor.value.cidade = dados.localidade || ''
  novoFornecedor.value.uf = dados.uf || ''
}

const buscarCepPrestadorServico = async () => {
  const cep = (novoPrestadorServico.value.cep || '').replace(/\D/g, '')
  if (cep.length !== 8) {
    erro.value = 'Informe um CEP com 8 dígitos.'
    return
  }

  erro.value = ''
  const response = await fetch(`https://viacep.com.br/ws/${cep}/json/`)
  const dados = await response.json()

  if (dados.erro) {
    erro.value = 'CEP não encontrado.'
    return
  }

  novoPrestadorServico.value.cep = dados.cep || novoPrestadorServico.value.cep
  novoPrestadorServico.value.logradouro = dados.logradouro || ''
  novoPrestadorServico.value.complemento = dados.complemento || ''
  novoPrestadorServico.value.bairro = dados.bairro || ''
  novoPrestadorServico.value.cidade = dados.localidade || ''
  novoPrestadorServico.value.uf = dados.uf || ''
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
  abrirPagina('fretes')
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
    mostrarToast('Este status não existe para este frete.', 'error')
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

  await salvarComFeedback('Caminhão marcado como indisponível.', async () => {
    await axios.put(`${API_URL}/veiculos/${veiculoIndisponibilidadeAberto.value.id}`, {
      ativo: false,
      motivo_indisponibilidade: motivo,
    })
    fecharIndisponibilidadeVeiculo()
    await carregarTudo()
  })
}

const liberarVeiculo = async (veiculo) => {
  await salvarComFeedback('Caminhão liberado para uso.', async () => {
    await axios.put(`${API_URL}/veiculos/${veiculo.id}`, {
      ativo: true,
      motivo_indisponibilidade: '',
    })
    await carregarTudo()
  })
}

const salvarObservacaoEstadoVeiculo = async (veiculo) => {
  if (!veiculo?.id) return
  await salvarComFeedback('Estado do caminhão salvo.', async () => {
    await axios.put(`${API_URL}/veiculos/${veiculo.id}`, {
      observacao_estado: (veiculo.observacao_estado || '').trim(),
    })
    await carregarTudo()
  })
}

const excluirEmpresa = async (id) => {
  await axios.delete(`${API_URL}/empresas/${id}`)
  await carregarTudo()
}

const excluirFornecedor = async (id) => {
  await axios.delete(`${API_URL}/fornecedores/${id}`)
  await carregarTudo()
}

const excluirPrestadorServico = async (id) => {
  await axios.delete(`${API_URL}/prestadores-servicos/${id}`)
  await carregarTudo()
}

const checklistTemApontamento = (checklist) => {
  return itensChecklistCaminhao.some((item) => checklist?.[item.chave] === false)
}

const checklistCompleto = computed(() => itensChecklistCaminhao.every((item) => checklistResposta.value[item.chave] !== null))
const checklistRespostaTemApontamento = computed(() => checklistTemApontamento(checklistResposta.value))
const checklistPublicoTemApontamento = computed(() => checklistTemApontamento(checklistPublico.value))

const carregarChecklistPublico = async () => {
  checklistCarregando.value = true
  checklistErro.value = ''
  try {
    const resposta = await axios.get(`${API_URL}/checklists/${checklistToken.value}`)
    checklistPublico.value = resposta.data
    checklistResposta.value = {
      tacografo: resposta.data.confirmado ? Boolean(resposta.data.tacografo) : null,
      pneus: resposta.data.confirmado ? Boolean(resposta.data.pneus) : null,
      oleo: resposta.data.confirmado ? Boolean(resposta.data.oleo) : null,
      avarias_externas: resposta.data.confirmado ? Boolean(resposta.data.avarias_externas) : null,
      avarias_internas: resposta.data.confirmado ? Boolean(resposta.data.avarias_internas) : null,
      observacoes: resposta.data.observacoes || '',
    }
    if (resposta.data.confirmado) {
      checklistSucesso.value = 'Checklist já confirmado.'
    }
  } catch (error) {
    checklistErro.value = 'Checklist não encontrado ou API indisponível.'
  } finally {
    checklistCarregando.value = false
  }
}

const confirmarChecklistPublico = async () => {
  checklistErro.value = ''
  checklistSucesso.value = ''

  if (!checklistCompleto.value) {
    checklistErro.value = 'Selecione OK ou Problema em todos os itens antes de confirmar.'
    return
  }

  if (checklistRespostaTemApontamento.value && !checklistResposta.value.observacoes.trim()) {
    checklistErro.value = 'Informe uma observação para o item com problema.'
    return
  }

  checklistSalvando.value = true
  try {
    const resposta = await axios.put(`${API_URL}/checklists/${checklistToken.value}`, checklistResposta.value)
    checklistPublico.value = resposta.data
    checklistSucesso.value = 'Checklist confirmado com sucesso.'
  } catch (error) {
    checklistErro.value = 'Não foi possível confirmar o checklist.'
  } finally {
    checklistSalvando.value = false
  }
}

const linkChecklistFrete = (frete) => {
  if (!frete.checklist_token) return ''
  return `${window.location.origin}/checklist/${frete.checklist_token}`
}

const checklistStatusFrete = (frete) => {
  if (!frete.checklist_confirmado) return 'Checklist pendente'
  return checklistTemApontamento({
    tacografo: frete.checklist_tacografo,
    pneus: frete.checklist_pneus,
    oleo: frete.checklist_oleo,
    avarias_externas: frete.checklist_avarias_externas,
    avarias_internas: frete.checklist_avarias_internas,
  })
    ? 'Checklist com apontamento'
    : 'Checklist ok'
}

const classeChecklistFrete = (frete) => {
  if (!frete.checklist_confirmado) return 'pending'
  return checklistStatusFrete(frete) === 'Checklist com apontamento' ? 'issue' : 'confirmed'
}

const dataHoraChecklistFrete = (frete) => {
  if (!frete.checklist_confirmado_em) return ''
  return new Date(frete.checklist_confirmado_em).toLocaleString('pt-BR', {
    dateStyle: 'short',
    timeStyle: 'short',
  })
}

const checklistCaminhaoMensagem = (frete, veiculo) => {
  const tipo = veiculo?.tipo || frete.tipo_caminhao_necessario || 'caminhão'
  const placa = veiculo?.placa || placaVeiculo(frete.veiculo_id)
  const link = linkChecklistFrete(frete)

  return [
    `Checklist caminhão ${tipo} - placa ${placa}`,
    'Confirme a vistoria pelo link:',
    link || 'Link do checklist ainda não gerado. Atualize o frete e copie a mensagem novamente.',
  ].join('\n')
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
    '',
    checklistCaminhaoMensagem(frete, veiculo),
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
    mostrarToast('Não há fretes concluídos neste filtro.', 'error')
    return
  }

  const confirmou = window.confirm(`Você deseja excluir todos os ${total} fretes concluídos deste filtro?`)
  if (!confirmou) return

  await salvarComFeedback('Fretes concluídos excluídos com sucesso.', async () => {
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
  return empresa ? enderecoEmpresa(empresa) : 'Endereço não cadastrado'
}

const pontosMensagemFrete = (frete) => {
  const adicionais = (frete.empresas_coleta || '')
    .split(',')
    .map((ponto) => ponto.trim())
    .filter(Boolean)

  return [frete.origem, ...adicionais, frete.destino].filter(Boolean)
}

const viewState = reactive({
  API_URL,
  tiposVeiculo,
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
  statusFiltroFrete,
  router,
  route,
  paginaPorRota,
  rotaPorPagina,
  carregando,
  erro,
  aba,
  cadastroAtivo,
  motoristaAberto,
  motoristas,
  motoristasAlocacao,
  veiculos,
  empresas,
  fornecedores,
  prestadoresServicos,
  fretes,
  filtroDataInicioFretes,
  filtroDataFimFretes,
  filtroStatus,
  filtroClienteFretes,
  filtroPendenciasAntigas,
  filtroConcluidos,
  filtroClienteConcluidos,
  dataInicioConcluidos,
  dataFimConcluidos,
  buscaOrigemFrete,
  buscaEmpresaColeta,
  buscaDestinoFrete,
  buscaMotoristasCadastro,
  buscaVeiculosCadastro,
  buscaEmpresasCadastro,
  toast,
  freteArrastandoId,
  statusDestinoAtivo,
  freteAbertoId,
  menuStatusFrete,
  filtroSituacaoVeiculo,
  filtroTipoVeiculo,
  veiculoIndisponibilidadeAberto,
  motivoIndisponibilidadeVeiculo,
  motoristaEditandoId,
  veiculoEditandoId,
  empresaEditandoId,
  fornecedorEditandoId,
  prestadorEditandoId,
  freteEditandoId,
  abaRetornoEdicaoFrete,
  sidebarRecolhida,
  menuMobileAberto,
  avisoPendenciasMostrado,
  checklistToken,
  modoChecklist,
  checklistCarregando,
  checklistSalvando,
  checklistErro,
  checklistSucesso,
  checklistPublico,
  checklistResposta,
  itensChecklistCaminhao,
  novoMotorista,
  novoVeiculo,
  novaEmpresa,
  novoFornecedor,
  tiposPrestadorServico,
  novoPrestadorServico,
  criarFormularioFreteVazio,
  novoFrete,
  paginas,
  paginaAtual,
  navegarParaPagina,
  selecionarCadastroAtivo,
  sincronizarRotaComEstado,
  abrirPagina,
  carregarTudo,
  statusEhConcluido,
  statusEhPontoAdicional,
  statusConfereFiltroFrete,
  freteEhRetorno,
  dataLocal,
  hojeLocal,
  diasAbertoFrete,
  freteEstaAtrasado,
  textoAtrasoFrete,
  dataConferePeriodoFretes,
  fretesFiltrados,
  fretesAtrasados,
  maiorAtrasoDias,
  ativarFiltroPendenciasAntigas,
  limparFiltroPendenciasAntigas,
  statusVisualFrete,
  classeStatusVisualFrete,
  totais,
  fretesEmAberto,
  fretesAbertosPorVeiculo,
  fretesAbertosPorMotorista,
  situacaoVeiculo,
  classeSituacaoVeiculo,
  fretesUsoVeiculo,
  situacaoMotorista,
  classeSituacaoMotorista,
  fretesUsoMotorista,
  veiculosFiltrados,
  totaisVeiculos,
  fretesPorData,
  empresasColetaDisponiveis,
  buscarEmpresasPorTermo,
  empresasOrigemDisponiveis,
  empresasDestinoDisponiveis,
  fretesConcluidos,
  fretesConcluidosFiltrados,
  totalConcluido,
  pontosAdicionaisFrete,
  historicoFretesMotorista,
  empresasPorNome,
  empresasClientes,
  normalizarTextoBusca,
  motoristasCadastroFiltrados,
  veiculosCadastroFiltrados,
  empresasCadastroFiltradas,
  nomeMotorista,
  telefoneMotorista,
  placaVeiculo,
  veiculoPorId,
  pontosColetaFrete,
  statusDisponiveisFrete,
  colunasKanban,
  fretesPorStatusKanban,
  freteDetalhe,
  rotuloStatusFrete,
  classeStatusKanban,
  subtituloStatusKanban,
  abrirFreteDetalhe,
  fecharFreteDetalhe,
  rotaCompactaFrete,
  horarioFrete,
  abrirMenuStatusFrete,
  fecharMenuStatusFrete,
  moverFreteParaStatus,
  resumoStatusEdscha,
  linhaAtualizacaoEdscha,
  gerarAtualizacaoEdscha,
  copiarAtualizacaoEdscha,
  normalizarAlocacao,
  apenasDigitos,
  formatarCpf,
  limparRg,
  formatarRg,
  cpfValido,
  rgValido,
  aplicarMascaraCpfMotorista,
  aplicarMascaraRgMotorista,
  mostrarToast,
  salvarComFeedback,
  limparMotorista,
  limparVeiculo,
  limparEmpresa,
  limparFornecedor,
  limparPrestadorServico,
  limparFormularioFrete,
  abrirNovoFrete,
  cancelarEdicaoFrete,
  editarFrete,
  editarMotorista,
  editarVeiculo,
  editarEmpresa,
  editarFornecedor,
  editarPrestadorServico,
  cadastrarMotorista,
  cadastrarVeiculo,
  cadastrarEmpresa,
  cadastrarFornecedor,
  cadastrarPrestadorServico,
  buscarCepEmpresa,
  buscarCepFornecedor,
  buscarCepPrestadorServico,
  payloadFormularioFrete,
  cadastrarFrete,
  adicionarEmpresaColeta,
  selecionarOrigemFrete,
  selecionarDestinoFrete,
  limparOrigemFrete,
  limparDestinoFrete,
  removerEmpresaColeta,
  salvarAlocacao,
  salvarEscalaAutomaticamente,
  iniciarArrastoFrete,
  encerrarArrastoFrete,
  soltarFreteEmStatus,
  valorFretePayload,
  salvarValorFrete,
  salvarValoresConcluidosFiltrados,
  salvarDocumentosFrete,
  salvarNotaFiscalFrete,
  valorPreenchido,
  textoPreenchido,
  salvarValorPreenchidoFrete,
  salvarDocumentoPreenchidoFrete,
  salvarFechamentoFrete,
  excluirFrete,
  excluirMotorista,
  excluirVeiculo,
  abrirIndisponibilidadeVeiculo,
  fecharIndisponibilidadeVeiculo,
  confirmarIndisponibilidadeVeiculo,
  liberarVeiculo,
  salvarObservacaoEstadoVeiculo,
  excluirEmpresa,
  excluirFornecedor,
  excluirPrestadorServico,
  checklistTemApontamento,
  checklistCompleto,
  checklistRespostaTemApontamento,
  checklistPublicoTemApontamento,
  carregarChecklistPublico,
  confirmarChecklistPublico,
  linkChecklistFrete,
  checklistStatusFrete,
  classeChecklistFrete,
  dataHoraChecklistFrete,
  checklistCaminhaoMensagem,
  mensagemWhatsApp,
  abrirWhatsApp,
  copiarMensagem,
  formatarData,
  formatarMoeda,
  periodoExportacaoConcluidos,
  exportarConcluidos,
  exportarHistoricoMotoristas,
  excluirConcluidosFiltrados,
  enderecoEmpresa,
  empresaPorNome,
  enderecoPorNomeEmpresa,
  pontosMensagemFrete,
  logoAcelera,
})

watch(checklistToken, (token) => {
  checklistErro.value = ''
  checklistSucesso.value = ''
  checklistPublico.value = null
  checklistResposta.value = respostaChecklistVazia()

  if (!token) return
  carregarChecklistPublico()
}, { immediate: true })

watch(() => [route.path, route.query.cadastro, modoChecklist.value], sincronizarRotaComEstado, { immediate: true })

watch(modoChecklist, (emChecklist, estavaEmChecklist) => {
  if (!emChecklist && estavaEmChecklist) {
    carregarTudo()
  }
})

onMounted(() => {
  if (!modoChecklist.value) carregarTudo()
})
</script>

<template>
  <main v-if="modoChecklist" class="checklist-public">
    <ChecklistPublicView :state="viewState" />
  </main>

  <main v-else class="app-shell" :class="{ 'sidebar-collapsed': sidebarRecolhida }">
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

      <nav class="sidebar-nav" aria-label="Navegação principal">
        <button title="Fretes" :class="{ active: aba === 'fretes' }" type="button" @click="abrirPagina('fretes')">
          <span class="nav-icon"><img :src="iconFretes" alt="" /></span>
          <span><strong>Fretes</strong><small>FRETES</small></span>
        </button>
        <button title="Concluídos" :class="{ active: aba === 'concluidos' }" type="button" @click="abrirPagina('concluidos')">
          <span class="nav-icon"><img :src="iconConcluidos" alt="" /></span>
          <span><strong>Concluídos</strong><small>CONCLUÍDOS</small></span>
        </button>
        <button title="Caminhões" :class="{ active: aba === 'caminhoes' }" type="button" @click="abrirPagina('caminhoes')">
          <span class="nav-icon"><img :src="iconCaminhao" alt="" /></span>
          <span><strong>Caminhões</strong><small>CAMINHÃO</small></span>
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
        <button title="Fornecedores" :class="{ active: aba === 'fornecedores' }" type="button" @click="abrirPagina('fornecedores')">
          <span class="nav-icon"><img :src="iconFornecedores" alt="" /></span>
          <span><strong>Fornecedores</strong><small>FORNECEDOR</small></span>
        </button>
        <button title="Prestadores" :class="{ active: aba === 'prestadores-servicos' }" type="button" @click="abrirPagina('prestadores-servicos')">
          <span class="nav-icon"><img :src="iconPrestadores" alt="" /></span>
          <span><strong>Prestadores</strong><small>SERVIÇOS</small></span>
        </button>
      </nav>

      <button
        class="sidebar-collapse"
        type="button"
        :title="sidebarRecolhida ? 'Expandir menu' : 'Recolher menu'"
        :aria-label="sidebarRecolhida ? 'Expandir menu' : 'Recolher menu'"
        @click="sidebarRecolhida = !sidebarRecolhida"
      >
        <span class="hamburger-lines" aria-hidden="true"><i></i><i></i><i></i></span>
      </button>
    </aside>

    <button v-if="menuMobileAberto" class="sidebar-scrim" type="button" aria-label="Fechar menu" @click="menuMobileAberto = false"></button>

    <div class="content-shell">
      <header class="topbar">
        <button class="mobile-menu-button" type="button" aria-label="Abrir menu" @click="menuMobileAberto = true">
          <span class="hamburger-lines" aria-hidden="true"><i></i><i></i><i></i></span>
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

      <RouterView v-slot="{ Component }">
        <component :is="Component" :state="viewState" />
      </RouterView>
    </div>
  </main>
</template>
