import axios from 'axios'
import { reactive } from 'vue'

const TOKEN_STORAGE_KEY = 'acelera_access_token'
const rotasPermitidasPorCargo = {
  admin: [
    '/fretes',
    '/concluidos',
    '/caminhoes',
    '/motoristas',
    '/novo-frete',
    '/cadastros',
    '/fornecedores',
    '/prestadores-servicos',
  ],
  controle: ['/fretes', '/concluidos'],
  motorista: ['/fretes'],
}

export const authState = reactive({
  token: localStorage.getItem(TOKEN_STORAGE_KEY) || '',
  user: null,
  pronto: false,
})

const normalizarApiUrl = (valor) => {
  const raw = String(valor || '').trim()
  if (!raw) return 'http://127.0.0.1:8000'
  if (/^https?:\/\//i.test(raw)) return raw.replace(/\/+$/, '')
  if (/^(localhost|127\.0\.0\.1)(:\d+)?(\/.*)?$/i.test(raw)) return `http://${raw}`.replace(/\/+$/, '')
  return `https://${raw}`.replace(/\/+$/, '')
}

export const API_URL = normalizarApiUrl(import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000')

const normalizarRota = (path) => {
  const rota = String(path || '').trim()
  if (!rota || rota === '/') return '/fretes'
  if (rota.endsWith('/') && rota !== '/') return rota.slice(0, -1)
  return rota
}

const aplicarTokenAxios = (token) => {
  axios.defaults.baseURL = API_URL
  if (token) {
    axios.defaults.headers.common.Authorization = `Bearer ${token}`
  } else {
    delete axios.defaults.headers.common.Authorization
  }
}

const definirToken = (token) => {
  authState.token = token || ''
  if (authState.token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, authState.token)
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY)
  }
  aplicarTokenAxios(authState.token)
}

export const encerrarSessao = () => {
  definirToken('')
  authState.user = null
  authState.pronto = true
}

let interceptadorAtivo = false
export const configurarAutenticacaoAxios = () => {
  if (interceptadorAtivo) return
  interceptadorAtivo = true
  aplicarTokenAxios(authState.token)

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error?.response?.status
      const rota = String(error?.config?.url || '')
      if (status === 401 && !rota.includes('/auth/login')) {
        encerrarSessao()
      }
      return Promise.reject(error)
    },
  )
}

export const rotaInicialPorCargo = (cargo) => {
  if (cargo === 'admin') return '/fretes'
  if (cargo === 'controle') return '/fretes'
  if (cargo === 'motorista') return '/fretes'
  return '/fretes'
}

export const rotaPermitidaParaCargo = (path, cargo) => {
  if (!cargo) return false
  if (/^\/checklists?\//.test(String(path || ''))) return true
  const rota = normalizarRota(path)
  const rotas = rotasPermitidasPorCargo[cargo] || []
  return rotas.includes(rota)
}

export const restaurarSessao = async () => {
  if (authState.pronto) return authState.user
  if (!authState.token) {
    authState.pronto = true
    return null
  }

  aplicarTokenAxios(authState.token)
  try {
    const response = await axios.get('/auth/me')
    authState.user = response.data
    return authState.user
  } catch {
    encerrarSessao()
    return null
  } finally {
    authState.pronto = true
  }
}

export const loginInterno = async (email, senha) => {
  const response = await axios.post('/auth/login', { email, senha })
  const token = response?.data?.access_token || ''
  const user = response?.data?.user || null

  definirToken(token)
  authState.user = user
  authState.pronto = true
  return user
}
