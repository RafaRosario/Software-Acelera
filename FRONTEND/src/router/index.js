import { createRouter, createWebHistory } from 'vue-router'
import { authState, restaurarSessao, rotaInicialPorCargo, rotaPermitidaParaCargo } from '../auth'
import FretesView from '../views/FretesView.vue'
import ConcluidosView from '../views/ConcluidosView.vue'
import CaminhoesView from '../views/CaminhoesView.vue'
import NovoFreteView from '../views/NovoFreteView.vue'
import CadastrosView from '../views/CadastrosView.vue'
import RelatoriosView from '../views/RelatoriosView.vue'
import FornecedoresView from '../views/FornecedoresView.vue'
import PrestadoresServicosView from '../views/PrestadoresServicosView.vue'
import LoginView from '../views/LoginView.vue'

const ChecklistRoutePlaceholder = { render: () => null }

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/fretes' },
    { path: '/login', component: LoginView },
    { path: '/fretes', component: FretesView },
    { path: '/concluidos', component: ConcluidosView },
    { path: '/caminhoes', component: CaminhoesView },
    { path: '/motoristas', component: RelatoriosView },
    { path: '/novo-frete', component: NovoFreteView },
    { path: '/cadastros', component: CadastrosView },
    { path: '/fornecedores', component: FornecedoresView },
    { path: '/prestadores-servicos', component: PrestadoresServicosView },
    { path: '/checklist/:token', component: ChecklistRoutePlaceholder },
    { path: '/:pathMatch(.*)*', redirect: '/fretes' },
  ],
})

router.beforeEach(async (to) => {
  if (to.path.startsWith('/checklist/')) return true

  const usuario = authState.pronto ? authState.user : await restaurarSessao()

  if (!usuario) {
    if (to.path === '/login') return true
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  if (to.path === '/login') {
    return { path: rotaInicialPorCargo(usuario.cargo), replace: true }
  }

  if (!rotaPermitidaParaCargo(to.path, usuario.cargo)) {
    return { path: rotaInicialPorCargo(usuario.cargo), replace: true }
  }

  return true
})

export default router
