<script setup>
import { toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  checklistCarregando,
  checklistErro,
  checklistPublico,
  checklistPublicoTemApontamento,
  checklistResposta,
  checklistRespostaTemApontamento,
  checklistSalvando,
  checklistSucesso,
  confirmarChecklistPublico,
  formatarData,
  itensChecklistCaminhao,
  logoAcelera,
} = toRefs(state)
</script>

<template>
    <section class="checklist-panel">
      <div class="checklist-brand">
        <img :src="logoAcelera" alt="Acelera Transportes" />
        <div>
          <p>Acelera Transportes</p>
          <h1>Checklist caminhão e placa</h1>
        </div>
      </div>

      <p v-if="checklistCarregando" class="checklist-muted">Carregando checklist...</p>
      <p v-if="checklistErro" class="checklist-alert">{{ checklistErro }}</p>
      <p v-if="checklistSucesso" class="checklist-success">{{ checklistSucesso }}</p>

      <div v-if="checklistPublico" class="checklist-card">
        <div class="checklist-trip">
          <strong>{{ checklistPublico.caminhao }} - {{ checklistPublico.placa }}</strong>
          <span
            class="checklist-status"
            :class="checklistPublico.confirmado ? (checklistPublicoTemApontamento ? 'issue' : 'confirmed') : 'pending'"
          >
            {{ checklistPublico.confirmado ? (checklistPublicoTemApontamento ? 'Checklist com apontamento' : 'Checklist confirmado') : 'Checklist pendente' }}
          </span>
          <span>{{ checklistPublico.motorista }}</span>
          <small>{{ formatarData(checklistPublico.data_coleta) }} - {{ String(checklistPublico.horario_coleta).slice(0, 5) }}</small>
          <small>{{ checklistPublico.origem }} -> {{ checklistPublico.destino }}</small>
        </div>

        <div class="checklist-options">
          <div
            v-for="item in itensChecklistCaminhao"
            :key="item.chave"
            class="checklist-option"
            :class="{ checked: checklistResposta[item.chave] === true, issue: checklistResposta[item.chave] === false }"
          >
            <strong>{{ item.rotulo }}</strong>
            <div class="checklist-choices">
              <label class="checklist-choice ok" :class="{ selected: checklistResposta[item.chave] === true }">
                <input v-model="checklistResposta[item.chave]" type="radio" :name="item.chave" :value="true" :disabled="checklistPublico.confirmado" />
                OK
              </label>
              <label class="checklist-choice issue" :class="{ selected: checklistResposta[item.chave] === false }">
                <input v-model="checklistResposta[item.chave]" type="radio" :name="item.chave" :value="false" :disabled="checklistPublico.confirmado" />
                Problema
              </label>
            </div>
          </div>
        </div>

        <label v-if="checklistRespostaTemApontamento || checklistPublico.observacoes" class="field checklist-notes">
          Observação do apontamento
          <textarea
            v-model="checklistResposta.observacoes"
            rows="3"
            :disabled="checklistPublico.confirmado"
            placeholder="Descreva o que não está ok"
          ></textarea>
        </label>

        <button
          type="button"
          :disabled="checklistSalvando || checklistPublico.confirmado"
          @click="confirmarChecklistPublico"
        >
          {{ checklistPublico.confirmado ? 'Checklist confirmado' : checklistSalvando ? 'Confirmando...' : 'Confirmar checklist' }}
        </button>
      </div>
    </section>
</template>
