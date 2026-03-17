# SIGEF - Sistema Integrado de Gestão de Frequência

Sistema offline para prefeituras com Flask + SQLite.

## Requisitos
- Python 3.10+

## Instalação e execução
```bash
pip install -r requirements.txt
python app.py
```

Acesse: http://localhost:5000

## Usuários de teste
- Admin: `admin` / `admin123`
- Encarregado: `encarregado` / `enc123`

## Funcionalidades
- Login com sessão e senha bcrypt
- Perfis Admin e Encarregado (escopo por setor)
- CRUD sem delete físico para Setores, Funcionários, Frequências, Ocorrências e Plantões
- Dashboard operacional
- Auditoria completa para INSERT e UPDATE
- Relatórios CSV e PDF (PDF como HTML imprimível)
- Backup automático do SQLite em `backups/`

## Estrutura
- `routes/` rotas Flask
- `models/` banco e seed
- `services/` autenticação, auditoria e backup
- `templates/` telas Bootstrap
- `static/` assets
