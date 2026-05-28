<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import logoAcelera from '../assets/logoacelera.png'
import { authState, loginInterno, rotaInicialPorCargo } from '../auth'

defineProps({
  state: {
    type: Object,
    required: false,
    default: null,
  },
})

const route = useRoute()
const router = useRouter()
const carregando = ref(false)
const erro = ref('')
const email = ref('')
const senha = ref('')
const lembrar = ref(true)

const redirectDestino = computed(() => {
  const destino = String(route.query.redirect || '').trim()
  return destino && destino.startsWith('/') ? destino : null
})

const concluirLogin = async () => {
  const emailNormalizado = String(email.value || '').trim().toLowerCase()
  const senhaNormalizada = String(senha.value || '').trim()
  if (!emailNormalizado || !senhaNormalizada) {
    erro.value = 'Preencha email e senha para continuar.'
    return
  }

  carregando.value = true
  erro.value = ''
  try {
    const usuario = await loginInterno(emailNormalizado, senhaNormalizada)
    const destino = redirectDestino.value
    const rotaPadrao = rotaInicialPorCargo(usuario?.cargo)
    await router.replace(destino || rotaPadrao)
  } catch (error) {
    erro.value = String(error?.response?.data?.detail || 'Falha ao autenticar. Verifique seu email e senha.')
  } finally {
    carregando.value = false
  }
}

onMounted(async () => {
  if (authState.user) {
    await router.replace(rotaInicialPorCargo(authState.user.cargo))
  }
})
</script>

<template>
  <section class="login-page">
    <div class="login-card">
      <div class="login-form">
        <div class="login-brand">
          <img :src="logoAcelera" alt="Acelera Transportes" />
          <div>
            <strong>Login</strong>
            <small>Acesso interno seguro</small>
          </div>
        </div>

        <div class="login-body">
          <p v-if="erro" class="login-alert">{{ erro }}</p>
          <p v-if="carregando" class="login-loading">Validando acesso...</p>

          <form class="login-local-form" @submit.prevent="concluirLogin">
            <label class="field login-field">
              Usuario
              <input v-model="email" type="email" autocomplete="email" placeholder="seuemail@empresa.com" required />
            </label>
            <label class="field login-field">
              Senha
              <input v-model="senha" type="password" autocomplete="current-password" placeholder="Digite sua senha" required />
            </label>
            <label class="login-remember">
              <input v-model="lembrar" type="checkbox" />
              <span>Lembrar-me</span>
            </label>
            <button type="submit" :disabled="carregando">{{ carregando ? 'Entrando...' : 'Entrar no sistema' }}</button>
          </form>

          <a class="login-note" href="#" @click.prevent>Esqueceu sua senha?</a>
        </div>
      </div>
    </div>
  </section>
</template>
