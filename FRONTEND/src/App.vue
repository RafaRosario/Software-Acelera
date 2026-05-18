<script setup>
import { computed, onMounted, ref } from 'vue'
import axios from 'axios'

const API_URL = 'http://127.0.0.1:8000'
const statusFiltroFrete = [
  'Aguardando horario',
  'Em andamento',
  'concluido',
  'Cancelada',
]
const tiposVeiculo = ['Motoboy', 'Fiorino', 'Iveco', '3/4', 'Toco', 'Truk', 'Carreta']

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
const filtroData = ref(new Date().toISOString().slice(0, 10))
const filtroStatus = ref('Todos')
const filtroClienteFretes = ref('Todos')
const filtroConcluidos = ref('todos')
const filtroClienteConcluidos = ref('Todos')
const dataInicioConcluidos = ref('')
const dataFimConcluidos = ref('')
const buscaEmpresaColeta = ref('')
const toast = ref(null)

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
const novoFrete = ref({
  cliente: '',
  nota_fiscal: '',
  data_coleta: new Date().toISOString().slice(0, 10),
  horario_coleta: '',
  origem: '',
  empresas_coleta: [],
  destino: '',
  tipo_caminhao_necessario: 'Truk',
  retorno: false,
  status: 'Aguardando horario',
  valor_servico: null,
  observacoes: '',
  motorista_id: '',
  veiculo_id: '',
})

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

const fretesFiltrados = computed(() => {
  return fretes.value.filter((frete) => {
    const dataConfere = !filtroData.value || frete.data_coleta === filtroData.value
    const clienteConfere = filtroClienteFretes.value === 'Todos' || frete.cliente === filtroClienteFretes.value
    const statusConfere =
      filtroStatus.value === 'Todos' ||
      statusVisualFrete(frete.status) === filtroStatus.value ||
      (filtroStatus.value === 'concluido' && frete.status === 'Concluida')
    return dataConfere && clienteConfere && statusConfere
  })
})

const statusEhConcluido = (status) => status === 'concluido' || status === 'Concluida'
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
  retorno: fretesPorData.value.filter((frete) => frete.retorno).length,
}))

const fretesPorData = computed(() => {
  return fretes.value.filter((frete) => {
    const dataConfere = !filtroData.value || frete.data_coleta === filtroData.value
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

const fretesConcluidos = computed(() => {
  return fretes.value.filter((frete) => statusEhConcluido(frete.status))
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
  return fretesConcluidosFiltrados.value.reduce((total, frete) => total + Number(frete.valor_servico || 0), 0)
})

const maiorViagensSemana = computed(() => {
  return Math.max(0, ...motoristasAlocacao.value.map((motorista) => motorista.viagens_semana || 0))
})

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
  const adicionais = (frete.empresas_coleta || '')
    .split(',')
    .map((ponto) => ponto.trim())
    .filter(Boolean)
  return 1 + adicionais.length
}

const statusDisponiveisFrete = (frete) => {
  const status = ['Aguardando horario', 'A caminho P1']
  const totalPontos = pontosColetaFrete(frete)

  for (let indice = 1; indice <= totalPontos; indice += 1) {
    status.push(`coletado P${indice}`)
  }

  if (frete.retorno) status.push('retornando')
  status.push('concluido')
  status.push('Cancelada')

  if (frete.status && !status.includes(frete.status)) {
    status.unshift(frete.status)
  }

  return status
}

const resumoStatusEdscha = (frete) => {
  if (frete.status === 'Aguardando horario') return 'aguardando horario'
  if (frete.status === 'A caminho P1') return `a caminho ${frete.origem}`
  if (frete.status?.startsWith('coletado P')) return `${frete.status}, em rota`
  if (frete.status === 'retornando') return 'retornando'
  if (statusEhConcluido(frete.status)) return 'concluido'
  if (frete.status === 'Cancelada') return 'cancelado'
  return statusVisualFrete(frete.status).toLowerCase()
}

const linhaAtualizacaoEdscha = (frete) => {
  const pontos = pontosMensagemFrete(frete)
  const rota = pontos.join(' x ')
  return `${frete.tipo_caminhao_necessario} - ${rota}, ${resumoStatusEdscha(frete)}`
}

const gerarAtualizacaoEdscha = () => {
  const fretesAtualizacao = fretesFiltrados.value.filter((frete) => !statusEhConcluido(frete.status) && frete.status !== 'Cancelada')

  if (fretesAtualizacao.length === 0) {
    mostrarToast('Nao ha fretes em aberto neste filtro.', 'error')
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

const classeCargaMotorista = (motorista) => {
  if (!maiorViagensSemana.value || motorista.viagens_semana === 0) return 'low'
  if (motorista.viagens_semana === maiorViagensSemana.value) return 'high'
  return 'medium'
}

const normalizarAlocacao = (frete) => ({
  motorista_id: frete.motorista_id ? Number(frete.motorista_id) : null,
  veiculo_id: frete.veiculo_id ? Number(frete.veiculo_id) : null,
  status: frete.status,
})

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

const cadastrarMotorista = async () => {
  await axios.post(`${API_URL}/motoristas/`, novoMotorista.value)
  novoMotorista.value = { nome: '', telefone: '', rg: '', cpf: '', cnh: '', observacoes: '' }
  await carregarTudo()
}

const cadastrarVeiculo = async () => {
  await axios.post(`${API_URL}/veiculos/`, novoVeiculo.value)
  novoVeiculo.value = { placa: '', tipo: 'Truk', observacoes: '' }
  await carregarTudo()
}

const cadastrarEmpresa = async () => {
  await axios.post(`${API_URL}/empresas/`, novaEmpresa.value)
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

const cadastrarFrete = async () => {
  const payload = {
    ...novoFrete.value,
    empresas_coleta: Array.isArray(novoFrete.value.empresas_coleta)
      ? novoFrete.value.empresas_coleta.join(', ')
      : novoFrete.value.empresas_coleta,
    motorista_id: novoFrete.value.motorista_id ? Number(novoFrete.value.motorista_id) : null,
    veiculo_id: novoFrete.value.veiculo_id ? Number(novoFrete.value.veiculo_id) : null,
    valor_servico:
      novoFrete.value.valor_servico === '' || novoFrete.value.valor_servico === null
        ? null
        : Number(novoFrete.value.valor_servico),
  }
  await axios.post(`${API_URL}/fretes/`, payload)
  novoFrete.value = {
    cliente: '',
    nota_fiscal: '',
    data_coleta: filtroData.value || new Date().toISOString().slice(0, 10),
    horario_coleta: '',
    origem: '',
    empresas_coleta: [],
    destino: '',
    tipo_caminhao_necessario: 'Truk',
    retorno: false,
    status: 'Aguardando horario',
    valor_servico: null,
    observacoes: '',
    motorista_id: '',
    veiculo_id: '',
  }
  aba.value = 'fretes'
  await carregarTudo()
}

const adicionarEmpresaColeta = (empresa) => {
  if (!novoFrete.value.empresas_coleta.includes(empresa.nome)) {
    novoFrete.value.empresas_coleta.push(empresa.nome)
  }
  buscaEmpresaColeta.value = ''
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

const salvarValorFrete = async (frete) => {
  await salvarComFeedback('Valor salvo com sucesso.', async () => {
    await axios.put(`${API_URL}/fretes/${frete.id}/valor`, {
      valor_servico: frete.valor_servico === '' || frete.valor_servico === null ? null : Number(frete.valor_servico),
    })
    await carregarTudo()
  })
}

const salvarDocumentosFrete = async (frete) => {
  await salvarComFeedback('CTE/OC salvos com sucesso.', async () => {
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
  <main class="app-shell">
    <div v-if="toast" class="toast" :class="toast.tipo">
      {{ toast.mensagem }}
    </div>

    <header class="topbar">
      <div>
        <p class="eyebrow">Acelera Transportes</p>
        <h1>Controle de fretes</h1>
      </div>
      <button class="ghost-button" type="button" @click="carregarTudo">
        Atualizar
      </button>
    </header>

    <section v-if="erro" class="alert">{{ erro }}</section>

    <div class="nav-groups">
      <nav class="tabs" aria-label="Visualizacao e operacao">
        <button :class="{ active: aba === 'fretes' }" type="button" @click="aba = 'fretes'">Fretes</button>
        <button :class="{ active: aba === 'concluidos' }" type="button" @click="aba = 'concluidos'">Concluidos</button>
        <button :class="{ active: aba === 'relatorios' }" type="button" @click="aba = 'relatorios'">Motoristas</button>
      </nav>

      <nav class="tabs create-tabs" aria-label="Criacao e cadastros">
        <button :class="{ active: aba === 'novo-frete' }" type="button" @click="aba = 'novo-frete'">Novo frete</button>
        <button :class="{ active: aba === 'cadastros' }" type="button" @click="aba = 'cadastros'; cadastroAtivo = 'motoristas'">Cadastros</button>
      </nav>
    </div>

    <section v-if="aba === 'fretes'" class="workspace">
      <div class="section-head">
        <div>
          <h2>Escala diaria</h2>
          <p>Fretes cadastrados, alocacao e status da viagem.</p>
        </div>
        <button class="update-button" type="button" @click="copiarAtualizacaoEdscha">
          Copiar atualizacao Edscha
        </button>
        <label class="field compact">
          Data
          <input v-model="filtroData" type="date" />
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
            <option v-for="status in statusFiltroFrete" :key="status" :value="status">{{ status }}</option>
          </select>
        </label>
      </div>

      <div class="metrics">
        <div><strong>{{ totais.aguardando }}</strong><span>Aguardando horario</span></div>
        <div><strong>{{ totais.andamento }}</strong><span>Em andamento</span></div>
        <div><strong>{{ totais.concluidas }}</strong><span>Concluidas</span></div>
        <div><strong>{{ totais.retorno }}</strong><span>Com retorno</span></div>
      </div>

      <div class="freight-list">
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
          <p>Fechamento financeiro dos servicos ja realizados.</p>
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

          <div class="value-row">
            <label class="field">
              Nota fiscal
              <input v-model="frete.nota_fiscal" placeholder="Numero da nota fiscal" />
            </label>
            <strong>{{ frete.nota_fiscal || 'Sem nota' }}</strong>
            <button class="secondary" type="button" @click="salvarNotaFiscalFrete(frete)">Salvar NF</button>
          </div>

          <div class="value-row">
            <label class="field">
              CTE
              <input v-model="frete.cte" placeholder="Numero do CTE" />
            </label>
            <label class="field">
              OC
              <input v-model="frete.oc" placeholder="Numero da OC" />
            </label>
            <button class="secondary" type="button" @click="salvarDocumentosFrete(frete)">Salvar CTE/OC</button>
          </div>

          <div class="value-row">
            <label class="field">
              Valor do servico
              <input v-model="frete.valor_servico" type="number" min="0" step="0.01" placeholder="0,00" />
            </label>
            <strong>{{ formatarMoeda(frete.valor_servico) }}</strong>
            <button type="button" @click="salvarValorFrete(frete)">Salvar valor</button>
          </div>
        </article>

        <p v-if="fretesConcluidosFiltrados.length === 0" class="empty">Nenhum frete concluido para este periodo.</p>
      </div>
    </section>

    <section v-if="aba === 'novo-frete'" class="workspace">
      <div class="section-head">
        <div>
          <h2>Cadastrar frete</h2>
          <p>Use para fretes recebidos por planilha ou WhatsApp.</p>
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
        <label class="field">
          Origem
          <select v-model="novoFrete.origem" required>
            <option value="" disabled></option>
            <option v-for="empresa in empresas" :key="empresa.id" :value="empresa.nome">{{ empresa.nome }}</option>
          </select>
        </label>
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
        <label class="field">
          Destino
          <select v-model="novoFrete.destino" required>
            <option value="" disabled></option>
            <option v-for="empresa in empresas" :key="empresa.id" :value="empresa.nome">{{ empresa.nome }}</option>
          </select>
        </label>
        <label class="field">
          Tipo de veículo requisitado
          <select v-model="novoFrete.tipo_caminhao_necessario" required>
            <option v-for="tipo in tiposVeiculo" :key="tipo" :value="tipo">{{ tipo }}</option>
          </select>
        </label>
        <label class="field">Valor do servico<input v-model="novoFrete.valor_servico" type="number" min="0" step="0.01" placeholder="Opcional" /></label>
        <label class="check-field"><input v-model="novoFrete.retorno" type="checkbox" /> Tem retorno</label>
        <label class="field">Motorista<select v-model="novoFrete.motorista_id" required><option value="" disabled></option><option v-for="motorista in motoristas" :key="motorista.id" :value="motorista.id">{{ motorista.nome }}</option></select></label>
        <label class="field">Caminhao<select v-model="novoFrete.veiculo_id" required><option value="" disabled></option><option v-for="veiculo in veiculos" :key="veiculo.id" :value="veiculo.id">{{ veiculo.placa }} - {{ veiculo.tipo }}</option></select></label>
        <label class="field wide">Observacoes<textarea v-model="novoFrete.observacoes" rows="3"></textarea></label>
        <button type="submit">Cadastrar frete</button>
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
        <button :class="{ active: cadastroAtivo === 'veiculos' }" type="button" @click="cadastroAtivo = 'veiculos'">Caminhoes</button>
        <button :class="{ active: cadastroAtivo === 'empresas' }" type="button" @click="cadastroAtivo = 'empresas'">Empresas</button>
      </div>

      <div v-if="cadastroAtivo === 'motoristas'">
        <h2>Motoristas</h2>
        <form class="stack-form" @submit.prevent="cadastrarMotorista">
          <input v-model="novoMotorista.nome" placeholder="Nome" required />
          <input v-model="novoMotorista.telefone" placeholder="Telefone/WhatsApp" required />
          <input v-model="novoMotorista.rg" placeholder="RG" required />
          <input v-model="novoMotorista.cpf" placeholder="CPF" required />
          <textarea v-model="novoMotorista.observacoes" placeholder="Observacoes" rows="3"></textarea>
          <button type="submit">Cadastrar motorista</button>
        </form>
        <ul class="simple-list">
          <li v-for="motorista in motoristas" :key="motorista.id">
            <span>
              {{ motorista.nome }}
              <small>{{ motorista.telefone }}</small>
              <small v-if="motorista.observacoes" class="registry-note">Obs: {{ motorista.observacoes }}</small>
            </span>
            <button class="danger compact-button" type="button" @click="excluirMotorista(motorista.id)">Excluir</button>
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
          <button type="submit">Cadastrar caminhao</button>
        </form>
        <ul class="simple-list">
          <li v-for="veiculo in veiculos" :key="veiculo.id">
            <span>
              {{ veiculo.placa }}
              <small>{{ veiculo.tipo }}</small>
              <small v-if="veiculo.observacoes" class="registry-note">Obs: {{ veiculo.observacoes }}</small>
            </span>
            <button class="danger compact-button" type="button" @click="excluirVeiculo(veiculo.id)">Excluir</button>
          </li>
        </ul>
      </div>

      <div v-if="cadastroAtivo === 'empresas'">
        <h2>Empresas</h2>
        <form class="stack-form" @submit.prevent="cadastrarEmpresa">
          <input v-model="novaEmpresa.nome" placeholder="Nome da empresa" required />
          <input v-model="novaEmpresa.cnpj" placeholder="CNPJ" required />
          <label class="check-field compact-check"><input v-model="novaEmpresa.cliente" type="checkbox" /> E cliente</label>
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
          <button type="submit">Cadastrar empresa</button>
        </form>
        <ul class="simple-list">
          <li v-for="empresa in empresas" :key="empresa.id">
            <span>
              {{ empresa.nome }}
              <small>{{ empresa.cnpj }} - {{ enderecoEmpresa(empresa) }}</small>
              <small v-if="empresa.cliente" class="registry-note">Cliente</small>
              <small v-if="empresa.observacoes" class="registry-note">Obs: {{ empresa.observacoes }}</small>
            </span>
            <button class="danger compact-button" type="button" @click="excluirEmpresa(empresa.id)">Excluir</button>
          </li>
        </ul>
      </div>
    </section>

    <section v-if="aba === 'relatorios'" class="workspace">
      <div class="section-head">
        <div>
          <h2>Equilibrio da semana</h2>
          <p>Cores indicam quem esta fazendo menos, medio ou mais fretes na semana.</p>
        </div>
      </div>

      <div class="driver-cards">
        <article v-for="motorista in motoristasAlocacao" :key="motorista.id" class="driver-card" :class="classeCargaMotorista(motorista)">
          <div>
            <h3>{{ motorista.nome }}</h3>
            <p v-if="motorista.observacoes">{{ motorista.observacoes }}</p>
          </div>
          <div class="driver-stats">
            <span><strong>{{ motorista.viagens_dia }}</strong>Hoje</span>
            <span><strong>{{ motorista.viagens_semana }}</strong>Semana</span>
          </div>
          <button class="secondary" type="button" @click="motoristaAberto = motoristaAberto === motorista.id ? null : motorista.id">
            {{ motoristaAberto === motorista.id ? 'Ocultar dados' : 'Ver dados' }}
          </button>
          <div v-if="motoristaAberto === motorista.id" class="driver-data">
            <span>Telefone: {{ motorista.telefone }}</span>
            <span>RG: {{ motorista.rg }}</span>
            <span>CPF: {{ motorista.cpf }}</span>
          </div>
        </article>
      </div>
    </section>
  </main>
</template>
