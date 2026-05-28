import { createApp } from 'vue'
import './style.css'
import App from './App.vue'
import router from './router'
import { configurarAutenticacaoAxios, restaurarSessao } from './auth'

configurarAutenticacaoAxios()
await restaurarSessao()

createApp(App).use(router).mount('#app')
