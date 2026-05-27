<script setup>
import { toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  classeSituacaoMotorista,
  exportarHistoricoMotoristas,
  formatarCpf,
  formatarData,
  formatarRg,
  fretes,
  fretesUsoMotorista,
  historicoFretesMotorista,
  horarioFrete,
  motoristaAberto,
  motoristas,
  motoristasAlocacao,
  pontosAdicionaisFrete,
  rotuloStatusFrete,
  situacaoMotorista,
} = toRefs(state)

const rotuloSituacaoMotorista = (situacao) => {
  if (situacao === 'Disponivel') return 'Disponível'
  if (situacao === 'Indisponivel') return 'Indisponível'
  if (situacao === 'Em servico') return 'Em serviço'
  return situacao
}
</script>

<template>
    <section class="workspace">
      <div class="section-head">
        <div>
          <h2>Status dos motoristas</h2>
          <p>Cores indicam quem está em serviço, disponível ou indisponível.</p>
        </div>
        <button type="button" @click="exportarHistoricoMotoristas">Exportar histórico Excel</button>
      </div>

      <div class="driver-cards">
        <article v-for="motorista in motoristasAlocacao" :key="motorista.id" class="driver-card" :class="classeSituacaoMotorista(motorista)">
          <div class="driver-card-head">
            <div>
              <h3>{{ motorista.nome }}</h3>
              <p v-if="motorista.observacoes">{{ motorista.observacoes }}</p>
            </div>
            <span class="driver-status">{{ rotuloSituacaoMotorista(situacaoMotorista(motorista)) }}</span>
          </div>
          <div class="driver-stats">
            <span><strong>{{ motorista.viagens_dia }}</strong>Hoje</span>
            <span><strong>{{ motorista.viagens_semana }}</strong>Semana</span>
          </div>
          <div class="driver-card-body">
            <div v-if="fretesUsoMotorista(motorista).length > 0" class="driver-active-freights">
              <strong>Fretes em aberto</strong>
              <div v-for="frete in fretesUsoMotorista(motorista)" :key="frete.id" class="driver-active-row">
                <span>{{ formatarData(frete.data_coleta) }} - {{ horarioFrete(frete) }}</span>
                <small>{{ frete.cliente }} | {{ frete.origem }} -> {{ frete.destino }}</small>
                <small>{{ rotuloStatusFrete(frete.status) }}</small>
              </div>
            </div>
            <div v-else class="driver-active-empty">Sem fretes em aberto</div>
          </div>
          <button class="secondary driver-detail-button" type="button" @click="motoristaAberto = motoristaAberto === motorista.id ? null : motorista.id">
            {{ motoristaAberto === motorista.id ? 'Ocultar dados' : 'Ver dados' }}
          </button>
          <div v-if="motoristaAberto === motorista.id" class="driver-data">
            <span>Telefone: {{ motorista.telefone }}</span>
            <span>RG: {{ formatarRg(motorista.rg) }}</span>
            <span>CPF: {{ formatarCpf(motorista.cpf) }}</span>

            <div class="driver-history">
              <strong>Histórico de fretes</strong>
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
                Nenhum frete concluído encontrado.
              </p>
            </div>
          </div>
        </article>
      </div>
    </section>
</template>
