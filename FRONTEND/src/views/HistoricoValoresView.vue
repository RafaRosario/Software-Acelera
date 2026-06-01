<script setup>
import { toRefs } from 'vue'
import { ref } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  buscaHistoricoValores,
  formatarDataHora,
  formatarMoeda,
  historicoValoresFiltrado,
  salvarTemplateValorHistorico,
} = toRefs(state)

const templatesExpandidos = ref({})

const templateExpandido = (id) => Boolean(templatesExpandidos.value[String(id)])

const alternarTemplateExpandido = (id) => {
  const chave = String(id)
  templatesExpandidos.value = {
    ...templatesExpandidos.value,
    [chave]: !templatesExpandidos.value[chave],
  }
}
</script>

<template>
  <section class="workspace">
    <div class="section-head">
      <div>
        <h2>Histórico de valores</h2>
        <p>Valores aprendidos automaticamente para sugestão em novos fretes concluídos.</p>
      </div>
    </div>

    <div class="period-filter historico-toolbar">
      <label class="field historico-search-field">
        Buscar
        <input
          v-model="buscaHistoricoValores"
          class="historico-search-input"
          type="search"
          placeholder="Empresa, tipo, origem, destino..."
        />
      </label>
    </div>

    <div class="historico-valores-grid">
      <article v-for="template in historicoValoresFiltrado" :key="template.id" class="historico-valor-card">
        <div class="historico-valor-head">
          <div>
            <strong>{{ template.empresa_id }}</strong>
            <small>{{ template.caminhao_contratado_id }}</small>
          </div>
          <span class="badge aguardando">Usos: {{ template.qtd_usos || 0 }}</span>
        </div>

        <div class="historico-rota">
          <span>{{ template.origem_id }}</span>
          <b>→</b>
          <span>{{ template.destino_id }}</span>
        </div>

        <div class="historico-flags">
          <span :class="template.tem_retorno ? 'flag-yes' : 'flag-no'">Retorno: {{ template.tem_retorno ? 'Sim' : 'Não' }}</span>
          <span :class="template.tem_ponto_adicional ? 'flag-yes' : 'flag-no'">Ponto adicional: {{ template.tem_ponto_adicional ? 'Sim' : 'Não' }}</span>
        </div>

        <div v-if="templateExpandido(template.id)" class="historico-inputs">
          <label class="field">
            Frete
            <input v-model="template.valor_padrao" type="number" min="0" step="0.01" placeholder="0,00" />
          </label>
          <label class="field">
            Retorno
            <input v-model="template.valor_retorno" type="number" min="0" step="0.01" placeholder="0,00" />
          </label>
          <label class="field">
            Ponto
            <input v-model="template.valor_ponto_adicional" type="number" min="0" step="0.01" placeholder="0,00" />
          </label>
          <div class="historico-inputs-actions">
            <button type="button" @click="salvarTemplateValorHistorico(template)">Salvar valores</button>
          </div>
        </div>

        <div class="historico-valor-footer">
          <small>Atualizado: {{ formatarDataHora(template.updated_at) }}</small>
          <button class="secondary" type="button" @click="alternarTemplateExpandido(template.id)">
            {{ templateExpandido(template.id) ? 'Ocultar valores' : 'Ver valores' }}
          </button>
        </div>
      </article>

      <p v-if="historicoValoresFiltrado.length === 0" class="empty">Nenhum template encontrado.</p>
    </div>
  </section>
</template>
