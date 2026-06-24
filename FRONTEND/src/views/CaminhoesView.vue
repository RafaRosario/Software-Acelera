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
  abrirOcorrenciasVeiculo,
  adicionarOcorrenciaVeiculo,
  classeSituacaoVeiculo,
  confirmarIndisponibilidadeVeiculo,
  excluirOcorrenciaVeiculo,
  fecharIndisponibilidadeVeiculo,
  fecharOcorrenciasVeiculo,
  filtroSituacaoVeiculo,
  filtroTipoVeiculo,
  formatarData,
  formatarDataHora,
  fretes,
  fretesUsoVeiculo,
  horarioFrete,
  liberarVeiculo,
  motivoIndisponibilidadeVeiculo,
  novaOcorrencia,
  ocorrenciaEditandoId,
  ocorrenciaResolucaoTexto,
  ocorrenciasPorVeiculo,
  ocorrenciasAbertas,
  resolverOcorrenciaVeiculo,
  rotuloStatusFrete,
  salvarObservacaoEstadoVeiculo,
  situacaoVeiculo,
  tiposVeiculo,
  totaisVeiculos,
  veiculoIndisponibilidadeAberto,
  veiculoOcorrenciasAberto,
  veiculosFiltrados,
} = toRefs(state)

const rotuloSituacaoVeiculo = (situacao) => {
  if (situacao === 'Disponivel') return 'Disponível'
  if (situacao === 'Indisponivel') return 'Indisponível'
  return situacao
}

const rotuloUrgencia = (urgencia) => {
  if (urgencia === 'Alta') return '🔴 Alta'
  if (urgencia === 'Media' || urgencia === 'Média') return '🟡 Média'
  return '🟢 Baixa'
}

const rotuloStatusOcorrencia = (status) => {
  if (status === 'Resolvido') return 'Resolvido'
  if (status === 'Em resolução' || status === 'Em resolucao') return 'Em resolução'
  return 'Aberto'
}

const classeStatusOcorrencia = (status) => {
  if (status === 'Resolvido') return 'ocorrencia-resolvida'
  if (status === 'Em resolução' || status === 'Em resolucao') return 'ocorrencia-em-resolucao'
  return 'ocorrencia-aberta'
}
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <div>
        <h2>Controle de caminhões</h2>
        <p>Disponibilidade da frota e ocorrências de manutenção.</p>
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
      <div :class="totaisVeiculos.comOcorrencias > 0 ? 'metric-alert' : ''">
        <strong>{{ totaisVeiculos.comOcorrencias }}</strong><span>Com ocorrências</span>
      </div>
    </div>

    <div class="vehicle-grid">
      <article v-for="veiculo in veiculosFiltrados" :key="veiculo.id" class="vehicle-card" :class="classeSituacaoVeiculo(veiculo)">
        <div class="vehicle-card-head">
          <div>
            <h3>{{ veiculo.tipo }}</h3>
            <p>{{ veiculo.placa }}</p>
            <small v-if="veiculo.observacoes" class="vehicle-feature">{{ veiculo.observacoes }}</small>
          </div>
          <div class="vehicle-card-head-right">
            <span class="vehicle-status">{{ rotuloSituacaoVeiculo(situacaoVeiculo(veiculo)) }}</span>
            <button
              class="ocorrencias-badge"
              :class="ocorrenciasAbertas(veiculo).length > 0 ? 'badge-alert' : 'badge-ok'"
              type="button"
              @click="abrirOcorrenciasVeiculo(veiculo)"
            >
              {{ ocorrenciasAbertas(veiculo).length > 0 ? `⚠️ ${ocorrenciasAbertas(veiculo).length} ocorrência(s)` : '✓ Sem ocorrências' }}
            </button>
          </div>
        </div>

        <div class="vehicle-card-body">
          <div v-if="fretesUsoVeiculo(veiculo).length > 0" class="vehicle-usage">
            <strong>Fretes abertos</strong>
            <div v-for="frete in fretesUsoVeiculo(veiculo)" :key="frete.id" class="vehicle-usage-row">
              <span>{{ formatarData(frete.data_coleta) }} - {{ horarioFrete(frete) }}</span>
              <small>{{ frete.cliente }} | {{ frete.origem }} → {{ frete.destino }}</small>
              <small>{{ rotuloStatusFrete(frete.status) }}</small>
            </div>
          </div>
          <div v-else class="vehicle-usage-empty">Sem fretes em aberto</div>
        </div>

        <div v-if="!veiculo.ativo" class="vehicle-unavailable-reason">
          <strong>Motivo da indisponibilidade</strong>
          <p>{{ veiculo.motivo_indisponibilidade || 'Sem motivo informado' }}</p>
        </div>

        <div class="actions vehicle-actions">
          <button class="secondary" type="button" @click="abrirOcorrenciasVeiculo(veiculo)">
            Ocorrências
          </button>
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

    <!-- Modal: indisponibilizar -->
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

    <!-- Modal: ocorrências -->
    <div v-if="veiculoOcorrenciasAberto" class="freight-detail-backdrop" @click.self="fecharOcorrenciasVeiculo">
      <section class="freight-detail-modal ocorrencias-modal" role="dialog" aria-modal="true" @click.stop>
        <header class="freight-detail-header">
          <div>
            <div class="freight-detail-kickers">
              <span class="freight-detail-label">{{ veiculoOcorrenciasAberto.tipo }}</span>
              <span class="freight-detail-label">{{ veiculoOcorrenciasAberto.placa }}</span>
            </div>
            <h2>Ocorrências</h2>
            <p>Registro de problemas e manutenções do dia a dia.</p>
          </div>
          <button class="icon-button" type="button" aria-label="Fechar" @click="fecharOcorrenciasVeiculo">✕</button>
        </header>

        <div class="ocorrencias-modal-body">
          <!-- Nova ocorrência -->
          <div class="ocorrencia-form">
            <h4>Registrar ocorrência</h4>
            <div class="ocorrencia-form-fields">
              <label class="field compact">
                Categoria
                <select v-model="novaOcorrencia.categoria">
                  <option value="" disabled>Selecione</option>
                  <option>Elétrico</option>
                  <option>Pneu</option>
                  <option>Freio</option>
                  <option>Lataria</option>
                  <option>Motor</option>
                  <option>Iluminação</option>
                  <option>Outro</option>
                </select>
              </label>
              <label class="field compact">
                Urgência
                <select v-model="novaOcorrencia.urgencia">
                  <option>Baixa</option>
                  <option>Média</option>
                  <option>Alta</option>
                </select>
              </label>
              <label class="field compact">
                Reportado por
                <input v-model="novaOcorrencia.reportado_por" type="text" placeholder="Nome (opcional)" />
              </label>
            </div>
            <label class="field">
              Descrição
              <textarea v-model="novaOcorrencia.descricao" rows="2" placeholder="Descreva o problema encontrado..."></textarea>
            </label>
            <div class="actions">
              <button type="button" @click="adicionarOcorrenciaVeiculo">Registrar ocorrência</button>
            </div>
          </div>

          <!-- Lista de ocorrências -->
          <div class="ocorrencias-lista">
            <h4>Histórico</h4>
            <div
              v-for="ocorrencia in (ocorrenciasPorVeiculo[veiculoOcorrenciasAberto.id] || [])"
              :key="ocorrencia.id"
              class="ocorrencia-item"
              :class="classeStatusOcorrencia(ocorrencia.status)"
            >
              <div class="ocorrencia-item-head">
                <div class="ocorrencia-meta">
                  <strong>{{ ocorrencia.categoria }}</strong>
                  <span class="ocorrencia-urgencia">{{ rotuloUrgencia(ocorrencia.urgencia) }}</span>
                  <span class="ocorrencia-status-badge">{{ rotuloStatusOcorrencia(ocorrencia.status) }}</span>
                </div>
                <small class="ocorrencia-data">{{ formatarDataHora ? formatarDataHora(ocorrencia.criado_em) : ocorrencia.criado_em }}</small>
              </div>
              <p class="ocorrencia-descricao">{{ ocorrencia.descricao }}</p>
              <small v-if="ocorrencia.reportado_por" class="ocorrencia-reportado">Reportado por: {{ ocorrencia.reportado_por }}</small>
              <p v-if="ocorrencia.resolucao" class="ocorrencia-resolucao">Resolução: {{ ocorrencia.resolucao }}</p>

              <div v-if="ocorrencia.status !== 'Resolvido'" class="ocorrencia-acoes">
                <div v-if="ocorrenciaEditandoId === ocorrencia.id" class="ocorrencia-resolver-form">
                  <label class="field">
                    Descrição da resolução (opcional)
                    <textarea v-model="ocorrenciaResolucaoTexto" rows="2" placeholder="O que foi feito para resolver..."></textarea>
                  </label>
                  <div class="actions">
                    <button class="secondary" type="button" @click="ocorrenciaEditandoId = null">Cancelar</button>
                    <button type="button" @click="resolverOcorrenciaVeiculo(ocorrencia)">Confirmar resolução</button>
                  </div>
                </div>
                <div v-else class="actions">
                  <button class="secondary" type="button" @click="ocorrenciaEditandoId = ocorrencia.id; ocorrenciaResolucaoTexto = ''">
                    Marcar resolvido
                  </button>
                  <button class="danger" type="button" @click="excluirOcorrenciaVeiculo(ocorrencia)">Excluir</button>
                </div>
              </div>
              <div v-else class="actions">
                <button class="danger" type="button" @click="excluirOcorrenciaVeiculo(ocorrencia)">Excluir</button>
              </div>
            </div>
            <p v-if="!(ocorrenciasPorVeiculo[veiculoOcorrenciasAberto.id] || []).length" class="empty">
              Nenhuma ocorrência registrada para este caminhão.
            </p>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>
