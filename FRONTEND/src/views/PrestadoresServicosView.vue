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

const cidadesPrestadores = computed(() => {
  return [...new Set(prestadoresServicos.value.map((prestador) => String(prestador.cidade || '').trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

const tiposPrestadores = computed(() => {
  return [...new Set(prestadoresServicos.value.map((prestador) => String(prestador.tipo || '').trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

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
    ]
      .filter(Boolean)
      .join(' ')
    return normalizarTextoBusca.value(dados).includes(termo)
  })
})

const enderecoPrestador = (prestador) => {
  return prestador.endereco || [prestador.logradouro || prestador.rua, prestador.numero, prestador.bairro, prestador.cidade, prestador.uf, prestador.cep].filter(Boolean).join(', ')
}

const rotuloTipoPrestador = (tipo) => {
  if (tipo === 'valvula') return 'Válvula'
  if (tipo === 'mecanicos') return 'Mecânicos'
  if (tipo === 'bombistas') return 'Bombistas'
  return tipo
}
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <div>
        <h2>Prestadores de serviços</h2>
        <p>Cadastro de válvula, mecânico e bombista.</p>
      </div>
    </div>

    <div class="registry-layout">
      <div class="registry-form-card">
        <div class="registry-card-head">
          <span>05</span>
          <div>
            <h2>Novo prestador</h2>
            <p>SERVIÇO</p>
          </div>
        </div>
        <form class="stack-form" @submit.prevent="cadastrarPrestadorServico">
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
            <button v-if="prestadorEditandoId" class="secondary" type="button" @click="limparPrestadorServico">Cancelar edição</button>
          </div>
        </form>
      </div>

      <aside class="registry-directory">
        <div class="registry-directory-head">
          <div>
            <strong>Prestadores cadastrados</strong>
            <small>{{ prestadoresFiltrados.length }} de {{ prestadoresServicos.length }} registros</small>
          </div>
        </div>

        <div class="form-grid">
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

        <ul class="simple-list registry-list">
          <li v-for="prestador in prestadoresFiltrados" :key="prestador.id">
            <span>
              {{ prestador.nome }}
              <small>{{ rotuloTipoPrestador(prestador.tipo) }} | {{ prestador.telefone || 'Sem telefone' }} | {{ prestador.cep || 'Sem CEP' }}</small>
              <small class="registry-note">{{ enderecoPrestador(prestador) }}</small>
              <small v-if="prestador.observacoes" class="registry-note">Obs: {{ prestador.observacoes }}</small>
            </span>
            <div class="registry-actions">
              <button class="secondary compact-button" type="button" @click="editarPrestadorServico(prestador)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirPrestadorServico(prestador.id)">Excluir</button>
            </div>
          </li>
        </ul>
        <p v-if="prestadoresFiltrados.length === 0" class="empty">Nenhum prestador encontrado.</p>
      </aside>
    </div>
  </section>
</template>
