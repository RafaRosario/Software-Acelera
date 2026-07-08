<script setup>
import { nextTick, onMounted, ref } from 'vue'
import { API_URL, authState } from '../auth'

const emit = defineEmits(['fechar'])

const mensagens = ref([])
const textoDigitado = ref('')
const respondendo = ref(false)
const erroChat = ref('')
const areaMensagens = ref(null)
const campoTexto = ref(null)
let controladorAbort = null

// Historico salvo por usuario: a conversa sobrevive a recarregar a pagina.
const CHAT_HISTORICO_MAX = 60
const chaveHistorico = () => `acelera_chat_historico_${authState.user?.id || 'anon'}`

const salvarHistorico = () => {
  try {
    const completas = mensagens.value.filter((m) => m.texto).slice(-CHAT_HISTORICO_MAX)
    localStorage.setItem(chaveHistorico(), JSON.stringify(completas))
  } catch {
    /* armazenamento cheio/indisponivel: segue sem salvar */
  }
}

const restaurarHistorico = () => {
  try {
    const salvo = JSON.parse(localStorage.getItem(chaveHistorico()) || '[]')
    if (Array.isArray(salvo)) {
      mensagens.value = salvo.filter((m) => m && m.texto && (m.papel === 'user' || m.papel === 'assistant'))
    }
  } catch {
    mensagens.value = []
  }
}

const sugestoes = [
  'Quantos fretes temos hoje?',
  'Quantos fretes esta semana?',
  'Quais caminhoes estao disponiveis?',
  'Ocorrencias de veiculos em aberto',
]

const rolarParaFim = async () => {
  await nextTick()
  const area = areaMensagens.value
  if (area) area.scrollTop = area.scrollHeight
}

const enviarPergunta = async (texto) => {
  const pergunta = String(texto || textoDigitado.value || '').trim()
  if (!pergunta || respondendo.value) return

  erroChat.value = ''
  textoDigitado.value = ''
  mensagens.value.push({ papel: 'user', texto: pergunta })
  const resposta = { papel: 'assistant', texto: '' }
  mensagens.value.push(resposta)
  respondendo.value = true
  rolarParaFim()

  controladorAbort = new AbortController()

  try {
    const historico = mensagens.value
      .slice(0, -1)
      .filter((m) => m.texto)
      .slice(-20)
      .map((m) => ({ papel: m.papel, texto: m.texto }))

    const respostaHttp = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authState.token}`,
      },
      body: JSON.stringify({ mensagens: historico }),
      signal: controladorAbort.signal,
    })

    if (!respostaHttp.ok) {
      let detalhe = 'Nao foi possivel consultar o assistente.'
      try {
        const corpo = await respostaHttp.json()
        detalhe = corpo?.detail || detalhe
      } catch {
        /* resposta sem JSON */
      }
      throw new Error(detalhe)
    }

    const leitor = respostaHttp.body.getReader()
    const decodificador = new TextDecoder()

    while (true) {
      const { done, value } = await leitor.read()
      if (done) break
      resposta.texto += decodificador.decode(value, { stream: true })
      rolarParaFim()
    }

    if (!resposta.texto.trim()) {
      resposta.texto = 'Nao consegui gerar uma resposta. Tente reformular a pergunta.'
    }
  } catch (error) {
    if (error?.name !== 'AbortError') {
      erroChat.value = String(error?.message || 'Erro ao conectar com o assistente.')
      if (!resposta.texto) mensagens.value.pop()
    }
  } finally {
    respondendo.value = false
    controladorAbort = null
    salvarHistorico()
    rolarParaFim()
  }
}

const aoTeclar = (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    enviarPergunta()
  }
}

const limparConversa = () => {
  if (controladorAbort) controladorAbort.abort()
  mensagens.value = []
  erroChat.value = ''
  try {
    localStorage.removeItem(chaveHistorico())
  } catch {
    /* sem armazenamento disponivel */
  }
}

onMounted(() => {
  restaurarHistorico()
  rolarParaFim()
  campoTexto.value?.focus()
})
</script>

<template>
  <div class="chat-assistente" role="dialog" aria-label="Assistente Acelera">
    <header class="chat-topo">
      <div class="chat-titulo">
        <span class="chat-status-dot" aria-hidden="true"></span>
        <div>
          <strong>Assistente Acelera</strong>
          <small>Pergunte sobre fretes, motoristas e caminhoes</small>
        </div>
      </div>
      <div class="chat-topo-acoes">
        <button
          v-if="mensagens.length"
          class="chat-icon-btn"
          type="button"
          title="Limpar conversa"
          aria-label="Limpar conversa"
          @click="limparConversa"
        >
          &#8635;
        </button>
        <button class="chat-icon-btn" type="button" title="Fechar" aria-label="Fechar chat" @click="emit('fechar')">
          &#10005;
        </button>
      </div>
    </header>

    <div ref="areaMensagens" class="chat-mensagens">
      <div v-if="!mensagens.length" class="chat-vazio">
        <p>Ola! Consulto os dados do sistema pra voce. Experimente:</p>
        <div class="chat-sugestoes">
          <button
            v-for="sugestao in sugestoes"
            :key="sugestao"
            type="button"
            @click="enviarPergunta(sugestao)"
          >
            {{ sugestao }}
          </button>
        </div>
      </div>

      <div
        v-for="(mensagem, indice) in mensagens"
        :key="indice"
        class="chat-balao"
        :class="mensagem.papel === 'user' ? 'de-usuario' : 'de-assistente'"
      >
        <template v-if="mensagem.texto">{{ mensagem.texto }}</template>
        <span v-else-if="respondendo && indice === mensagens.length - 1" class="chat-digitando" aria-label="Consultando">
          <i></i><i></i><i></i>
        </span>
      </div>

      <p v-if="erroChat" class="chat-erro">{{ erroChat }}</p>
    </div>

    <footer class="chat-rodape">
      <textarea
        ref="campoTexto"
        v-model="textoDigitado"
        rows="1"
        placeholder="Pergunte algo..."
        :disabled="respondendo"
        @keydown="aoTeclar"
      ></textarea>
      <button
        class="chat-enviar"
        type="button"
        :disabled="respondendo || !textoDigitado.trim()"
        aria-label="Enviar pergunta"
        @click="enviarPergunta()"
      >
        &#10148;
      </button>
    </footer>
  </div>
</template>

<style scoped>
.chat-assistente {
  position: fixed;
  inset: 0;
  z-index: 90;
  display: flex;
  flex-direction: column;
  background: var(--surface, #fff);
  overscroll-behavior: contain;
}

.chat-topo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  padding-top: calc(14px + env(safe-area-inset-top, 0px));
  background: var(--surface-strong, #12241d);
  color: #fff;
  flex-shrink: 0;
}

.chat-titulo {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.chat-titulo strong {
  display: block;
  font-size: 15px;
}

.chat-titulo small {
  display: block;
  font-size: 11.5px;
  opacity: 0.75;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chat-status-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #3ddc84;
  flex-shrink: 0;
}

.chat-topo-acoes {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
}

.chat-icon-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.14);
  color: #fff;
  font-size: 15px;
  cursor: pointer;
  display: grid;
  place-items: center;
}

.chat-icon-btn:hover {
  background: rgba(255, 255, 255, 0.26);
}

.chat-mensagens {
  flex: 1;
  overflow-y: auto;
  padding: 16px 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--bg, #edf3ee);
  -webkit-overflow-scrolling: touch;
}

.chat-vazio {
  margin: auto 0;
  text-align: center;
  color: var(--muted, #5e6d66);
  font-size: 14px;
  padding: 0 8px;
}

.chat-sugestoes {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 14px;
}

.chat-sugestoes button {
  border: 1px solid var(--line, #d2ddd5);
  background: var(--surface, #fff);
  color: var(--text, #111a17);
  border-radius: 999px;
  padding: 8px 14px;
  font-size: 13px;
  cursor: pointer;
}

.chat-sugestoes button:hover {
  border-color: var(--primary, #078546);
  color: var(--primary-dark, #056437);
}

.chat-balao {
  max-width: 86%;
  padding: 10px 13px;
  border-radius: 14px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.chat-balao.de-usuario {
  align-self: flex-end;
  background: var(--primary, #078546);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-balao.de-assistente {
  align-self: flex-start;
  background: var(--surface, #fff);
  color: var(--text, #111a17);
  border: 1px solid var(--line, #d2ddd5);
  border-bottom-left-radius: 4px;
}

.chat-digitando {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  height: 14px;
}

.chat-digitando i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--muted, #5e6d66);
  animation: chat-pulo 1.1s infinite ease-in-out;
}

.chat-digitando i:nth-child(2) {
  animation-delay: 0.18s;
}

.chat-digitando i:nth-child(3) {
  animation-delay: 0.36s;
}

@keyframes chat-pulo {
  0%,
  60%,
  100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-4px);
    opacity: 1;
  }
}

.chat-erro {
  align-self: center;
  color: var(--danger, #d93932);
  font-size: 13px;
  text-align: center;
  margin: 4px 0 0;
}

.chat-rodape {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 10px 12px;
  padding-bottom: calc(10px + env(safe-area-inset-bottom, 0px));
  background: var(--surface, #fff);
  border-top: 1px solid var(--line, #d2ddd5);
  flex-shrink: 0;
}

.chat-rodape textarea {
  flex: 1;
  resize: none;
  border: 1px solid var(--line, #d2ddd5);
  border-radius: 12px;
  padding: 10px 12px;
  font: inherit;
  font-size: 14px;
  max-height: 110px;
  background: var(--surface-soft, #f1f6f2);
  color: var(--text, #111a17);
}

.chat-rodape textarea:focus {
  outline: 2px solid var(--primary, #078546);
  outline-offset: -1px;
}

.chat-enviar {
  width: 42px;
  height: 42px;
  border: none;
  border-radius: 12px;
  background: var(--primary, #078546);
  color: #fff;
  font-size: 17px;
  cursor: pointer;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.chat-enviar:disabled {
  opacity: 0.45;
  cursor: default;
}

/* Desktop: painel flutuante no canto inferior direito */
@media (min-width: 861px) {
  .chat-assistente {
    inset: auto 24px 24px auto;
    width: 390px;
    height: min(620px, calc(100vh - 48px));
    border-radius: 18px;
    overflow: hidden;
    box-shadow: var(--shadow, 0 18px 46px rgba(17, 33, 26, 0.18)), 0 6px 18px rgba(0, 0, 0, 0.12);
    border: 1px solid var(--line, #d2ddd5);
  }

  .chat-topo {
    padding-top: 14px;
  }
}
</style>
