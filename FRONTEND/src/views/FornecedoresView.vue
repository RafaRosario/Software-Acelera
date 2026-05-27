<script setup>
import { computed, ref, toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  buscarCepFornecedor,
  cadastrarFornecedor,
  editarFornecedor,
  excluirFornecedor,
  fornecedorEditandoId,
  fornecedores,
  limparFornecedor,
  normalizarTextoBusca,
  novoFornecedor,
} = toRefs(state)

const buscaFornecedor = ref('')
const filtroCidade = ref('Todos')
const filtroMarca = ref('Todas')
const formularioAberto = ref(false)
const marcasPadraoFornecedores = ['Iveco', 'Volskwagen', 'Mercedes', 'Amanhã', 'Safra', 'Variadas']

const formularioVisivel = computed(() => formularioAberto.value || Boolean(fornecedorEditandoId.value))

const cidadesFornecedores = computed(() => {
  return [...new Set(fornecedores.value.map((fornecedor) => String(fornecedor.cidade || '').trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

const marcasFornecedores = computed(() => {
  return [...new Set([
    ...marcasPadraoFornecedores,
    ...fornecedores.value.map((fornecedor) => String(fornecedor.marca || '').trim()).filter(Boolean),
  ])]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

const enderecoFornecedor = (fornecedor) => {
  return fornecedor.endereco || [fornecedor.logradouro, fornecedor.numero, fornecedor.bairro, fornecedor.cidade, fornecedor.uf, fornecedor.cep]
    .filter(Boolean)
    .join(', ')
}

const fornecedoresFiltrados = computed(() => {
  const termo = normalizarTextoBusca.value(buscaFornecedor.value)
  return fornecedores.value.filter((fornecedor) => {
    const cidadeConfere = filtroCidade.value === 'Todos' || fornecedor.cidade === filtroCidade.value
    const marcaConfere = filtroMarca.value === 'Todas' || fornecedor.marca === filtroMarca.value
    if (!cidadeConfere || !marcaConfere) return false

    if (!termo) return true
    const dados = [
      fornecedor.nome,
      fornecedor.telefone,
      fornecedor.cep,
      fornecedor.logradouro,
      fornecedor.numero,
      fornecedor.bairro,
      fornecedor.uf,
      fornecedor.endereco,
      fornecedor.cidade,
      fornecedor.marca,
      fornecedor.observacoes,
      enderecoFornecedor(fornecedor),
    ]
      .filter(Boolean)
      .join(' ')
    return normalizarTextoBusca.value(dados).includes(termo)
  })
})

const abrirFormularioFornecedor = () => {
  if (!novoFornecedor.value.marca) {
    novoFornecedor.value.marca = marcasPadraoFornecedores[0]
  }
  formularioAberto.value = true
}

const alternarFormularioFornecedor = () => {
  formularioAberto.value = !formularioAberto.value
}

const abrirEdicaoFornecedor = (fornecedor) => {
  formularioAberto.value = true
  editarFornecedor.value(fornecedor)
}

const cancelarFormularioFornecedor = () => {
  limparFornecedor.value()
  formularioAberto.value = false
}
</script>

<template>
  <section class="workspace">
    <div class="focus-directory-layout">
      <section class="focus-directory-main">
        <header class="focus-directory-main-head">
          <div class="focus-page-headline">
            <p class="focus-page-kicker">FORNECEDORES</p>
            <h2>Fornecedores</h2>
            <small>Lojas onde são comprados materiais para os caminhões.</small>
            <span class="focus-page-count">{{ fornecedoresFiltrados.length }} de {{ fornecedores.length }} registros</span>
          </div>
          <div class="focus-directory-meta">
            <span class="focus-chip">{{ cidadesFornecedores.length }} cidades</span>
            <span class="focus-chip">{{ marcasFornecedores.length }} marcas</span>
            <button class="secondary compact-button" type="button" @click="abrirFormularioFornecedor">Novo fornecedor</button>
          </div>
        </header>

        <div class="focus-directory-toolbar">
          <label class="field">
            Buscar
            <input v-model="buscaFornecedor" type="search" placeholder="Nome, telefone, CEP, cidade, marca..." />
          </label>
          <label class="field">
            Cidade
            <select v-model="filtroCidade">
              <option value="Todos">Todas</option>
              <option v-for="cidade in cidadesFornecedores" :key="cidade" :value="cidade">{{ cidade }}</option>
            </select>
          </label>
          <label class="field">
            Marca
            <select v-model="filtroMarca">
              <option value="Todas">Todas</option>
              <option v-for="marca in marcasFornecedores" :key="marca" :value="marca">{{ marca }}</option>
            </select>
          </label>
        </div>

        <ul class="focus-directory-cards">
          <li v-for="fornecedor in fornecedoresFiltrados" :key="fornecedor.id">
            <div class="focus-directory-card-main">
              <div class="focus-directory-card-title">
                <strong>{{ fornecedor.nome }}</strong>
                <span class="focus-tag">{{ fornecedor.marca || 'Sem marca' }}</span>
              </div>
              <small class="focus-directory-card-line">{{ fornecedor.cidade || 'Cidade não informada' }} | {{ fornecedor.telefone || 'Sem telefone' }} | {{ fornecedor.cep || 'Sem CEP' }}</small>
              <small class="focus-directory-card-line">{{ enderecoFornecedor(fornecedor) || 'Endereço não informado' }}</small>
              <small v-if="fornecedor.observacoes" class="focus-directory-note">{{ fornecedor.observacoes }}</small>
            </div>
            <div class="focus-directory-card-actions">
              <button class="secondary compact-button" type="button" @click="abrirEdicaoFornecedor(fornecedor)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirFornecedor(fornecedor.id)">Excluir</button>
            </div>
          </li>
        </ul>

        <p v-if="fornecedoresFiltrados.length === 0" class="empty">Nenhum fornecedor encontrado.</p>
      </section>

      <aside class="focus-directory-aside" :class="{ collapsed: !formularioVisivel }">
        <div class="focus-directory-aside-head">
          <div>
            <h3>{{ fornecedorEditandoId ? 'Editar fornecedor' : 'Cadastro rápido' }}</h3>
            <p>Formulário compacto para inclusão e ajustes.</p>
          </div>
          <button class="ghost-button compact-button" type="button" @click="alternarFormularioFornecedor">
            {{ formularioVisivel ? 'Ocultar' : 'Abrir' }}
          </button>
        </div>

        <form v-if="formularioVisivel" class="stack-form compact-stack-form" @submit.prevent="cadastrarFornecedor">
          <input v-model="novoFornecedor.nome" placeholder="Nome da loja" required />
          <input v-model="novoFornecedor.telefone" placeholder="Telefone" />
          <div class="cep-row">
            <input v-model="novoFornecedor.cep" placeholder="CEP" required @blur="buscarCepFornecedor" />
            <button class="secondary" type="button" @click="buscarCepFornecedor">Buscar CEP</button>
          </div>
          <input v-model="novoFornecedor.logradouro" placeholder="Rua / avenida" required />
          <div class="address-grid">
            <input v-model="novoFornecedor.numero" placeholder="Número" />
            <input v-model="novoFornecedor.complemento" placeholder="Complemento" />
          </div>
          <input v-model="novoFornecedor.bairro" placeholder="Bairro" required />
          <div class="address-grid">
            <input v-model="novoFornecedor.cidade" placeholder="Cidade" required />
            <input v-model="novoFornecedor.uf" placeholder="UF" maxlength="2" required />
          </div>
          <select v-model="novoFornecedor.marca" required>
            <option v-for="marca in marcasFornecedores" :key="marca" :value="marca">{{ marca }}</option>
          </select>
          <textarea v-model="novoFornecedor.observacoes" placeholder="Observações" rows="3"></textarea>
          <div class="form-actions">
            <button type="submit">{{ fornecedorEditandoId ? 'Salvar fornecedor' : 'Cadastrar fornecedor' }}</button>
            <button
              v-if="fornecedorEditandoId || formularioAberto"
              class="secondary"
              type="button"
              @click="cancelarFormularioFornecedor"
            >
              Cancelar
            </button>
          </div>
        </form>

        <p v-else class="focus-form-hint">Clique em "Abrir" para cadastrar ou editar fornecedores.</p>
      </aside>
    </div>
  </section>
</template>
