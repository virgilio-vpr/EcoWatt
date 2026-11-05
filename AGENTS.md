# Orientações do EcoWatt

## Como iniciar uma tarefa

1. Consulte `docs/STATUS.md` e o plano da fase correspondente em `docs/phases/`.
2. Leia apenas as seções da SPEC indicadas no plano e os arquivos de código envolvidos na entrega. Use `rg` para localizar símbolos e referências antes de abrir arquivos inteiros.
3. Amplie a leitura quando houver dependência, dúvida, conflito ou mudança transversal. Não é necessário reler toda a SPEC ou todo o código a cada solicitação; não deixe de consultar regras relevantes para economizar contexto.
4. Confira a implementação real antes de agir: o status é um resumo, não prova de que o código está correto.

## Fontes e referências

- `EcoWatt_PROJECT_SPEC.md`: fonte principal dos requisitos e critérios de aceite, especialmente seção 15.
- `docs/phases/README.md`: mapa das fases e modelo de pedido para um novo chat.
- `docs/STATUS.md`: estado atual, última entrega, verificações e próximo passo.
- `README.md`: entrada do projeto e instruções de utilização.
- Instruções atuais do usuário prevalecem sobre estas orientações e a SPEC. Ajuste a documentação afetada quando houver mudança de requisito; não altere escopo por conta própria.
- Planos de fase são mapas de leitura e execução. Não copie a SPEC para eles. Cite número e título de seção, evitando números de linha que mudam com edições.

## Regras essenciais

- Backend primeiro: Python/FastAPI, SQLAlchemy 2 e Alembic. SQLite local agora; PostgreSQL/Docker na preparação de produção. Não iniciar containers nesta etapa.
- Interface: Jinja2 + HTMX, componentes em layouts/macros/parciais, Tailwind compilado e temas claro/escuro. API REST JSON independente da apresentação, preparada para mobile.
- Motor Python independente de rotas, ORM, OCR e PDF. Usar Decimal; JSON transporta decimais como strings.
- Fluxo central: leitura/validação/armazenamento → cálculo versionado → relatório. OCR fora da transação; dados relacionados persistidos atomicamente.
- Não persistir PDFs, imagens ou texto bruto. Observar a seção 5 da SPEC antes de tocar no processamento de arquivos.
- Cliente acessa apenas seus dados; admin também pode simular, com titularidade e autoria explícitas. Aplicar autorização nas rotas JSON e HTML/HTMX.
- Máximo de duas simulações não excluídas por dono, garantido no backend; cenários e recálculos são versões da mesma simulação.
- Upload é liberado após salvar dados da unidade. Seleção não inicia leitura: o usuário aciona “Ler fatura”. Simular exige ao menos uma fatura válida/conferida e nenhuma pendência do conjunto.
- Cadastro usa e-mail/senha e confirmação de e-mail; tokens revogáveis, hash de senha e MFA admin conforme SPEC. Seed admin/cliente é apenas local e idempotente.
- Não presumir que imagens da planilha, corpus não fornecido ou tarifas desconhecidas estejam homologados. Ausente não equivale a zero.

## Ambiente e configuração

- Usuário não tem administrador. Preferir ambiente virtual e recursos no diretório do usuário, respeitando políticas da máquina. Não contornar bloqueios organizacionais.
- Inspeção anterior não comprova estado atual das ferramentas. Verifique novamente somente o que a tarefa exigir.
- Criar estes documentos não autoriza instalar dependências ou iniciar a aplicação. Na tarefa de instalação, respeite o escopo autorizado pelo usuário.
- `.env` local e `.env.example` podem ser versionados com valores sintéticos de desenvolvimento; não incluir segredos reais. Banco SQLite, faturas, logs, `.venv` e caches não entram no versionamento.

## Ao concluir uma entrega

- Execute verificações proporcionais à mudança e registre resultados reais. Não trate plano ou comando proposto como teste executado.
- Marque itens na seção 15 da SPEC somente quando seus critérios estiverem atendidos. Não mantenha um segundo checklist completo nos planos.
- Atualize `docs/STATUS.md` com resumo curto, arquivos principais, verificações, pendências e próximo passo. Preserve decisões relevantes, sem transcrever a conversa ou acumular logs.
- Atualize instruções operacionais no README e documentos complementares quando os comandos existirem e forem verificados.
- Commits diretos no repositório virgilio-vpr/EcoWatt estão autorizados pelo usuário, sem confirmação adicional no site. Preferir a integração GitHub, sem exigir Git local; preservar alterações remotas e limitar o envio aos arquivos da entrega. Na resposta, listar arquivos novos/alterados/removidos e informar o commit realizado. Não enviar faturas, planilhas reais ou outros artefatos locais.
