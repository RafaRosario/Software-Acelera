<script setup>
import { computed, ref, toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  buscarCepPrestadorServico,
  cadastrarPrestadorServico,
  editarPrestadorServico,
  excluirPrestadorServico,
  limparPrestadorServico,
  normalizarTextoBusca,
  novoPrestadorServico,
  prestadorEditandoId,
  prestadoresServicos,
  tiposPrestadorServico,
} = toRefs(state)

const buscaPrestador = ref('')
const filtroCidade = ref('Todos')
const filtroTipo = ref('Todos')
const formularioAberto = ref(false)

const formularioVisivel = computed(() => formularioAberto.value || Boolean(prestadorEditandoId.value))

const cidadesPrestadores = computed(() => {
  return [...new Set(prestadoresServicos.value.map((prestador) => String(prestador.cidade || '').trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

const tiposPrestadores = computed(() => {
  return [...new Set(prestadoresServicos.value.map((prestador) => String(prestador.tipo || '').trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

const rotuloTipoPrestador = (tipo) => {
  if (tipo === 'valvula') return 'Válvula'
  if (tipo === 'mecanicos') return 'Mecânicos'
  if (tipo === 'bombistas') return 'Bombistas'
  if (tipo === 'outros') return 'Outros'
  return tipo
}

const enderecoPrestador = (prestador) => {
  return prestador.endereco || [prestador.logradouro || prestador.rua, prestador.numero, prestador.bairro, prestador.cidade, prestador.uf, prestador.cep]
    .filter(Boolean)
    .join(', ')
}

const prestadoresFiltrados = computed(() => {
  const termo = normalizarTextoBusca.value(buscaPrestador.value)
  return prestadoresServicos.value.filter((prestador) => {
    const cidadeConfere = filtroCidade.value === 'Todos' || prestador.cidade === filtroCidade.value
    const tipoConfere = filtroTipo.value === 'Todos' || prestador.tipo === filtroTipo.value
    if (!cidadeConfere || !tipoConfere) return false

    if (!termo) return true
    const dados = [
      prestador.nome,
      prestador.telefone,
      prestador.cep,
      prestador.logradouro,
      prestador.numero,
      prestador.bairro,
      prestador.cidade,
      prestador.uf,
      prestador.tipo,
      prestador.observacoes,
      enderecoPrestador(prestador),
      rotuloTipoPrestador(prestador.tipo),
    ]
      .filter(Boolean)
      .join(' ')
    return normalizarTextoBusca.value(dados).includes(termo)
  })
})

const abrirFormularioPrestador = () => {
  formularioAberto.value = true
}

const alternarFormularioPrestador = () => {
  formularioAberto.value = !formularioAberto.value
}

const abrirEdicaoPrestador = (prestador) => {
  formularioAberto.value = true
  editarPrestadorServico.value(prestador)
}

const cancelarFormularioPrestador = () => {
  limparPrestadorServico.value()
  formularioAberto.value = false
}
</script>

<template>
  <section class="workspace">
    <div class="focus-directory-layout">
      <section class="focus-directory-main">
        <header class="focus-directory-main-head">
          <div class="focus-page-headline">
            <p class="focus-page-kicker">PRESTADORES</p>
            <h2>Prestadores de serviços</h2>
            <small>Cadastro de válvula, mecânico e bombista.</small>
            <span class="focus-page-count">{{ prestadoresFiltrados.length }} de {{ prestadoresServicos.length }} registros</span>
          </div>
          <div class="focus-directory-meta">
            <span class="focus-chip">{{ cidadesPrestadores.length }} cidades</span>
            <span class="focus-chip">{{ tiposPrestadores.length }} tipos</span>
            <button class="secondary compact-button" type="button" @click="abrirFormularioPrestador">Novo prestador</button>
          </div>
        </header>

        <div class="focus-directory-toolbar">
          <label class="field">
            Buscar
            <input v-model="buscaPrestador" type="search" placeholder="Nome, tipo, cidade, telefone, CEP..." />
          </label>
          <label class="field">
            Cidade
            <select v-model="filtroCidade">
              <option value="Todos">Todas</option>
              <option v-for="cidade in cidadesPrestadores" :key="cidade" :value="cidade">{{ cidade }}</option>
            </select>
          </label>
          <label class="field">
            Tipo
            <select v-model="filtroTipo">
              <option value="Todos">Todos</option>
              <option v-for="tipo in tiposPrestadores" :key="tipo" :value="tipo">{{ rotuloTipoPrestador(tipo) }}</option>
            </select>
          </label>
        </div>

        <ul class="focus-directory-cards">
          <li v-for="prestador in prestadoresFiltrados" :key="prestador.id">
            <div class="focus-directory-card-main">
              <div class="focus-directory-card-title">
                <strong>{{ prestador.nome }}</strong>
                <span class="focus-tag">{{ rotuloTipoPrestador(prestador.tipo) }}</span>
              </div>
              <small class="focus-directory-card-line">{{ prestador.cidade || 'Cidade não informada' }} | {{ prestador.telefone || 'Sem telefone' }} | {{ prestador.cep || 'Sem CEP' }}</small>
              <small class="focus-directory-card-line">{{ enderecoPrestador(prestador) || 'Endereço não informado' }}</small>
              <small v-if="prestador.observacoes" class="focus-directory-note">{{ prestador.observacoes }}</small>
            </div>
            <div class="focus-directory-card-actions">
              <button class="secondary compact-button" type="button" @click="abrirEdicaoPrestador(prestador)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirPrestadorServico(prestador.id)">Excluir</button>
            </div>
          </li>
        </ul>

        <p v-if="prestadoresFiltrados.length === 0" class="empty">Nenhum prestador encontrado.</p>
      </section>

      <aside class="focus-directory-aside" :class="{ collapsed: !formularioVisivel }">
        <div class="focus-directory-aside-head">
          <div>
            <h3>{{ prestadorEditandoId ? 'Editar prestador' : 'Cadastro rápido' }}</h3>
            <p>Formulário compacto para inclusão e ajustes.</p>
          </div>
          <button class="ghost-button compact-button" type="button" @click="alternarFormularioPrestador">
            {{ formularioVisivel ? 'Ocultar' : 'Abrir' }}
          </button>
        </div>

        <form v-if="formularioVisivel" class="stack-form compact-stack-form" @submit.prevent="cadastrarPrestadorServico">
          <input v-model="novoPrestadorServico.nome" placeholder="Nome" required />
          <input v-model="novoPrestadorServico.telefone" placeholder="Telefone" />
          <select v-model="novoPrestadorServico.tipo" required>
            <option v-for="tipo in tiposPrestadorServico" :key="tipo" :value="tipo">{{ rotuloTipoPrestador(tipo) }}</option>
          </select>
          <div class="cep-row">
            <input v-model="novoPrestadorServico.cep" placeholder="CEP" required @blur="buscarCepPrestadorServico" />
            <button class="secondary" type="button" @click="buscarCepPrestadorServico">Buscar CEP</button>
          </div>
          <input v-model="novoPrestadorServico.logradouro" placeholder="Rua / avenida" required />
          <div class="address-grid">
            <input v-model="novoPrestadorServico.numero" placeholder="Número" />
            <input v-model="novoPrestadorServico.complemento" placeholder="Complemento" />
          </div>
          <input v-model="novoPrestadorServico.bairro" placeholder="Bairro" required />
          <div class="address-grid">
            <input v-model="novoPrestadorServico.cidade" placeholder="Cidade" required />
            <input v-model="novoPrestadorServico.uf" placeholder="UF" maxlength="2" required />
          </div>
          <textarea v-model="novoPrestadorServico.observacoes" placeholder="Observações" rows="3"></textarea>
          <div class="form-actions">
            <button type="submit">{{ prestadorEditandoId ? 'Salvar prestador' : 'Cadastrar prestador' }}</button>
            <button
              v-if="prestadorEditandoId || formularioAberto"
              class="secondary"
              type="button"
              @click="cancelarFormularioPrestador"
            >
              Cancelar
            </button>
          </div>
        </form>

        <p v-else class="focus-form-hint">Clique em "Abrir" para cadastrar ou editar prestadores.</p>
      </aside>
    </div>
  </section>
</template>
