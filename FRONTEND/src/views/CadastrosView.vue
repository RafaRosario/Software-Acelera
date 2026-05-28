<script setup>
import { toRefs } from 'vue'

const { state } = defineProps({
  state: {
    type: Object,
    required: true,
  },
})

const {
  aplicarMascaraCpfMotorista,
  aplicarMascaraRgMotorista,
  buscarCepEmpresa,
  cadastrarEmpresa,
  cadastrarMotorista,
  cadastrarUsuarioSistema,
  cadastrarVeiculo,
  cadastroAtivo,
  buscaEmpresasCadastro,
  buscaMotoristasCadastro,
  buscaVeiculosCadastro,
  editarEmpresa,
  editarMotorista,
  editarUsuarioSistema,
  editarVeiculo,
  ehAdmin,
  empresaEditandoId,
  empresas,
  empresasCadastroFiltradas,
  enderecoEmpresa,
  excluirEmpresa,
  excluirMotorista,
  excluirVeiculo,
  limparEmpresa,
  limparMotorista,
  limparUsuarioSistema,
  limparVeiculo,
  motoristaEditandoId,
  motoristas,
  motoristasCadastroFiltrados,
  novaEmpresa,
  novoMotorista,
  novoUsuarioSistema,
  novoVeiculo,
  selecionarCadastroAtivo,
  tiposVeiculo,
  usuarioSistemaEditandoId,
  usuariosSistema,
  veiculoEditandoId,
  veiculosCadastroFiltrados,
  veiculos,
} = toRefs(state)
</script>

<template>
    <section class="workspace">
      <div class="section-head">
        <div>
          <h2>Cadastros</h2>
          <p>Escolha o tipo de cadastro que deseja criar ou consultar.</p>
        </div>
      </div>

      <div class="cadastro-switch">
        <button :class="{ active: cadastroAtivo === 'motoristas' }" type="button" @click="selecionarCadastroAtivo('motoristas')">Motoristas</button>
        <button :class="{ active: cadastroAtivo === 'veiculos' }" type="button" @click="selecionarCadastroAtivo('veiculos')">Caminhões</button>
        <button :class="{ active: cadastroAtivo === 'empresas' }" type="button" @click="selecionarCadastroAtivo('empresas')">Empresas</button>
        <button v-if="ehAdmin" :class="{ active: cadastroAtivo === 'acessos' }" type="button" @click="selecionarCadastroAtivo('acessos')">Acessos</button>
      </div>

      <div v-if="cadastroAtivo === 'motoristas'" class="registry-layout">
        <div class="registry-form-card">
          <div class="registry-card-head">
            <span>01</span>
            <div>
              <h2>Motoristas</h2>
              <p>MOTORISTA</p>
            </div>
          </div>
        <form class="stack-form" @submit.prevent="cadastrarMotorista">
          <input v-model="novoMotorista.nome" placeholder="Nome" required />
          <input v-model="novoMotorista.telefone" placeholder="Telefone/WhatsApp" required />
          <input v-model="novoMotorista.rg" placeholder="RG" required maxlength="12" @input="aplicarMascaraRgMotorista" />
          <input v-model="novoMotorista.cpf" placeholder="CPF" required maxlength="14" @input="aplicarMascaraCpfMotorista" />
          <input v-model="novoMotorista.cnh" placeholder="CNH" />
          <textarea v-model="novoMotorista.observacoes" placeholder="Observações" rows="3"></textarea>
          <div class="form-actions">
            <button type="submit">{{ motoristaEditandoId ? 'Salvar motorista' : 'Cadastrar motorista' }}</button>
            <button v-if="motoristaEditandoId" class="secondary" type="button" @click="limparMotorista">Cancelar edição</button>
          </div>
        </form>
        </div>
        <aside class="registry-directory">
          <div class="registry-directory-head">
            <div>
              <strong>Motoristas cadastrados</strong>
              <small>{{ motoristasCadastroFiltrados.length }} de {{ motoristas.length }} registros</small>
            </div>
            <label class="field compact registry-search">
              Buscar
              <input v-model="buscaMotoristasCadastro" type="search" placeholder="Nome, telefone, CPF, RG..." />
            </label>
          </div>
        <ul class="simple-list registry-list">
          <li v-for="motorista in motoristasCadastroFiltrados" :key="motorista.id">
            <span>
              {{ motorista.nome }}
              <small>{{ motorista.telefone }}</small>
              <small v-if="motorista.observacoes" class="registry-note">Obs: {{ motorista.observacoes }}</small>
            </span>
            <div class="registry-actions">
              <button class="secondary compact-button" type="button" @click="editarMotorista(motorista)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirMotorista(motorista.id)">Excluir</button>
            </div>
          </li>
        </ul>
        <p v-if="motoristasCadastroFiltrados.length === 0" class="empty">Nenhum motorista encontrado.</p>
        </aside>
      </div>

      <div v-if="cadastroAtivo === 'veiculos'" class="registry-layout">
        <div class="registry-form-card">
          <div class="registry-card-head">
            <span>02</span>
            <div>
              <h2>Caminhões</h2>
              <p>CAMINHÃO</p>
            </div>
          </div>
        <form class="stack-form" @submit.prevent="cadastrarVeiculo">
          <input v-model="novoVeiculo.placa" placeholder="Placa ou identificação (ex: Terceiros)" required />
          <select v-model="novoVeiculo.tipo" required>
            <option v-for="tipo in tiposVeiculo" :key="tipo" :value="tipo">{{ tipo }}</option>
          </select>
          <textarea v-model="novoVeiculo.observacoes" placeholder="Observações" rows="3"></textarea>
          <label class="field">
            Observação
            <textarea
              v-model="novoVeiculo.observacao_estado"
              rows="3"
            ></textarea>
          </label>
          <div class="form-actions">
            <button type="submit">{{ veiculoEditandoId ? 'Salvar caminhão' : 'Cadastrar caminhão' }}</button>
            <button v-if="veiculoEditandoId" class="secondary" type="button" @click="limparVeiculo">Cancelar edição</button>
          </div>
        </form>
        </div>
        <aside class="registry-directory">
          <div class="registry-directory-head">
            <div>
              <strong>Caminhões cadastrados</strong>
              <small>{{ veiculosCadastroFiltrados.length }} de {{ veiculos.length }} registros</small>
            </div>
            <label class="field compact registry-search">
              Buscar
              <input v-model="buscaVeiculosCadastro" type="search" placeholder="Placa, tipo, observações, estado..." />
            </label>
          </div>
        <ul class="simple-list registry-list">
          <li v-for="veiculo in veiculosCadastroFiltrados" :key="veiculo.id">
            <span>
              {{ veiculo.placa }}
              <small>{{ veiculo.tipo }}</small>
              <small v-if="veiculo.observacoes" class="registry-note">Obs: {{ veiculo.observacoes }}</small>
              <small v-if="veiculo.observacao_estado" class="registry-note">Estado: {{ veiculo.observacao_estado }}</small>
            </span>
            <div class="registry-actions">
              <button class="secondary compact-button" type="button" @click="editarVeiculo(veiculo)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirVeiculo(veiculo.id)">Excluir</button>
            </div>
          </li>
        </ul>
        <p v-if="veiculosCadastroFiltrados.length === 0" class="empty">Nenhum caminhão encontrado.</p>
        </aside>
      </div>

      <div v-if="cadastroAtivo === 'empresas'" class="registry-layout">
        <div class="registry-form-card">
          <div class="registry-card-head">
            <span>03</span>
            <div>
              <h2>Empresas</h2>
              <p>EMPRESAS</p>
            </div>
          </div>
        <form class="stack-form" @submit.prevent="cadastrarEmpresa">
          <input v-model="novaEmpresa.nome" placeholder="Nome da empresa" required />
          <input v-model="novaEmpresa.cnpj" placeholder="CNPJ" required />
          <label class="check-field compact-check"><input v-model="novaEmpresa.cliente" type="checkbox" />Cliente</label>
          <div class="cep-row">
            <input v-model="novaEmpresa.cep" placeholder="CEP" required @blur="buscarCepEmpresa" />
            <button class="secondary" type="button" @click="buscarCepEmpresa">Buscar CEP</button>
          </div>
          <input v-model="novaEmpresa.logradouro" placeholder="Rua / avenida" required />
          <div class="address-grid">
            <input v-model="novaEmpresa.numero" placeholder="Número" required />
            <input v-model="novaEmpresa.complemento" placeholder="Complemento" />
          </div>
          <input v-model="novaEmpresa.bairro" placeholder="Bairro" required />
          <div class="address-grid">
            <input v-model="novaEmpresa.cidade" placeholder="Cidade" required />
            <input v-model="novaEmpresa.uf" placeholder="UF" maxlength="2" required />
          </div>
          <textarea v-model="novaEmpresa.observacoes" placeholder="Observações" rows="3"></textarea>
          <div class="form-actions">
            <button type="submit">{{ empresaEditandoId ? 'Salvar empresa' : 'Cadastrar empresa' }}</button>
            <button v-if="empresaEditandoId" class="secondary" type="button" @click="limparEmpresa">Cancelar edição</button>
          </div>
        </form>
        </div>
        <aside class="registry-directory">
          <div class="registry-directory-head">
            <div>
              <strong>Empresas cadastradas</strong>
              <small>{{ empresasCadastroFiltradas.length }} de {{ empresas.length }} registros</small>
            </div>
            <label class="field compact registry-search">
              Buscar
              <input v-model="buscaEmpresasCadastro" type="search" placeholder="Nome, CNPJ, cidade, endereço..." />
            </label>
          </div>
        <ul class="simple-list registry-list">
          <li v-for="empresa in empresasCadastroFiltradas" :key="empresa.id">
            <span>
              {{ empresa.nome }}
              <small>{{ empresa.cnpj }} - {{ enderecoEmpresa(empresa) }}</small>
              <small v-if="empresa.cliente" class="registry-note">Cliente</small>
              <small v-if="empresa.observacoes" class="registry-note">Obs: {{ empresa.observacoes }}</small>
            </span>
            <div class="registry-actions">
              <button class="secondary compact-button" type="button" @click="editarEmpresa(empresa)">Editar</button>
              <button class="danger compact-button" type="button" @click="excluirEmpresa(empresa.id)">Excluir</button>
            </div>
          </li>
        </ul>
        <p v-if="empresasCadastroFiltradas.length === 0" class="empty">Nenhuma empresa encontrada.</p>
        </aside>
      </div>

      <div v-if="cadastroAtivo === 'acessos' && ehAdmin" class="registry-layout">
        <div class="registry-form-card">
          <div class="registry-card-head">
            <span>04</span>
            <div>
              <h2>Acessos</h2>
              <p>LOGIN</p>
            </div>
          </div>
          <form class="stack-form" @submit.prevent="cadastrarUsuarioSistema">
            <input v-model="novoUsuarioSistema.nome" placeholder="Nome do usuario" required />
            <input v-model="novoUsuarioSistema.email" placeholder="Email de acesso" required />
            <input
              v-model="novoUsuarioSistema.senha"
              :placeholder="usuarioSistemaEditandoId ? 'Nova senha (opcional)' : 'Senha de acesso (min. 6 caracteres)'"
              :required="!usuarioSistemaEditandoId"
              minlength="6"
              type="password"
            />
            <label class="field">
              Cargo
              <select v-model="novoUsuarioSistema.cargo" required>
                <option value="admin">Admin</option>
                <option value="controle">Controle</option>
                <option value="motorista">Motorista</option>
              </select>
            </label>
            <label class="field">
              Motorista vinculado
              <select v-model="novoUsuarioSistema.motorista_id" :disabled="novoUsuarioSistema.cargo !== 'motorista'">
                <option value="">Nao vincular</option>
                <option v-for="motorista in motoristas" :key="motorista.id" :value="motorista.id">{{ motorista.nome }}</option>
              </select>
            </label>
            <label class="check-field compact-check"><input v-model="novoUsuarioSistema.ativo" type="checkbox" />Acesso ativo</label>
            <div class="form-actions">
              <button type="submit">{{ usuarioSistemaEditandoId ? 'Salvar acesso' : 'Cadastrar acesso' }}</button>
              <button class="secondary" type="button" @click="limparUsuarioSistema">Cancelar</button>
            </div>
          </form>
        </div>

        <aside class="registry-directory">
          <div class="registry-directory-head">
            <div>
              <strong>Usuarios com acesso</strong>
              <small>{{ usuariosSistema.length }} registros</small>
            </div>
          </div>
          <ul class="simple-list registry-list">
            <li v-for="usuario in usuariosSistema" :key="usuario.id">
              <span>
                {{ usuario.nome }}
                <small>{{ usuario.email }}</small>
                <small class="registry-note">Cargo: {{ usuario.cargo }}<span v-if="usuario.motorista_nome"> | Motorista: {{ usuario.motorista_nome }}</span></small>
                <small class="registry-note">{{ usuario.ativo ? 'Ativo' : 'Inativo' }}</small>
              </span>
              <div class="registry-actions">
                <button class="secondary compact-button" type="button" @click="editarUsuarioSistema(usuario)">Editar</button>
              </div>
            </li>
          </ul>
          <p v-if="usuariosSistema.length === 0" class="empty">Nenhum acesso cadastrado.</p>
        </aside>
      </div>
    </section>
</template>
