# Publicação da nova home no domínio oficial

Se `https://saude.barrinha.sp.gov.br/` ainda não atualizou, normalmente o problema é **deploy/cache**, não código.

## 1) Onde publicar
Use o HTML da nova home em `index.html` deste repositório.

## 2) Publicar no WordPress (opção mais rápida)
1. Acesse `https://saude.barrinha.sp.gov.br/wp-admin`.
2. Vá em **Páginas** e edite a página definida como inicial.
3. No editor (bloco HTML personalizado / template), substitua o conteúdo pela estrutura de `index.html`.
4. Publique/Atualize.

## 3) Se a home estiver servida por arquivo no servidor
1. Substitua o arquivo `index.html` no DocumentRoot do site.
2. Garanta permissões de leitura do servidor web.

## 4) Limpar cache (obrigatório)
Após publicar:
- Limpe cache de plugin (ex.: LiteSpeed, W3 Total Cache, WP Rocket).
- Limpe cache do servidor/CDN (Cloudflare, proxy, hospedagem).
- Faça hard refresh no navegador (Ctrl+F5).

## 5) Verificação
- Abra em aba anônima: `https://saude.barrinha.sp.gov.br/`
- Confirme presença dos textos:
  - “A Saúde de Barrinha está entrando em uma nova era.”
  - Menu com “Portal Atual” e “Admin”.

## 6) Diagnóstico rápido quando "não atualizou"
- Está vendo versão antiga só no seu navegador: cache local.
- Todos veem versão antiga: cache de servidor/CDN ou arquivo/página inicial não foi substituído.
- URL abre outro conteúdo: a home ativa no WP não é a página editada.
