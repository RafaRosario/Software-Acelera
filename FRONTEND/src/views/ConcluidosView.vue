<script setup>
import { toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  dataFimConcluidos,
  dataInicioConcluidos,
  editarFrete,
  empresasClientes,
  excluirConcluidosFiltrados,
  exportarConcluidos,
  filtroClienteConcluidos,
  filtroConcluidos,
  formatarData,
  formatarMoeda,
  fretesConcluidosFiltrados,
  nomeMotorista,
  placaVeiculo,
  podeCriarFrete,
  podeEditarConcluidos,
  pontosAdicionaisFrete,
  salvarDocumentoPreenchidoFrete,
  salvarFechamentoFrete,
  salvarValorPreenchidoFrete,
  salvarValoresConcluidosFiltrados,
  totalConcluido,
} = toRefs(state)
</script>

<template>
    <section class="workspace">
      <div class="section-head">
        <div>
          <h2>Fretes concluídos</h2>
          <p>Fechamento financeiro dos serviços já realizados.</p>
        </div>
      </div>

      <div class="period-filter">
        <label class="field">
          Período
          <select v-model="filtroConcluidos">
            <option value="todos">Todos</option>
            <option value="hoje">Hoje</option>
            <option value="semana">Esta semana</option>
            <option value="mes">Este mês</option>
            <option value="periodo">Período personalizado</option>
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
          Início
          <input v-model="dataInicioConcluidos" type="date" :disabled="filtroConcluidos !== 'periodo'" />
        </label>
        <label class="field" :class="{ disabled: filtroConcluidos !== 'periodo' }">
          Fim
          <input v-model="dataFimConcluidos" type="date" :disabled="filtroConcluidos !== 'periodo'" />
        </label>
        <button type="button" @click="exportarConcluidos">Exportar Excel</button>
        <button v-if="podeEditarConcluidos" class="danger" type="button" @click="excluirConcluidosFiltrados">Excluir filtrados</button>
      </div>

      <div class="metrics concluded-metrics">
        <div><strong>{{ fretesConcluidosFiltrados.length }}</strong><span>Fretes concluídos</span></div>
        <div><strong>{{ formatarMoeda(totalConcluido) }}</strong><span>Total informado</span></div>
      </div>

      <div v-if="podeEditarConcluidos" class="concluded-bulk-actions">
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
            <span class="badge concluida">concluído</span>
          </div>

          <div class="billing-grid">
            <label class="field billing-field">
              Nota fiscal
              <input
                v-model="frete.nota_fiscal"
                :disabled="!podeEditarConcluidos"
                placeholder="Número da nota fiscal"
                @change="salvarDocumentoPreenchidoFrete(frete, 'nota_fiscal')"
              />
            </label>
            <label class="field billing-field">
              OC
              <input v-model="frete.oc" :disabled="!podeEditarConcluidos" placeholder="Número da OC" @change="salvarDocumentoPreenchidoFrete(frete, 'oc')" />
            </label>
            <label class="field billing-field">
              Valor do serviço
              <input
                v-model="frete.valor_servico"
                :disabled="!podeEditarConcluidos"
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
                :disabled="!podeEditarConcluidos"
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
                :disabled="!podeEditarConcluidos"
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
              <span>Serviço: {{ formatarMoeda(frete.valor_servico) }}</span>
              <span v-if="frete.retorno">Retorno: {{ formatarMoeda(frete.valor_retorno) }}</span>
              <span v-if="pontosAdicionaisFrete(frete).length > 0">Ponto: {{ formatarMoeda(frete.valor_ponto_adicional) }}</span>
            </div>
            <div class="concluded-card-actions">
              <button v-if="podeCriarFrete" class="secondary" type="button" @click="editarFrete(frete)">Editar frete</button>
              <button v-if="podeEditarConcluidos" type="button" @click="salvarFechamentoFrete(frete)">Salvar fechamento</button>
            </div>
          </div>
        </article>

        <p v-if="fretesConcluidosFiltrados.length === 0" class="empty">Nenhum frete concluído para este período.</p>
      </div>
    </section>
</template>
