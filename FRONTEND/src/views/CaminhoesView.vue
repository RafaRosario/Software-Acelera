<script setup>
import { toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  abrirIndisponibilidadeVeiculo,
  classeSituacaoVeiculo,
  confirmarIndisponibilidadeVeiculo,
  fecharIndisponibilidadeVeiculo,
  filtroSituacaoVeiculo,
  filtroTipoVeiculo,
  formatarData,
  fretes,
  fretesUsoVeiculo,
  horarioFrete,
  liberarVeiculo,
  motivoIndisponibilidadeVeiculo,
  rotuloStatusFrete,
  salvarObservacaoEstadoVeiculo,
  situacaoVeiculo,
  tiposVeiculo,
  totaisVeiculos,
  veiculoIndisponibilidadeAberto,
  veiculosFiltrados,
} = toRefs(state)

const rotuloSituacaoVeiculo = (situacao) => {
  if (situacao === 'Disponivel') return 'Disponível'
  if (situacao === 'Indisponivel') return 'Indisponível'
  return situacao
}
</script>

<template>
    <section class="workspace">
      <div class="section-head">
        <div>
          <h2>Controle de caminhões</h2>
          <p>Disponibilidade da frota e uso em fretes abertos.</p>
        </div>
        <label class="field compact">
          Situação
          <select v-model="filtroSituacaoVeiculo">
            <option value="Todos">Todos</option>
            <option value="Disponivel">Disponíveis</option>
            <option value="Em uso">Em uso</option>
            <option value="Indisponivel">Indisponíveis</option>
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
        <div><strong>{{ totaisVeiculos.disponiveis }}</strong><span>Disponíveis</span></div>
        <div><strong>{{ totaisVeiculos.emUso }}</strong><span>Em uso</span></div>
        <div><strong>{{ totaisVeiculos.indisponiveis }}</strong><span>Indisponíveis</span></div>
      </div>

      <div class="vehicle-grid">
        <article v-for="veiculo in veiculosFiltrados" :key="veiculo.id" class="vehicle-card" :class="classeSituacaoVeiculo(veiculo)">
          <div class="vehicle-card-head">
            <div>
              <h3>{{ veiculo.tipo }}</h3>
              <p>{{ veiculo.placa }}</p>
              <small v-if="veiculo.observacoes" class="vehicle-feature">{{ veiculo.observacoes }}</small>
              <small v-if="veiculo.observacao_estado" class="vehicle-feature">Estado: {{ veiculo.observacao_estado }}</small>
            </div>
            <span class="vehicle-status">{{ rotuloSituacaoVeiculo(situacaoVeiculo(veiculo)) }}</span>
          </div>

          <div class="vehicle-card-body">
            <div v-if="fretesUsoVeiculo(veiculo).length > 0" class="vehicle-usage">
              <strong>Fretes abertos</strong>
              <div v-for="frete in fretesUsoVeiculo(veiculo)" :key="frete.id" class="vehicle-usage-row">
                <span>{{ formatarData(frete.data_coleta) }} - {{ horarioFrete(frete) }}</span>
                <small>{{ frete.cliente }} | {{ frete.origem }} -> {{ frete.destino }}</small>
                <small>{{ rotuloStatusFrete(frete.status) }}</small>
              </div>
            </div>
            <div v-else class="vehicle-usage-empty">Sem fretes em aberto</div>
          </div>

          <label class="field">
            Observação
            <textarea
              v-model="veiculo.observacao_estado"
              rows="3"
              @change="salvarObservacaoEstadoVeiculo(veiculo)"
            ></textarea>
          </label>

          <div v-if="!veiculo.ativo" class="vehicle-unavailable-reason">
            <strong>Motivo da indisponibilidade</strong>
            <p>{{ veiculo.motivo_indisponibilidade || 'Sem motivo informado' }}</p>
          </div>

          <div class="actions vehicle-actions">
            <button v-if="veiculo.ativo" class="danger" type="button" @click="abrirIndisponibilidadeVeiculo(veiculo)">
              Marcar indisponível
            </button>
            <button v-else type="button" @click="liberarVeiculo(veiculo)">
              Liberar para uso
            </button>
          </div>
        </article>

        <p v-if="veiculosFiltrados.length === 0" class="empty">Nenhum caminhão nesta situação.</p>
      </div>

      <div v-if="veiculoIndisponibilidadeAberto" class="modal-backdrop" @click.self="fecharIndisponibilidadeVeiculo">
        <div class="modal-panel">
          <div>
            <h3>Indisponibilizar caminhão</h3>
            <p>{{ veiculoIndisponibilidadeAberto.placa }} - {{ veiculoIndisponibilidadeAberto.tipo }}</p>
          </div>

          <label class="field">
            Motivo
            <textarea v-model="motivoIndisponibilidadeVeiculo" rows="4" placeholder="Ex: conserto, revisão, reservado"></textarea>
          </label>

          <div class="actions">
            <button class="secondary" type="button" @click="fecharIndisponibilidadeVeiculo">Cancelar</button>
            <button class="danger" type="button" @click="confirmarIndisponibilidadeVeiculo">Confirmar</button>
          </div>
        </div>
      </div>
    </section>
</template>
