<script setup>
import { toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  adicionarEmpresaColeta,
  buscaDestinoFrete,
  buscaEmpresaColeta,
  buscaOrigemFrete,
  cadastrarFrete,
  cancelarEdicaoFrete,
  empresas,
  empresasClientes,
  empresasColetaDisponiveis,
  empresasDestinoDisponiveis,
  empresasOrigemDisponiveis,
  freteEditandoId,
  fretes,
  limparDestinoFrete,
  limparOrigemFrete,
  motoristas,
  novoFrete,
  removerEmpresaColeta,
  selecionarDestinoFrete,
  selecionarOrigemFrete,
  tiposVeiculo,
  veiculosParaFrete,
  ocorrenciasVeiculoSelecionado,
} = toRefs(state)
</script>

<template>
    <section class="workspace">
      <div class="section-head">
        <div>
          <h2>{{ freteEditandoId ? 'Editar frete' : 'Cadastrar frete' }}</h2>
          <p>{{ freteEditandoId ? 'Ajuste os dados do frete e salve as alterações.' : 'Use para fretes recebidos por planilha ou WhatsApp.' }}</p>
        </div>
      </div>

      <form class="form-grid freight-create-form" @submit.prevent="cadastrarFrete">
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
              {{ empresa.nome }}<small>{{ empresa.cnpj || 'CNPJ não informado' }}</small>
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
              {{ empresa.nome }}<small>{{ empresa.cnpj || 'CNPJ não informado' }}</small>
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
        <label class="field">Valor do serviço<input v-model="novoFrete.valor_servico" type="number" min="0" step="0.01" placeholder="Opcional" /></label>
        <label class="check-field"><input v-model="novoFrete.retorno" type="checkbox" /> Criar retorno para cobrança</label>
        <label class="field">Motorista<select v-model="novoFrete.motorista_id" required><option value="" disabled></option><option v-for="motorista in motoristas" :key="motorista.id" :value="motorista.id">{{ motorista.nome }}</option></select></label>
        <label class="field">Caminhão<select v-model="novoFrete.veiculo_id" required><option value="" disabled></option><option v-for="veiculo in veiculosParaFrete" :key="veiculo.id" :value="veiculo.id">{{ veiculo.placa }} - {{ veiculo.tipo }}</option></select></label>
        <div v-if="ocorrenciasVeiculoSelecionado.length > 0" class="ocorrencias-aviso">
          <strong>⚠️ Atenção:</strong> Este caminhão tem {{ ocorrenciasVeiculoSelecionado.length }} ocorrência(s) em aberto:
          <ul>
            <li v-for="o in ocorrenciasVeiculoSelecionado" :key="o.id">{{ o.categoria }} — {{ o.descricao }}</li>
          </ul>
        </div>
        <label class="field wide">Observações<textarea v-model="novoFrete.observacoes" rows="3"></textarea></label>
        <div class="form-actions freight-form-actions">
          <button type="submit">{{ freteEditandoId ? 'Salvar alterações' : 'Cadastrar frete' }}</button>
          <button v-if="freteEditandoId" class="secondary" type="button" @click="cancelarEdicaoFrete">Cancelar edição</button>
        </div>
      </form>
    </section>
</template>
