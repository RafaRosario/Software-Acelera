<script setup>
import { toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  STATUS_CONCLUIDO,
  abrirFreteDetalhe,
  abrirMenuStatusFrete,
  abrirWhatsApp,
  ativarFiltroPendenciasAntigas,
  carregando,
  checklistStatusFrete,
  classeChecklistFrete,
  classeStatusKanban,
  classeStatusVisualFrete,
  colunasKanban,
  copiarAtualizacaoEdscha,
  copiarMensagem,
  dataHoraChecklistFrete,
  editarFrete,
  empresasClientes,
  encerrarArrastoFrete,
  excluirFrete,
  fecharFreteDetalhe,
  fecharMenuStatusFrete,
  filtroClienteFretes,
  filtroDataFimFretes,
  filtroDataInicioFretes,
  filtroPendenciasAntigas,
  filtroStatus,
  formatarData,
  formatarMoeda,
  freteAbertoId,
  freteArrastandoId,
  freteDetalhe,
  freteEstaAtrasado,
  fretes,
  fretesAtrasados,
  fretesFiltrados,
  fretesPorStatusKanban,
  horarioFrete,
  iniciarArrastoFrete,
  limparFiltroPendenciasAntigas,
  maiorAtrasoDias,
  menuStatusFrete,
  motoristas,
  moverFreteParaStatus,
  nomeMotorista,
  placaVeiculo,
  pontosMensagemFrete,
  rotaCompactaFrete,
  rotuloStatusFrete,
  salvarEscalaAutomaticamente,
  salvarNotaFiscalFrete,
  salvarValorFrete,
  soltarFreteEmStatus,
  statusDestinoAtivo,
  statusDisponiveisFrete,
  statusEhConcluido,
  statusFiltroFrete,
  statusVisualFrete,
  subtituloStatusKanban,
  textoAtrasoFrete,
  totais,
  veiculos,
} = toRefs(state)
</script>

<template>
    <section class="workspace">
      <div class="section-head freight-toolbar">
        <div>
          <h2>Escala diária</h2>
          <p>Fretes cadastrados, alocação e status da viagem.</p>
        </div>
        <div class="freight-toolbar-controls">
          <button class="update-button" type="button" @click="copiarAtualizacaoEdscha">
            Copiar atualização Edscha
          </button>
          <div class="freight-quick-filters">
            <button
              class="secondary overdue-filter-button"
              :class="{ active: filtroPendenciasAntigas }"
              type="button"
              @click="filtroPendenciasAntigas ? limparFiltroPendenciasAntigas() : ativarFiltroPendenciasAntigas()"
            >
              Pendentes antigos
              <span v-if="fretesAtrasados.length > 0">{{ fretesAtrasados.length }}</span>
            </button>
          </div>
          <div class="freight-filters">
            <label class="field compact">
              Data início
              <input v-model="filtroDataInicioFretes" type="date" />
            </label>
            <label class="field compact">
              Data fim
              <input v-model="filtroDataFimFretes" type="date" />
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
                <option v-for="status in statusFiltroFrete" :key="status" :value="status">{{ rotuloStatusFrete(status) }}</option>
              </select>
            </label>
          </div>
        </div>
      </div>

      <section v-if="fretesAtrasados.length > 0" class="overdue-alert">
        <div class="overdue-alert-main">
          <span class="overdue-alert-count">{{ fretesAtrasados.length }}</span>
          <div>
            <strong>{{ fretesAtrasados.length === 1 ? '1 frete antigo em aberto' : `${fretesAtrasados.length} fretes antigos em aberto` }}</strong>
            <p>Mais antigo: {{ maiorAtrasoDias === 1 ? '1 dia' : `${maiorAtrasoDias} dias` }}. Revise antes de seguir a escala do dia.</p>
          </div>
        </div>
        <div class="overdue-alert-actions">
          <button type="button" @click="ativarFiltroPendenciasAntigas">Ver pendências</button>
          <button v-if="filtroPendenciasAntigas" class="secondary" type="button" @click="limparFiltroPendenciasAntigas">Voltar para filtros</button>
        </div>
      </section>

      <div class="metrics">
        <div><strong>{{ totais.aguardando }}</strong><span>Aguardando horário</span></div>
        <div><strong>{{ totais.andamento }}</strong><span>Em andamento</span></div>
        <div><strong>{{ totais.concluidas }}</strong><span>Concluídas</span></div>
        <div><strong>{{ totais.retorno }}</strong><span>Com retorno</span></div>
      </div>

      <section v-if="fretesAtrasados.length > 0" class="overdue-panel">
        <div class="overdue-panel-head">
          <div>
            <h3>Pendências antigas</h3>
            <p>Fretes abertos com data anterior a hoje.</p>
          </div>
          <button class="secondary" type="button" @click="ativarFiltroPendenciasAntigas">Filtrar no Kanban</button>
        </div>
        <div class="overdue-list">
          <article v-for="frete in fretesAtrasados" :key="frete.id" class="overdue-row">
            <div class="overdue-row-main">
              <strong>{{ formatarData(frete.data_coleta) }} - {{ horarioFrete(frete) }}</strong>
              <span>{{ rotaCompactaFrete(frete) }}</span>
              <small>{{ nomeMotorista(frete.motorista_id) }} | {{ placaVeiculo(frete.veiculo_id) }} | {{ rotuloStatusFrete(frete.status) }}</small>
            </div>
            <span class="overdue-days">{{ textoAtrasoFrete(frete) }}</span>
            <div class="overdue-row-actions">
              <button class="secondary compact-button" type="button" @click="abrirMenuStatusFrete($event, frete)">Mover status</button>
              <button class="secondary compact-button" type="button" @click="editarFrete(frete)">Editar</button>
              <button class="secondary compact-button" type="button" @click="abrirWhatsApp(frete)">WhatsApp</button>
            </div>
          </article>
        </div>
      </section>

      <div class="kanban-board">
        <section
          v-for="status in colunasKanban"
          :key="status"
          class="kanban-column"
          :class="[classeStatusKanban(status), { 'drop-active': statusDestinoAtivo === status }]"
          @dragover.prevent
          @dragenter.prevent="statusDestinoAtivo = status"
          @drop="soltarFreteEmStatus($event, status)"
        >
          <header class="kanban-column-head">
            <div>
              <h3>{{ rotuloStatusFrete(status) }}</h3>
              <p>{{ subtituloStatusKanban(status) }}</p>
            </div>
            <span>{{ fretesPorStatusKanban(status).length }}</span>
          </header>

          <div class="kanban-cards">
            <article
              v-for="frete in fretesPorStatusKanban(status)"
              :key="frete.id"
              class="freight-card kanban-card"
              :class="{ dragging: freteArrastandoId === frete.id, expanded: freteAbertoId === frete.id, overdue: freteEstaAtrasado(frete) }"
              draggable="true"
              role="button"
              tabindex="0"
              @dragstart="iniciarArrastoFrete($event, frete)"
              @dragend="encerrarArrastoFrete"
              @click="abrirFreteDetalhe(frete.id)"
              @contextmenu.prevent.stop="abrirMenuStatusFrete($event, frete)"
              @keydown.enter.prevent="abrirFreteDetalhe(frete.id)"
              @keydown.space.prevent="abrirFreteDetalhe(frete.id)"
            >
              <div class="kanban-card-summary">
                <div class="kanban-time-block">
                  <span class="time">{{ horarioFrete(frete) }}</span>
                  <span class="badge" :class="classeStatusVisualFrete(frete.status)">{{ statusVisualFrete(frete.status) }}</span>
                </div>

                <p class="kanban-route">{{ rotaCompactaFrete(frete) }}</p>

                <div class="kanban-mini-details">
                  <span>{{ frete.tipo_caminhao_necessario }}</span>
                  <span>{{ placaVeiculo(frete.veiculo_id) }}</span>
                  <span class="checklist-chip" :class="classeChecklistFrete(frete)">{{ checklistStatusFrete(frete) }}</span>
                  <span v-if="freteEstaAtrasado(frete)" class="overdue-chip">{{ textoAtrasoFrete(frete) }}</span>
                  <span v-if="frete.retorno">Gera retorno</span>
                </div>
              </div>

              <div v-if="false" class="kanban-card-expanded" @click.stop>

                <div v-if="frete.checklist_observacoes" class="note">Checklist: {{ frete.checklist_observacoes }}</div>

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
                    Caminhão
                    <select v-model="frete.veiculo_id" @change="salvarEscalaAutomaticamente(frete)">
                      <option :value="null">Selecionar</option>
                      <option v-for="veiculo in veiculos" :key="veiculo.id" :value="veiculo.id">{{ veiculo.placa }} - {{ veiculo.tipo }}</option>
                    </select>
                  </label>
                  <label class="field">
                    Valor do serviço
                    <input v-model="frete.valor_servico" type="number" min="0" step="0.01" placeholder="Opcional" />
                  </label>
                  <label class="field">
                    Nota fiscal
                    <input v-model="frete.nota_fiscal" placeholder="Opcional" />
                  </label>
                </div>

                <div class="actions">
                  <button class="secondary status-move-button" type="button" @click="abrirMenuStatusFrete($event, frete)">Mover status</button>
                  <button class="secondary" type="button" @click="salvarValorFrete(frete)">Salvar valor</button>
                  <button class="secondary" type="button" @click="salvarNotaFiscalFrete(frete)">Salvar NF</button>
                  <button class="secondary" type="button" @click="editarFrete(frete)">Editar frete</button>
                  <button class="secondary" type="button" @click="copiarMensagem(frete)">Copiar mensagem</button>
                  <button class="secondary" type="button" @click="abrirWhatsApp(frete)">WhatsApp</button>
                  <button class="danger" type="button" @click="excluirFrete(frete.id)">Excluir</button>
                </div>
              </div>
            </article>

            <p v-if="fretesPorStatusKanban(status).length === 0" class="kanban-empty">Solte fretes aqui</p>
          </div>
        </section>

        <p v-if="!carregando && fretesFiltrados.length === 0" class="empty">
          {{ filtroPendenciasAntigas ? 'Nenhuma pendência antiga encontrada.' : 'Nenhum frete cadastrado para esta data.' }}
        </p>
      </div>

      <div v-if="freteDetalhe" class="freight-detail-backdrop" @click="fecharFreteDetalhe">
        <section class="freight-detail-modal" role="dialog" aria-modal="true" @click.stop>
          <header class="freight-detail-header">
            <div>
              <div class="freight-detail-kickers">
                <span class="freight-detail-label">{{ rotuloStatusFrete(freteDetalhe.status) }}</span>
                <span class="checklist-chip" :class="classeChecklistFrete(freteDetalhe)">{{ checklistStatusFrete(freteDetalhe) }}</span>
              </div>
              <h2>{{ horarioFrete(freteDetalhe) }} - {{ freteDetalhe.origem }} para {{ freteDetalhe.destino }}</h2>
              <p>{{ nomeMotorista(freteDetalhe.motorista_id) }} | {{ placaVeiculo(freteDetalhe.veiculo_id) }}</p>
            </div>
            <button class="icon-button" type="button" aria-label="Fechar detalhes" @click="fecharFreteDetalhe">x</button>
          </header>

          <div class="freight-detail-body">
            <section class="freight-detail-main">
              <div class="freight-detail-overview">
                <div>
                  <small>Veículo</small>
                  <strong>{{ freteDetalhe.tipo_caminhao_necessario }}</strong>
                </div>
                <div>
                  <small>Nota fiscal</small>
                  <strong>{{ freteDetalhe.nota_fiscal || 'Sem nota' }}</strong>
                </div>
                <div>
                  <small>Valor</small>
                  <strong>{{ formatarMoeda(freteDetalhe.valor_servico) }}</strong>
                </div>
                <div>
                  <small>Retorno</small>
                  <strong>{{ freteDetalhe.retorno ? 'Sim' : 'Não' }}</strong>
                </div>
              </div>

              <div class="freight-detail-section">
                <h3>Rota</h3>
                <div class="freight-route-steps">
                  <div v-for="(ponto, index) in pontosMensagemFrete(freteDetalhe)" :key="`${ponto}-${index}`" class="freight-route-step">
                    <span>{{ index + 1 }}</span>
                    <strong>{{ ponto }}</strong>
                  </div>
                </div>
              </div>

              <div class="freight-detail-section">
                <h3>Checklist</h3>
                <div class="freight-checklist-summary">
                  <span class="checklist-chip" :class="classeChecklistFrete(freteDetalhe)">
                    {{ freteDetalhe.checklist_confirmado ? `${checklistStatusFrete(freteDetalhe)} ${dataHoraChecklistFrete(freteDetalhe)}` : 'Checklist pendente' }}
                  </span>
                  <p v-if="freteDetalhe.checklist_observacoes">{{ freteDetalhe.checklist_observacoes }}</p>
                </div>
              </div>

              <p v-if="freteDetalhe.observacoes" class="freight-detail-note">{{ freteDetalhe.observacoes }}</p>
            </section>

            <aside class="freight-detail-side">
              <div class="freight-detail-panel">
                <div class="modal-allocation-grid">
                  <label class="field">
                    Motorista
                    <select v-model="freteDetalhe.motorista_id" @change="salvarEscalaAutomaticamente(freteDetalhe)">
                      <option :value="null">Selecionar</option>
                      <option v-for="motorista in motoristas" :key="motorista.id" :value="motorista.id">{{ motorista.nome }}</option>
                    </select>
                  </label>
                  <label class="field">
                    Caminhão
                    <select v-model="freteDetalhe.veiculo_id" @change="salvarEscalaAutomaticamente(freteDetalhe)">
                      <option :value="null">Selecionar</option>
                      <option v-for="veiculo in veiculos" :key="veiculo.id" :value="veiculo.id">{{ veiculo.placa }} - {{ veiculo.tipo }}</option>
                    </select>
                  </label>
                  <label class="field">
                    Valor do serviço
                    <input v-model="freteDetalhe.valor_servico" type="number" min="0" step="0.01" placeholder="Opcional" @change="salvarValorFrete(freteDetalhe)" />
                  </label>
                  <label class="field">
                    Nota fiscal
                    <input v-model="freteDetalhe.nota_fiscal" placeholder="Opcional" @change="salvarNotaFiscalFrete(freteDetalhe)" />
                  </label>
                </div>
              </div>

              <div class="actions freight-detail-actions">
                <button class="secondary status-move-button" type="button" @click="abrirMenuStatusFrete($event, freteDetalhe)">Mover status</button>
                <button class="secondary" type="button" @click="editarFrete(freteDetalhe)">Editar frete</button>
                <button class="secondary" type="button" @click="copiarMensagem(freteDetalhe)">Copiar mensagem</button>
                <button class="secondary" type="button" @click="abrirWhatsApp(freteDetalhe)">WhatsApp</button>
                <button class="danger" type="button" @click="excluirFrete(freteDetalhe.id)">Excluir</button>
              </div>
            </aside>
          </div>
        </section>
      </div>

      <div v-if="menuStatusFrete.aberto" class="kanban-context-backdrop" @click="fecharMenuStatusFrete" @contextmenu.prevent="fecharMenuStatusFrete">
        <div
          class="kanban-context-menu"
          :style="{ left: `${menuStatusFrete.x}px`, top: `${menuStatusFrete.y}px`, maxHeight: `${menuStatusFrete.maxHeight}px` }"
          @click.stop
        >
          <div class="kanban-context-head">
            <strong>Mover para</strong>
            <span>{{ menuStatusFrete.frete?.origem }} -> {{ menuStatusFrete.frete?.destino }}</span>
          </div>
          <button
            v-for="status in statusDisponiveisFrete(menuStatusFrete.frete)"
            :key="status"
            type="button"
            :class="{ active: menuStatusFrete.frete?.status === status || (status === STATUS_CONCLUIDO && statusEhConcluido(menuStatusFrete.frete?.status)) }"
            @click="moverFreteParaStatus(menuStatusFrete.frete, status)"
          >
            {{ rotuloStatusFrete(status) }}
          </button>
        </div>
      </div>

      <div v-if="false" class="freight-list">
        <article v-for="frete in fretesFiltrados" :key="frete.id" class="freight-card">
          <div class="freight-main">
            <div>
              <p class="time">{{ frete.horario_coleta.slice(0, 5) }}</p>
              <h3>{{ frete.origem }} → {{ frete.destino }}</h3>
              <p class="muted">{{ frete.empresas_coleta || 'Sem pontos intermediários' }}</p>
            </div>
            <span class="badge" :class="classeStatusVisualFrete(frete.status)">{{ statusVisualFrete(frete.status) }}</span>
          </div>

          <div class="freight-details">
            <span>{{ frete.tipo_caminhao_necessario }}</span>
            <span>Retorno: {{ frete.retorno ? 'Sim' : 'Não' }}</span>
            <span>{{ nomeMotorista(frete.motorista_id) }}</span>
            <span>{{ placaVeiculo(frete.veiculo_id) }}</span>
            <span class="checklist-chip" :class="classeChecklistFrete(frete)">{{ checklistStatusFrete(frete) }}</span>
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
              Caminhão
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
              Valor do serviço
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
</template>
