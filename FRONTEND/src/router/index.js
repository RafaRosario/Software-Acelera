import { createRouter, createWebHistory } from 'vue-router'
import FretesView from '../views/FretesView.vue'
import ConcluidosView from '../views/ConcluidosView.vue'
import CaminhoesView from '../views/CaminhoesView.vue'
import NovoFreteView from '../views/NovoFreteView.vue'
import CadastrosView from '../views/CadastrosView.vue'
import RelatoriosView from '../views/RelatoriosView.vue'
import FornecedoresView from '../views/FornecedoresView.vue'
import PrestadoresServicosView from '../views/PrestadoresServicosView.vue'

const ChecklistRoutePlaceholder = { render: () => null }

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/fretes' },
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

export default router
