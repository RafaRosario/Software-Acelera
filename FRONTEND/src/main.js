import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { configurarAutenticacaoAxios, isChecklistPublicPath, restaurarSessao } from './auth'

configurarAutenticacaoAxios()
if (!isChecklistPublicPath(window.location.pathname)) {
  await restaurarSessao()
}

createApp(App).use(router).mount('#app')
