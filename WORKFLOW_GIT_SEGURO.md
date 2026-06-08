# Workflow seguro para evolucao continua

Este fluxo evita mexer no que ja esta online antes da validacao.

## 1) Estrategia de branches

- `main`: producao (o que esta online)
- `staging`: homologacao (pre-producao)
- `feature/*`: ajustes por tarefa
- `hotfix/*`: correcao urgente de producao

## 2) Preparacao inicial (fazer uma vez)

```powershell
cd "C:\Software acelera"
git checkout -b staging
git push -u origin staging
```

No GitHub (Settings > Branches):

- Proteger `main` e `staging`
- Bloquear push direto
- Exigir Pull Request para merge

## 3) Fluxo padrao de trabalho

### 3.1 Criar uma tarefa visual

```powershell
cd "C:\Software acelera"
git checkout staging
git pull origin staging
git checkout -b feature/ajuste-visual-home
```

### 3.2 Desenvolver e validar local

- Rodar API e frontend localmente
- Validar desktop e mobile
- Fazer commit pequeno e objetivo

```powershell
git add .
git commit -m "Ajusta layout da home no mobile"
git push -u origin feature/ajuste-visual-home
```

### 3.3 Abrir Pull Request para staging

- `feature/ajuste-visual-home` -> `staging`
- Revisar mudancas
- Validar no ambiente de homologacao (Vercel preview + backend de homologacao)
- Merge apenas depois de aprovado

### 3.4 Publicar em producao

- Abrir PR `staging` -> `main`
- Fazer checklist final
- Merge para `main`
- Deploy automatico em producao

## 4) Ambientes recomendados

- Producao:
  - Frontend: Vercel ligado na branch `main`
  - Backend: Railway ligado na branch `main`
- Homologacao:
  - Frontend: Vercel ligado na branch `staging` (ou Preview PR)
  - Backend: Railway ligado na branch `staging`

Se nao quiser dois servicos no Railway agora, use pelo menos Preview da Vercel para testar visual sem tocar em `main`.

## 5) Checklist rapido antes de qualquer merge para main

1. Build do frontend sem erro (`npm run build` em `FRONTEND`)
2. Backend sem erro de sintaxe (`python -m py_compile main.py models.py schemas.py database.py` em `API`)
3. Fluxos criticos funcionando (login, cadastro, listagem, edicao)
4. Responsividade ok (mobile e desktop)
5. Sem alteracao acidental em `.env` ou arquivos de segredo

## 6) Hotfix (quando algo quebrar em producao)

```powershell
cd "C:\Software acelera"
git checkout main
git pull origin main
git checkout -b hotfix/correcao-login
```

- Corrigir, commitar e subir
- PR `hotfix/...` -> `main`
- Depois do merge em `main`, abrir PR `main` -> `staging` para manter as branches alinhadas

## 7) Padrao de mensagens de commit

- `feat: ...` nova funcionalidade
- `fix: ...` correcao
- `style: ...` ajuste visual/CSS sem regra de negocio
- `refactor: ...` melhoria interna sem alterar comportamento

Exemplo:

```text
style: melhora contraste e espacamento do card de fretes
```
