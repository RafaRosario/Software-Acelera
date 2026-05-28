# Deploy: Frontend (Vercel) + Backend (Railway)

Este passo a passo foi preparado para este projeto em `2026-05-28`.

## 1) Pré-check local

1. No backend, garanta que compila:
   `python -m py_compile main.py models.py schemas.py database.py`
2. No frontend, gere build:
   `npm run build`
3. Confirme que o Git está limpo:
   `git status`

## 2) Subir código no GitHub

1. Na raiz do projeto:
   `git add .`
2. Commit:
   `git commit -m "Prepara deploy Vercel e Railway"`
3. Push:
   `git push origin main`

## 3) Deploy do Backend na Railway

1. Acesse [Railway](https://railway.app/) e faça login com GitHub.
2. Clique em `New Project` > `Deploy from GitHub Repo`.
3. Selecione este repositório.
4. Na criação do serviço, configure o **Root Directory** como `API`.
5. Em `Variables`, cadastre:
   - `ACELERA_JWT_SECRET` = uma chave forte
   - `ACELERA_JWT_EXPIRE_HOURS` = `12`
   - `ACELERA_PASSWORD_ITERATIONS` = `240000`
6. Em `Networking`, clique em `Generate Domain`.
7. Copie a URL pública da API, por exemplo:
   `https://seu-backend.up.railway.app`
8. Teste no navegador:
   `https://seu-backend.up.railway.app/docs`

## 4) Deploy do Frontend na Vercel

1. Acesse [Vercel](https://vercel.com/) e faça login com GitHub.
2. Clique em `Add New...` > `Project`.
3. Importe este mesmo repositório.
4. Em `Root Directory`, selecione `FRONTEND`.
5. Em `Environment Variables`, crie:
   - `VITE_API_URL` = URL da Railway (sem barra no final)
6. Deploy.
7. Após deploy, abra a URL do frontend e valide login/listagens.

## 5) Ajuste de CORS (recomendado para produção)

Atualmente a API está com `allow_origins=["*"]`.
Para produção, prefira permitir apenas o domínio Vercel.

Exemplo:
- `https://seu-projeto.vercel.app`

## 6) Checklist final de produção

1. Login funciona.
2. Criação/edição de fretes funciona.
3. Checklist público abre e confirma.
4. Cadastros (motoristas, caminhões, empresas, acessos) funcionando.
5. Exportação de concluídos sem erro.
6. Verificar logs da Railway e Vercel sem falhas críticas.

## 7) Fluxo de atualização contínua

1. Fazer alterações locais.
2. `git add . && git commit -m "..."`
3. `git push origin main`
4. Railway e Vercel redeploy automático via GitHub.

