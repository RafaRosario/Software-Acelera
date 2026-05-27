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

const cidadesFornecedores = computed(() => {
  return [...new Set(fornecedores.value.map((fornecedor) => String(fornecedor.cidade || '').trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

const marcasFornecedores = computed(() => {
  return [...new Set(fornecedores.value.map((fornecedor) => String(fornecedor.marca || '').trim()).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'))
})

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
    ]
      .filter(Boolean)
      .join(' ')
    return normalizarTextoBusca.value(dados).includes(termo)
  })
})
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <div>
        <h2>Fornecedores</h2>
        <p>Lojas onde são comprados materiais para os caminhões.</p>
      </div>
    </div>

    <div class="registry-layout">
      <div class="registry-form-card">
        <div class="registry-card-head">
          <span>04</span>
          <div>
            <h2>Novo fornecedor</h2>
            <p>FORNECEDOR</p>
          </div>
        </div>
        <form class="stack-form" @submit.prevent="cadastrarFornecedor">
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
          <input v-model="novoFornecedor.marca" placeholder="Marca que trabalha" required />
          <textarea v-model="novoFornecedor.observacoes" placeholder="Observações" rows="3"></textarea>
          <div class="form-actions">
            <button type="submit">{{ fornecedorEditandoId ? 'Salvar fornecedor' : 'Cadastrar fornecedor' }}</button>
            <button v-if="fornecedorEditandoId" class="secondary" type="button" @click="limparFornecedor">Cancelar edição</button>
          </div>
        </form>
      </div>

      <aside class="registry-directory">
        <div class="registry-directory-head">
          <div>
            <strong>Fornecedores cadastrados</strong>
            <small>{{ fornecedoresFiltrados.length }} de {{ fornecedores.length }} registros</small>
          </div>
        </div>

        <div class="form-grid">
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

        <ul class="simple-list registry-list">
          <li v-for="fornecedor in fornecedoresFiltrados" :key="fornecedor.id">
            <span>
              {{ fornecedor.nome }}
              <small>{{ fornecedor.marca }} | {{ fornecedor.cidade }} | {{ fornecedor.telefone || 'Sem telefone' }} | {{ fornecedor.cep || 'Sem CEP' }}</small>
              <small class="registry-note">Endereço: {{ fornecedor.endereco }}</small>
              <small v-if="fornecedor.observacoes" class="registry-note">Obs: {{ fornecedor.observacoes }}</small>
            </span>
            <div class="registry-actions">
              <button class="secondary compact-button" type="button" @click="editarFornecedor(fornecedor)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirFornecedor(fornecedor.id)">Excluir</button>
            </div>
          </li>
        </ul>
        <p v-if="fornecedoresFiltrados.length === 0" class="empty">Nenhum fornecedor encontrado.</p>
      </aside>
    </div>
  </section>
</template>
