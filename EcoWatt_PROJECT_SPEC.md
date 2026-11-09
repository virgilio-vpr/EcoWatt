# EcoWatt — Especificação de produto e implementação

Versão 3.11 • 09/11/2026 • Documento autossuficiente para orientar a implementação.

## 1. Objetivo e critérios do produto

O EcoWatt é uma plataforma de diagnóstico preliminar de contas de energia elétrica para captar clientes de consultoria. O empresário envia de 1 a 12 faturas de uma unidade consumidora, confere os dados extraídos e recebe um relatório com oportunidades de economia, gráficos, valores e premissas verificáveis.

O produto vende confiança pela transparência do cálculo. Não deve fabricar precisão, prometer economia garantida ou ocultar campos ausentes. A consultoria confirma a viabilidade, as condições contratuais, o investimento e as intervenções necessárias.

Resultados esperados:

- Importar faturas textuais e digitalizadas sem exigir digitação integral.
- Persistir dados faturáveis estruturados; não reter faturas, imagens ou texto bruto.
- Detectar duplicatas, ordenar competências e apontar lacunas.
- Identificar gastos com ociosidade, ultrapassagem e reativos excedentes.
- Comparar demandas contratadas e modalidades Azul/Verde quando houver dados suficientes.
- Exibir potencial mensal, projeção anual, memória de cálculo e limites da análise.
- Converter interesse em pedido explícito de contato com a consultoria.

Esta especificação substitui integralmente o rascunho recebido. Referências anteriores a D1–D19, RN-5, RN-6 ou exemplos de outra SPEC deixam de ser dependências. Valores de faturas não anexadas a esta revisão não constituem testes homologados.

## 2. Análise do rascunho e correções adotadas

| Problema identificado | Correção nesta versão |
| --- | --- |
| Lentidão atribuída à linguagem e ao banco sem medição | Arquitetura mais simples e orçamento de desempenho; a causa anterior permanece não comprovada |
| Ultrapassagem substitui indevidamente parte do faturamento regular | Separar demanda regular e cobrança adicional de ultrapassagem |
| Desconto de ociosidade presumido em 18% | Regra definida pelo usuário: preço da demanda ociosa = preço da demanda contratada × 0,82, na ponta, fora de ponta e demanda única; conferir contra os valores observados |
| Recálculo de impostos sobre preço já cheio | Preservar preço cheio observado; formar preço cheio de tarifa ANEEL sem impostos somente com regra tributária aplicável e documentada (§8.6) |
| Item ausente tratado automaticamente como zero | Distinguir zero confirmado, não aplicável, não encontrado e ilegível |
| Reativos calculados pela tarifa comum de energia | Valores de referência próprios e dependência de registros horários para reconstrução |
| Banco de capacitores como solução universal | Potencial de redução sujeito à engenharia, inclusive para excesso capacitivo |
| Verde → Azul com ganho chamado garantido | Cenários condicionais, limites e necessidade de demanda por posto |
| Economia de ociosidade, ultrapassagem e migração somadas repetidamente | Comparação incremental de cenários com reconciliação |
| 12 contas classificadas automaticamente como análise completa | Separar cobertura temporal, qualidade da leitura e suficiência dos dados |
| Processamento pesado no mesmo fluxo da API | Processo isolado e concorrência limitada |
| Promessa de não gravar PDFs baseada apenas no código Python | Verificar também proxy, servidor, bibliotecas, temporários e observabilidade |
| Muitos módulos comerciais antes da validação do motor | MVP centrado em extração, cálculo, relatório e pedido de contato |

## 3. Escopo e decisões de arquitetura

### 3.1 Escopo funcional

- Subgrupos A4 e AS, modalidades horárias Azul e Verde.
- Primeiro adaptador homologado: ENEL São Paulo, A4 Azul, com série real conferida. Confirmar na primeira fatura a concessionária/CNPJ; ENEL não identifica uma única distribuidora nacional.
- ENEL A4 Verde e AS entram após fixtures e tarifas próprias. Estar no escopo não significa leitor já homologado.
- Uma unidade consumidora por simulação, de 1 a 12 faturas, até 12 competências distintas em janela máxima de 18 meses.
- Faturas de mercado cativo no MVP. Mercado livre, geração distribuída, rural/sazonal, reserva de capacidade, faturamento excepcional e descontos especiais não homologados geram análise parcial ou encaminhamento à consultoria.
- Distribuidoras adicionais por adaptadores, sem alterar o núcleo do motor.

### 3.2 Decisões recomendadas para implementação

| Área | Decisão | Justificativa |
| --- | --- | --- |
| Backend | Python + FastAPI | Validação explícita, API e integração com leitura de documentos |
| Interface | Jinja2 + HTMX + HTML/CSS, dependências locais | Renderização pelo Python, templates reutilizáveis e interface elegante e responsiva |
| Integração | API REST JSON versionada e documentada por OpenAPI | Contratos compartilhados pela web e futuro app mobile |
| Persistência | SQLAlchemy 2 + Alembic | Modelos e migrações com caminho para PostgreSQL |
| Banco inicial | SQLite local, WAL e chaves estrangeiras habilitadas | Instalação simples e poucas escritas simultâneas |
| Banco de produção | PostgreSQL em container Docker, validado na preparação da migração | Modelos portáveis desde o início, sem exigir Docker agora |
| MySQL | Alternativa futura, somente após suíte própria | Não prometer portabilidade para banco não testado |
| Leitura | pdfplumber; rasterização por pypdfium2 | Extração por palavras e coordenadas; OCR seletivo |
| OCR inicial | Tesseract com português e números | Local, sem envio das contas a terceiros |
| Gráficos | SVG gerado no servidor | Leve e reutilizável no relatório |
| PDF do relatório | WeasyPrint, HTML de impressão próprio | Mesma fonte de dados do relatório online |
| Autenticação | E-mail e senha, confirmação de e-mail e token de sessão revogável | Backend controla usuários, credenciais, ativação e acesso |
| Estilização | Tailwind CSS compilado localmente e templates Jinja2 reutilizáveis | Temas claro/escuro, consistência visual e CSS otimizado |
| Administração | Conta administrativa com MFA antes da produção | Acesso privilegiado aos dados comerciais |
| Jobs iniciais | Coordenador único e processos isolados | Sem Redis/Celery inicialmente; limites explícitos |
| Desenvolvimento | Ambiente virtual, uv e Uvicorn, SQLite local; sem containers nesta etapa | Preparação para Docker e PostgreSQL antes da produção |

Python, Laravel, SQLite e PostgreSQL podem ter bom desempenho. A mudança de stack simplifica a operação, mas não substitui diagnóstico de consultas, OCR, memória, renderização e concorrência. O uso de SQLite é etapa de desenvolvimento/piloto controlado, não estratégia de escalabilidade.

### 3.3 Organização

```text
ecowatt/
  pyproject.toml
  alembic.ini
  .env.example
  README.md
  docs/
    SETUP.md
    DATABASE.md
    DEPLOYMENT.md
  deploy/                 # preparação de produção, sem execução de containers agora
    docker/              # futuros Dockerfile/Compose e instruções de operação
  src/ecowatt/
    engine/
    readers/enel_sp/
    readers/ocr/
    tariffs/
    db/
    api/
    web/
      routes/
      templates/
        layouts/
        components/
        auth/
        simulations/
        admin/
      static/
        css/
        js/
        vendor/
    reports/
    jobs/
    security/
  migrations/
  tests/unit/
  tests/golden/
  tests/integration/
  EcoWatt_PROJECT_SPEC.md
```

O motor recebe objetos tipados, usa Decimal e devolve resultados. Não importa FastAPI, ORM, OCR ou biblioteca de PDF. A API coordena serviços; regras de negócio não ficam em templates, JavaScript ou rotas. A interface web usa Jinja2 para renderizar páginas e fragmentos HTML, HTMX para atualizações parciais e CSS para apresentação, sem exigir uma SPA ou build Node no MVP. Layouts, macros e parciais preservam a reutilização dos componentes visuais. Templates de impressão são próprios para o PDF.

A API REST JSON em `/api/v1` permanece desacoplada da apresentação e disponível para o futuro app mobile. Rotas web de páginas e fragmentos ficam em camada separada e chamam os mesmos serviços de aplicação da API, sem duplicar regras nem fazer chamadas HTTP internas obrigatórias. Fragmentos HTMX não substituem o contrato JSON/OpenAPI. Web e API podem ser implantadas juntas no MVP; o desacoplamento é de contratos e regras, sem exigir serviços separados.

## 4. Jornada do cliente

### 4.1 Landing page e experiência

Landing page pública elegante com apresentação do serviço, benefícios, etapas, exemplo fictício de relatório, perguntas frequentes e ações “Criar conta” e “Entrar”, voltada à atração de potenciais clientes. Cadastro e login têm telas próprias. O acesso usa e-mail e senha. Cadastro público sempre cria cliente; administrador é provisionado internamente.

Cadastro obrigatório: nome da empresa, nome pessoal do responsável, endereço da empresa, telefone e e-mail. Solicitar e-mail e confirmação de e-mail, senha e confirmação de senha; os pares devem coincidir. A senha tem no mínimo oito caracteres, ao menos uma letra maiúscula, uma minúscula, um caractere especial e dois algarismos. A validação ocorre no frontend e no backend, com critérios visíveis e opção de mostrar/ocultar senha. Não persistir campos de confirmação nem senha em texto puro.

Confirmar o endereço de e-mail antes de liberar o primeiro login: criar conta pendente e enviar link de ativação com token de uso único e expiração. Permitir reenvio com limites e invalidar o token anterior. A ativação habilita a conta; a pessoa entra pela tela de e-mail e senha. Incluir recuperação de senha por link temporário, sem revelar se um e-mail está cadastrado. A ativação não representa consentimento para marketing.

O frontend Jinja2 + HTMX deve ser elegante e fluido: hierarquia tipográfica, cores sóbrias, espaçamento consistente, componentes reutilizáveis em templates e animações discretas que respeitem redução de movimento. Formulário em etapas curtas: empresa/unidade, faturas, conferência e resultado. Usar rótulos claros, exemplos, unidades e validação junto ao campo; preservar os dados estruturados já salvos e permitir nova tentativa individual após falha.

### 4.2 Fluxo principal

1. Acessar apresentação objetiva: o que será analisado, exemplo demonstrativo identificado como fictício e proteção dos dados.
2. Cadastrar empresa, responsável, endereço, telefone e credenciais com dupla confirmação; confirmar o e-mail e entrar com e-mail e senha.
3. Aceitar os termos do processamento e acessar o aviso de privacidade. Autorização de marketing é separada e opcional.
4. Salvar os dados básicos da unidade e então anexar de 1 a 12 PDFs, acionando “Ler fatura” para iniciar o envio e a extração de cada arquivo. Recomendar 12 competências consecutivas, sem bloquear uma conta única.
5. Acompanhar processamento por arquivo. Erros indicam o documento e a ação necessária.
6. Conferir resumo dos dados. Correção de campos críticos é obrigatória quando a extração não for validada.
7. Receber relatório online; gerar PDF sob demanda e baixá-lo em rota autenticada.
8. Solicitar contato, com canal escolhido e registro do pedido. A análise não dispara mensagem comercial automaticamente.

O cliente pode excluir a simulação e solicitar exclusão da conta. Uma nova tentativa não deve duplicar simulações ou pedidos de contato por repetição de requisição.

Antes de habilitar o campo de faturas, solicitar e salvar: distribuidora, identificador do consumidor/unidade (MTE, quando essa for a nomenclatura da fatura), nome da empresa titular e endereço do ponto de conexão. O cliente informa os dados da empresa no cadastro antes de iniciar a simulação. Oferecer “Usar o mesmo endereço da empresa”, copiando os campos com confirmação. Se a cabine/subestação ou ponto de conexão estiver em outra rua, inclusive adjacente, o cliente informa/corrige esse endereço próprio da unidade. Após salvar, liberar anexação/leitura; a API também exige essa etapa concluída.

No cabeçalho dessa mesma tela de anexação/leitura, exibir seletor de distribuidora e indicação do suporte ao layout. O piloto tem somente ENEL como família inicial de documentos, ainda sujeita à homologação do adaptador/layout; não tratar toda empresa ENEL ou todo layout como equivalente. Oferecer “Outra distribuidora / layout não suportado”, incluindo exemplos CPFL, EDP e Elektro, e ação explícita “Solicitar contato para análise das faturas”. O pedido registra distribuidora e canal autorizado, sem guardar documentos nem enviar mensagens automaticamente; a obtenção posterior de faturas exige procedimento autorizado próprio. Não exigir que a pessoa chegue ao resultado para solicitar esse atendimento. Tarifa no catálogo ANEEL não significa suporte ao parser. Bloquear leitura/simulação automática para layout não suportado também na API, com motivo e preservação dos dados já salvos. Confrontar a escolha com o documento na leitura: divergência exige resolução e nunca deve acionar silenciosamente o parser ENEL.

A extração pode sugerir nome/titular e endereço impressos na fatura para conferência: se coincidirem com os dados informados, mantê-los; se diferirem, o cliente confirma ou corrige o campo pertinente. Distinguir endereço da empresa, endereço impresso na fatura e endereço confirmado do ponto de conexão; não presumir que todo endereço impresso seja o da cabine ou que divergência de rua signifique outra unidade. Preservar o valor extraído e a justificativa estruturada da diferença. Não sobrescrever o cadastro da empresa nem o endereço confirmado automaticamente. Manter snapshots e autoria da confirmação/correção; mudança futura do perfil não modifica o histórico. Divergência de distribuidora/UC continua exigindo resolução, sem misturar unidades.

### 4.3 Perfil do cliente e limite de simulações

- O cliente vê exclusivamente seu perfil, sua empresa, suas simulações, faturas estruturadas, relatórios e pedidos de contato. No MVP, uma conta cliente corresponde a uma empresa; colaboração entre usuários será uma extensão com permissões explícitas.
- Cada cliente mantém no máximo **duas simulações não excluídas**, incluindo rascunhos, processamento, concluídas, parciais e falhas. Empresas ou unidades adicionais não ampliam essa cota.
- O painel mostra o contador “1 de 2” e os cartões existentes. Para criar uma terceira, o cliente precisa excluir uma das duas, com confirmação da exclusão.
- Revisar dados e recalcular gera versões da mesma simulação, sem consumir nova vaga. Versões não podem funcionar como simulações independentes para outras unidades.
- A API garante o limite em transação com bloqueio por cliente ou mecanismo equivalente, inclusive em requisições simultâneas. Idempotência impede duplicação por repetição.
- Excluir revoga acesso a resultados/PDFs, cancela jobs e libera a vaga na mesma operação lógica. Resultados tardios não podem recriar dados excluídos; limpeza física e backups seguem a política de retenção.
- O administrador também respeita a cota ao criar em nome do cliente.

### 4.4 Área administrativa e CRM

Somente o administrador pode acessar a área administrativa, com MFA antes de produção. O CRM essencial permite consultar todos os clientes e potenciais clientes, empresas, simulações, pendências e pedidos de contato, com busca, filtros, situação comercial, notas internas e histórico de contatos. Leads sem conta podem ser cadastrados pelo administrador com origem e finalidade registradas; isso não cria acesso autenticado automaticamente.

O administrador pode editar dados estruturados de simulações, com justificativa, autor, data e valores anterior/novo. Correções invalidam o resultado atual e exigem nova execução, preservando a anterior como histórico. O cliente vê a revisão e sua origem. Resultados numéricos congelados não são sobrescritos manualmente.

Notas internas e dados de outros clientes nunca são devolvidos nas rotas do cliente. Ocultar menus nos templates não substitui autorização por perfil e dono/empresa na API e nas rotas web, inclusive fragmentos HTMX.

O CRM deve permitir gerar orçamentos vinculados ao cliente e à revisão da simulação, com serviços, itens, valores, validade, condições e estados rascunho/emitido/enviado/aprovado/recusado. A geração integra o escopo web planejado e tem fase própria de entrega. O administrador revisa e baixa o PDF para encaminhar posteriormente por e-mail; gerar ou emitir não envia mensagem automaticamente. O estado “enviado” registra o envio manual e sua data. Eventual envio integrado será funcionalidade posterior, com ação explícita do administrador.

O administrador pode executar quantos cenários e recálculos forem necessários dentro de cada simulação, sujeitos a limites operacionais, preservando autoria e versões. Isso não consome nova vaga nem remove a cota de duas simulações por cliente. Nova unidade/conjunto independente exige vaga disponível. O CRM oferece acesso ao relatório e ação de nova simulação quando houver vaga.

O administrador também tem o fluxo completo de simulação disponível ao cliente: informar unidade, anexar/ler faturas, revisar, calcular e consultar o relatório. Pode criar para sua própria empresa de demonstração ou em nome de um cliente explicitamente selecionado no CRM. Registrar separadamente o dono da simulação e o administrador que a criou/alterou. Na própria conta também se aplica a cota de duas simulações; novas execuções dentro delas não têm essa cota. Nenhuma operação administrativa muda silenciosamente a titularidade dos dados.

### 4.5 Contas iniciais de desenvolvimento

Após aplicar as migrações, oferecer comando de seed explícito e idempotente que crie um administrador padrão de desenvolvimento e um cliente de teste, cada um vinculado à sua empresa de demonstração. Usar e-mails locais como `admin@ecowatt.test` e `cliente@ecowatt.test`, dados sintéticos e senhas obtidas da configuração local, com hash e política de complexidade normais; não embutir senha fixa no código.

O seed deve rodar somente em ambiente de desenvolvimento/teste e nunca no startup automático da API ou em produção. Pode marcar os dois e-mails como confirmados nesse ambiente, registrando que são fixtures, para permitir testes locais sem provedor de e-mail. Reexecução não duplica contas nem sobrescreve senhas/dados já alterados. Produção exige provisionamento explícito de administrador real, sem cliente de teste e sem bypass de ativação/MFA.

## 5. Upload, processamento e descarte

### 5.1 Limites iniciais

- 12 arquivos, 10 MB por PDF, 60 MB por lote e 60 páginas totais.
- Máximo de 10 páginas por arquivo; limite adicional de pixels por página, inclusive após rasterização.
- Limites configuráveis após benchmark, não ampliados silenciosamente.
- PDF com senha, estrutura inválida ou expansão excessiva é recusado individualmente.
- Validação por parser além da extensão, MIME e assinatura do arquivo.
- Uma simulação em processamento por usuário; arquivos dessa simulação são admitidos incrementalmente e processados em sequência no piloto. Um job OCR simultâneo; fila de admissão limitada. Limites de quantidade, bytes e páginas são acumulados por simulação, mesmo em requisições separadas.

### 5.2 Política de documentos

“Não armazenar faturas” significa não manter cópia persistente, backups, anexos, imagens, texto extraído integral, logs de conteúdo ou payloads em ferramentas de erro. O processamento usa memória e, quando indispensável para biblioteca externa, diretório temporário em RAM com quota, permissão restrita e limpeza em sucesso, erro e encerramento.

O framework pode transformar uploads em arquivos temporários e o proxy pode gravar corpos de requisição. A implementação deve impedir persistência em disco nesses componentes. A leitura de um PDF e seu descarte posterior não bastam para assegurar essa política. Evitar core dumps e swap não protegido no ambiente de processamento. Não prometer apagamento físico instantâneo da RAM.

Após a extração, persistir somente dados normalizados e proveniência mínima. Descartar o documento antes de o cliente sair da etapa de conferência. Na correção posterior, o cliente consulta seu arquivo original; uma prévia só pode existir durante a etapa efêmera de upload.

### 5.3 Execução

- A API admite cada arquivo somente se houver capacidade e reserva seus limites atomicamente. Caso contrário responde com indisponibilidade temporária e permite nova tentativa dos arquivos não admitidos; dados já processados permanecem salvos.
- Bytes são enviados ao processo isolado, sem conteúdo em tabela de jobs.
- O coordenador mantém a fila efêmera limitada; o banco guarda estado e metadados, não documentos.
- Extrair e confirmar dados antes de calcular. Não manter transação SQL aberta durante OCR ou geração de relatório.
- Coordenador único no piloto. Múltiplos processos web não criam filas independentes sem coordenação.
- Jobs têm timeout, heartbeat e identificador do executor. Recuperação marca somente jobs órfãos ou vencidos; iniciar uma instância web não pode invalidar o trabalho de outra.
- Reinício durante extração exige reenvio; após dados persistidos, o cálculo pode ser retomado.
- Fila durável com PDFs exigiria outra política de retenção e fica fora do MVP.

Estados: `uploaded`, `extracting`, `needs_review`, `ready`, `calculating`, `completed`, `partial`, `failed`, `expired`. Registrar erro estruturado por arquivo e módulo, sem conteúdo sensível.

### 5.4 Envio incremental, ordenação e remoção

- Cada seleção adiciona um PDF à lista local como “Anexada, aguardando leitura”. Não iniciar envio/OCR apenas pela seleção: “Ler fatura” envia o arquivo e solicita sua extração, respeitando capacidade e limites acumulados. A API retorna um identificador para consulta de estado. O cliente pode repetir esse fluxo até 12 faturas, sem precisar preparar todas antes de ler a primeira.
- Separar progresso de upload e estado da leitura. Mostrar contadores de selecionadas, enviadas, em leitura, prontas, pendentes e com erro, além do total válido para a simulação.
- Organizar da mais antiga para a mais recente por início/fim do ciclo e competência; arquivos sem data ficam em “Aguardando identificação”. Data de upload ou vencimento não substitui silenciosamente a competência.
- Exibir competência, período, estado e ação “Remover”. Antes do cálculo, remover cancela o processamento e exclui os dados daquele arquivo; ignorar resultados tardios. Atualizar contadores, lacunas, duplicidades e limites.
- Após um cálculo, alterar faturas exige revisão e novo cálculo; o relatório anterior fica identificado como histórico. A API verifica a revisão do conjunto para impedir corrida entre remoção, edição e cálculo.
- Habilitar “Simular” após a primeira fatura lida, válida e confirmada, sem envios/leituras em andamento ou campos críticos pendentes. Arquivos apenas anexados devem ser lidos ou removidos antes de calcular, sem inclusão silenciosa. Arquivos com erro devem ser reenviados ou removidos. O backend revalida essas condições. Explicar junto ao botão: “Você já pode simular com uma fatura. Para uma análise histórica mais sólida, recomendamos 12 faturas de competências consecutivas.” Isso não garante suficiência para todos os módulos.
- Ao retornar à tela, restaurar a lista e os dados já extraídos. Bytes não processados não são persistidos; interrupção ou expiração pode exigir reenvio, com indicação explícita ao cliente.
- Armazenar dados significa persistir campos estruturados; PDFs originais continuam sujeitos ao descarte definido em 5.2.

## 6. Extração e qualidade dos dados

### 6.1 Pipeline

1. Validar arquivo e calcular SHA-256 em fluxo.
2. Identificar distribuidora, layout, unidade e período.
3. Extrair palavras e posições do PDF textual, página a página.
4. Aplicar parser do layout ao quadro faturável e aos dados de medição/contratação.
5. Se campos críticos faltarem, estiverem corrompidos ou não reconciliarem, renderizar somente páginas/regiões necessárias e executar OCR.
6. Comparar texto e OCR. Divergência em campo crítico exige revisão, não escolha silenciosa do maior grau de confiança.
7. Validar contratos, unidades, quantidades, preços e totais por linha.
8. Persistir resultado estruturado, apresentar conferência e descartar documentos.

OCR lê caracteres de imagens; não compreende sozinho a regra de faturamento. O parser e as validações continuam obrigatórios. Modelo multimodal externo é extensão futura atrás de `OcrEngine`, com avaliação de custo, qualidade, privacidade e autorização específica antes de transmitir documentos.

### 6.2 Proveniência por campo

Cada campo crítico deve conter valor, unidade, estado, origem (`pdf_text`, `ocr`, `user`, `derived`), página, região opcional, versão do parser e validações. Guardar somente rótulo mínimo necessário, sem trechos extensos de texto bruto. Correção preserva valor anterior, autor e data.

Estados distintos:

- `confirmed`: extraído e validado ou conferido pelo cliente;
- `zero_confirmed`: ausência da cobrança confirmada por leitura suficiente;
- `not_applicable`: campo não pertence ao caso;
- `missing`: não encontrado;
- `unreadable`: encontrado mas ilegível;
- `estimated`: valor calculado a partir de premissa explícita.

A confiança do OCR é um indicador técnico, não probabilidade de o cálculo estar correto. Não usar um único limiar numérico para aprovar a conta inteira. Campos críticos precisam de regras de consistência ou conferência humana.

### 6.3 Duplicidade e lote

- Mesmo hash no lote: arquivo duplicado, independente do nome.
- Mesmo emissor e número de documento, quando disponível: duplicidade lógica. Ausência do número não bloqueia a extração mínima; usar hash e confronto UC/competência/ciclo/dados faturáveis para detectar possíveis duplicatas.
- Mesma unidade, competência, período e impressão digital dos dados: possível duplicata.
- Mesma competência com documentos diferentes: possível refaturamento, complemento ou dois períodos. Solicitar escolha explícita e manter apenas a versão válida; não somar automaticamente nem rejeitar refaturamento legítimo como fraude.
- Identificar UC pela combinação distribuidora + identificador normalizado, preservando zeros à esquerda.
- Ordenar por início/fim do ciclo e competência. Informar meses faltantes e ciclos sobrepostos.
- Mudança de contrato, tarifa ou modalidade é preservada por período, não sobrescrita pelo mês mais recente.
- Uma série pode conter modalidades diferentes se os dados forem suficientes; caso contrário separar trechos e emitir relatório parcial.

## 7. Contrato de dados faturáveis

### 7.1 Cabeçalho e escopo mínimo

Por definição do usuário em 06/11/2026, extrair apenas os blocos necessários ao diagnóstico: descrição do faturamento; informações do cliente e UC; classificação da unidade/tipo de fornecimento; datas gerais de leitura; grandezas contratadas. Não cadastrar exaustivamente a conta. Campos administrativos/fiscais extras são opcionais e sua ausência não impede conferência ou cálculo dos dados faturáveis suficientes. Segurança, proveniência mínima e autorização continuam aplicáveis.

Dados centrais: distribuidora identificada no cadastro/catálogo; UC; nome/titular e endereço; competência; leitura anterior/atual e dias do ciclo; demandas contratadas por posto ou única; classificação (subgrupo, modalidade, classe). Tipo de fornecimento, próxima leitura, vencimento e total a pagar podem ser capturados quando disponíveis, como informação geral. O endereço extraído permanece separado do cadastro da empresa e do ponto de conexão confirmado (§4.2). CNPJ completo do cliente não é exigido se a fatura o mascara.

CNPJ do emissor, número fiscal, chave NF3e, protocolo de autorização, situação formal de refaturamento, pagamento, boleto, códigos de barras/QR e informações de atendimento não fazem parte do mínimo a conferir. Não solicitar preenchimento ou investigação desses dados para liberar diagnóstico válido. A distribuidora precisa ser corretamente identificada para usar preços compatíveis; seu CNPJ pode vir do catálogo, sem reextração obrigatória em cada PDF. Versão técnica do parser/layout é metadado do sistema, não campo a confirmar pelo cliente.

Classificação de mercado por ciclo: priorizar identificação explícita da fatura e confirmação do cliente com proveniência. Em leitura completa do quadro financeiro, presença de cobrança de energia ativa TE sugere cativo; ausência dessa cobrança com identificação de cobrança de uso da rede/TUSD sugere livre. São indícios para sugestão, não prova automática. Procurar itens de energia e agrupamentos equivalentes do layout, não apenas a sequência de letras “TE”; UFER TE, referências históricas e ajustes isolados não bastam para classificar o fornecimento corrente. Leitura incompleta, agrupamento ambíguo, ausência de TE sem cobertura suficiente ou evidências conflitantes mantém mercado desconhecido e exige conferência. Registrar indício, cobertura, confirmação e origem sem guardar texto bruto. Mercado livre continua fora do cálculo cativo completo do MVP; não ampliar escopo pela classificação.

O total da fatura não é necessariamente o valor pago. Só usar “pago” quando houver confirmação de pagamento.

### 7.2 Medições e contratação

Por posto `peak`, `off_peak` ou `single`: demanda contratada e quantidades faturadas de demanda/energia necessárias ao diagnóstico. Demanda medida só é necessária aos módulos que dependem dela; aproveitar a quantidade de demanda utilizada do quadro de cobrança quando seu significado estiver identificado, sem chamar toda demanda faturada de medida. Grandezas reativas de medidor, fator de potência, números/códigos de medidor, contadores de leitura e séries históricas impressas são complementares; não exigir cadastro desses dados para analisar cobranças observadas. Registrar se o valor já inclui ajuste de perdas para não aplicá-lo duas vezes. Aviso de faturamento pela média ou outra estimativa exige estado `estimated` e método/proveniência; coincidência de números entre tabela de medição e itens não comprova medição real. Preservar dados impressos e separar hipóteses do usuário sobre ciclos de transição, sem reconstruir consumo ou anualizar como série medida contínua.

Na Azul e na Verde, extrair as demandas ativas medidas de ponta e fora de ponta do quadro de registro/dados de medição, quando presentes. A contratação única na Verde não elimina essas medições. Preservar separadamente demanda contratada, medida e faturada, unidade, posto, ciclo, ajuste de perdas e proveniência. Os exemplos visuais enviados em 09/11/2026 justificam essa fonte de extração, sem homologar todos os layouts. Não exigir cadastro integral dos contadores ou demais grandezas do quadro: somente os campos necessários ao módulo. Medição fora de ponta capacitiva/indutiva e outros rótulos exigem mapeamento validado; não somar máximos, escolher coluna ou equiparar grandezas pelo nome. Se a fatura só trouxer demanda única ou medições ambíguas, preservar a insuficiência em vez de fabricar os postos.

### 7.3 Itens de cobrança

Tipos: `active_energy_te`, `active_energy_tusd`, `regular_demand`, `idle_demand`, `overrun_demand`, `reactive_energy_excess`, `reactive_demand_excess`, `flag`, `tax`, `other`, `unclassified`.

Por item: descrição/tipo; posto quando identificável; quantidade e unidade disponíveis; preço unitário cheio com impostos incorporados; valor cobrado; estado e proveniência mínima. Incluir energia TE/TUSD, demanda, parcela ociosa LEI ESTADUAL, UFER e demais linhas monetárias do quadro, com subtotais/total do faturamento. Tarifa unitária sem impostos pode ser guardada se disponível, sem substituir o preço cheio. Colunas tributárias não são obrigatórias para usar preço cheio observado. Alíquotas, bases e incidências tornam-se necessárias somente à formação de preço ausente via catálogo (§8.6); sua extração não transforma o diagnóstico em auditoria fiscal.

TE e TUSD agrupadas em uma linha exigem identificação explícita de agrupamento. Não duplicar energia ao somar linhas TE/TUSD da mesma medição. Valores monetários de ociosidade podem existir sem quantidade ou preço; não inventar o campo ausente.

### 7.4 Validações

- Separadores brasileiros, sinais de crédito, decimais e conversões kWh/MWh normalizados.
- Tarifa e quantidade compatíveis com unidade e posto.
- `quantidade × preço ≈ valor`, considerando precisão impressa e arredondamento.
- Tolerância monetária de reconciliação: diferença absoluta de até R$ 0,99 por item, inclusive, autorizada pelo usuário em 06/11/2026. Preservar produto, valor observado e diferença; valores acima do limite geram pendência. Não aplicar esse limite aos kW, ao gatilho de ultrapassagem, a campos ausentes ou à identidade. O residual do total continua explícito e exige classificação; não o apagar por essa tolerância.
- Para o diagnóstico, a base financeira é o quadro de faturamento: comparar soma das linhas reconhecidas, subtotais e TOTAL desse quadro, com residual explícito. Inconsistência nos itens/base efetivamente usados exige revisão ou limita somente o módulo dependente. Total a pagar do cabeçalho pode ser mostrado separadamente; diferença para quadro ou boleto é observação informativa, não bloqueio automático dos módulos cujos dados faturáveis estão consistentes. Não criar parcela por diferença, misturar bases ou declarar auditado o valor a pagar. Boleto e documentos fiscais não precisam ser conferidos.
- Demanda contratada ou medida ausente bloqueia a otimização daquele posto; não bloqueia diagnóstico válido de reativos.
- Sem demanda por posto suficiente, migração pode ficar parcial/inconclusiva.
- Quantidades reativas não são reconstruídas com fator de potência médio mensal quando a regra exige intervalos.

## 8. Motor econômico e regulatório

### 8.1 Princípios

Todos os cálculos usam Decimal; entrada/saída JSON representa decimais como strings. Precisão interna mínima de 28 dígitos. Não truncar tarifas a cinco casas antes do cálculo: preservar precisão de origem. Arredondar moeda a centavos por item no fechamento, com política versionada e validada contra a distribuidora.

Parâmetros possuem vigência, escopo, fonte e versão. A simulação usa preços efetivos com impostos incorporados; não reaplica tributos sobre preço já cheio. A formação de preço a partir da tarifa ANEEL sem impostos segue o §8.6, com parâmetros próprios e memória versionada. Não transformar qualquer regra regulatória em campo livre sem validação administrativa.

Exceções rurais/sazonais, períodos de teste, ajustes e contratos especiais ficam fora da fórmula geral até homologação. Uma divergência não transforma automaticamente a fatura em cobrança indevida.

### 8.2 Demanda regular e ultrapassagem

No caso geral não sazonal homologado, por posto e ciclo:

```text
Dm = demanda ativa medida
Dc = demanda contratada
T  = tarifa de demanda aplicável
D_faturavel = max(Dm, Dc)
C_regular_sem_tributos = D_faturavel × T

se Dm > 1,05 × Dc:
    C_ultrapassagem_sem_tributos = (Dm − Dc) × 2 × T
senão:
    C_ultrapassagem_sem_tributos = 0

C_demanda_base = C_regular_sem_tributos + C_ultrapassagem_sem_tributos
```

A ultrapassagem é adicional ao faturamento regular. O gatilho de 5% não significa cobrar somente a parcela acima de 105%. A tarifa específica identificada e homologada prevalece sobre uma tarifa deduzida.

Exemplo sem tributos, Dc = 100 kW:

| Dm | Regular | Adicional | Total |
| --- | --- | --- | --- |
| 80 kW | 100 × T | 0 | 100 × T |
| 105 kW | 105 × T | 0 | 105 × T |
| 120 kW | 120 × T | 40 × T | 160 × T |

O resultado 140 × T apresentado no rascunho para 120 kW não deve ser utilizado como teste de referência.

Demanda ociosa física = `max(Dc − Dm, 0)`. Na simulação, valorar a demanda utilizada e a ociosa com seus preços efetivos próprios, já com impostos incorporados. Por esclarecimento do usuário em 06/11/2026, a parcela ociosa identificada como LEI ESTADUAL usa `P_ociosa = P_demanda_contratada × (1 − 0,18) = P_demanda_contratada × 0,82`. Aplicar a relação ao preço unitário, não aos kW contratados, na ponta, fora de ponta e demanda única. Não descontar novamente impostos da tarifa cheia nas demais parcelas. A regra informada orienta a simulação; o gabarito histórico preserva o preço e o valor impressos. Divergência entre a relação e a leitura candidata exige conferência, sem substituir o observado ou considerar o corpus aprovado.

O exemplo sem tributos acima fixa apenas a regra elétrica e o gatilho de ultrapassagem. Para preços cheios distintos, o custo regular é `min(Dm, Dc) × P_utilizada + max(Dc − Dm, 0) × P_ociosa + max(Dm − Dc, 0) × P_utilizada`, sem novo acréscimo ou retirada de impostos. O adicional de ultrapassagem usa seu preço efetivo específico quando disponível; o fator 2 exige base compatível e regra validada. Preservar valores observados quando faltarem preços para reproduzir ou simular parcelas.

Conferir o cenário atual com as linhas faturadas. Se não reconciliar, preservar o valor observado, registrar diferença e bloquear recomendações quantitativas que dependam da regra não validada. Uma base atual correta não torna automaticamente correto o cenário alternativo.

### 8.3 Otimização da demanda

Aproximar o pico de 105% da contratada é um candidato econômico, não uma obrigação ou garantia operacional. A tolerância não assegura disponibilidade adicional de potência. A decisão deve considerar variação de carga, expansão e condições contratuais.

Comparar dois cenários:

1. **Sem ultrapassagem nos dados observados:** nenhum ciclo excede o limite de tolerância.
2. **Menor custo histórico com risco controlado:** aceita ultrapassagem em até dois ciclos distintos, apenas se reduzir o custo total frente ao primeiro cenário.

Na Azul, otimizar ponta e fora de ponta respeitando restrições contratuais entre postos quando aplicáveis. O limite de dois ciclos considera a união dos meses afetados pelos dois postos; informar também quantas ocorrências por posto. Não otimizar cada posto de modo independente e depois exceder o limite global.

Gerar candidatos pela grade contratável validada e pelos pontos de mudança `Dm` e `Dm/1,05`, incluindo vizinhos da grade, contrato atual e limites regulatórios/contratuais. Usar arredondamento de teto quando necessário para não criar ultrapassagem por precisão numérica. Não fixar faixa arbitrária que possa excluir o ótimo.

O sistema só chama o resultado de mínimo dentro do conjunto e das restrições efetivamente exploradas. Empate: preferir menor exposição à ultrapassagem; depois maior margem de capacidade, sem sugerir contratação acima do limite técnico.

Mostrar contrato atual e sugerido, custo regular, adicional, ociosidade física, ciclos de risco e economia líquida das cobranças. Ociosidade e ultrapassagem são explicações do mesmo custo de demanda; não somar novamente como oportunidades independentes.

Com 1–2 contas: diagnóstico observado e candidatos ilustrativos, sem recomendação contratual anual. Com 3–11: simulação preliminar condicionada à representatividade. Com 12: referência histórica de até um ano, ainda sujeita à previsão de carga.

### 8.4 Reativos excedentes

O MVP usa cobranças de energia e demanda reativas excedentes efetivamente identificadas e validadas. Ausência de cobrança confirmada não gera cenário independente de aparecimento de reativos nem exige buscar tarifa apenas para simular essa existência. Ausência em leitura incompleta permanece desconhecida. Essa delimitação não autoriza presumir que alterações de demanda ou modalidade preservem a ausência futura; efeitos não calculáveis são declarados como limitação do cenário. Não confundir kVArh total medido, indicadores do medidor e valores cobrados. Rótulos UFER, UFDR, DMCR e equivalentes dependem do layout e da unidade; o nome isolado não prova cobrança ou ausência dela.

A REN 1000 estabelece referência de fator de potência de 0,92. A reconstrução regulatória completa depende de registros por intervalo e de valores de referência próprios: energia pela referência TE B1 em bandeira verde e demanda pela referência de demanda fora de ponta da Azul aplicável. Não usar automaticamente a TE/TUSD comum do consumidor nem a tarifa do posto da cobrança. Importar essas referências auxiliares mesmo que B1 esteja fora do público-alvo comercial.

O período capacitivo é a janela de seis horas definida pela distribuidora dentro do intervalo regulatório; não presumir todo fim de semana como capacitivo. Parametrizar calendário e janela da distribuidora quando houver dados intervalares.

Sem dados horários suficientes, mostrar a cobrança observada e o potencial condicionado de evitá-la; não declarar auditoria integral da regra de reativos. Ausência de linha em leitura incompleta significa desconhecido, não zero.

Apresentação comercial:

- Potencial técnico máximo observado: até 100% das cobranças excedentes elegíveis, se a solução corrigir integralmente a causa.
- Cenário de recuperação: percentual escolhido e identificado como hipótese; nunca percentual padrão escondido ou promessa.
- Capacitores automáticos podem corrigir excesso indutivo, mas exigem estudo de carga e harmônicos. Excesso capacitivo pode exigir retirada/seccionamento de capacitores, controle diferente ou outra solução.
- Não dimensionar banco, estimar investimento ou calcular retorno sem estudo próprio.

Reduzir a demanda contratada pode alterar a cobrança de demanda reativa excedente. Sem registros para recalculá-la, a soma de ajustes de demanda com recuperação parcial dos reativos é cenário condicionado. No cenário de correção completa, declarar explicitamente a hipótese de eliminação do excedente também no contrato proposto.

### 8.5 Comparação Azul ↔ Verde

Calcular energia ativa por posto, demanda regular, ultrapassagem e parcelas relevantes de reativos, com tributos e premissas compatíveis. Buscar TE e TUSD para cada modalidade e vigência; não assumir TE igual sem conferir a tabela aplicável. Componentes comprovadamente iguais podem cancelar na comparação.

**Azul → Verde:** quando as demandas medidas por posto usam a mesma base/período, a demanda única medida é o máximo entre ponta e fora de ponta. Otimizar contratação única. Reavaliar tarifas de energia ponta e fora de ponta; não transportar TUSD ponta da Azul para Verde.

**Verde → Azul:** procurar primeiro as demandas ativas medidas por posto no quadro de medição da própria fatura (§7.2), independentemente da contratação única. Com ponta e fora de ponta validadas para os ciclos analisados, calcular os dois contratos da Azul sem estimar a repartição da demanda única. O preço da demanda única Verde não substitui os preços de ponta/fora de ponta Azul: resolver os componentes faltantes no catálogo ANEEL e formar preços cheios conforme §8.6. Dados complementares podem suprir medições ausentes, com proveniência. Se existir somente o máximo único:

- Não inventar o horário do pico.
- Exibir cenário superior conservador de custo de demanda, atribuindo o máximo a ambos os postos, se as demais condições forem compatíveis.
- O resultado é limitado às hipóteses; não rotular como economia garantida.
- Exibir sensibilidade opcional com `Dm_ponta = alfa × Dm_unica` e `Dm_fora = Dm_unica`, alfa entre 0 e 1. O limiar é uma hipótese comum à série, não medição mensal nem único valor universal em kW.
- Se não houver mudança de sinal ou dados suficientes, mostrar “inconclusivo” ou “não houve vantagem nos cenários calculados”.

Quando faltarem medições por posto suficientes na fatura, buscar registros do portal da distribuidora para os meses analisados. Dados intervalares não são pré-requisito adicional se as medições mensais por posto já forem suficientes ao módulo; continuam necessários às regras que dependem de intervalos. Uma semana de medição pode apoiar diagnóstico, mas não comprova sazonalidade anual.

Mostrar economia técnica recorrente separada do prazo de implementação. Redução de demanda e mudança de modalidade dependem de elegibilidade, contrato, prazos e histórico de alterações. Não supor benefício imediato no mês seguinte. O relatório só informa datas de efeito quando as condições foram verificadas; sem elas registra “data de implantação não confirmada”.

### 8.6 Preços efetivos com impostos incorporados

Por atualização de escopo solicitada em 09/11/2026, distinguir duas visões independentes:

- **Histórico:** conferir valores e regras nas vigências das faturas.
- **Comparativo de referência:** reproduzir o mesmo perfil de carga com preços de referência selecionados pela regra abaixo, completos e equivalentes para os cenários atual e alternativo. Aplicar também ao ajuste de demanda sem mudança de modalidade; não apresentar a diferença contra gastos históricos como economia comparável.

**Fonte e formação do preço cheio.** Usar o preço unitário cheio aplicável extraído e validado da fatura para os componentes disponíveis; não acrescentar novamente impostos. Quando faltar tarifa de outra modalidade ou de qualquer componente necessário à simulação, buscar a Tarifa de Aplicação no catálogo local aprovado, importado do arquivo oficial ANEEL (§9), para distribuidora, subgrupo, modalidade, posto, componente, mercado e vigência corretos. A tabela não supre quantidades, medições nem cobranças que não existiram. Não usar preço de componente, concessionária ou modalidade diferente como substituto.

Se a fonte estiver sem impostos, formar o preço cheio com percentuais, bases e incidências aplicáveis a cada componente/modalidade e período, inclusive isenções/reduções quando comprovadas. Obter parâmetros da fatura quando identificados e transferíveis ao cenário, ou de fonte tributária/distribuidora documentada e aprovada. A importação ANEEL não fornece, por si, todas essas informações. Não fixar percentuais universais, copiar a carga tributária global da conta ou multiplicar por uma soma presumida de alíquotas. A fórmula de inclusão de tributos depende das bases/incidências e deve ser validada antes da implementação comercial. Registrar tarifa-base, unidade, alíquotas e origem, incidências, regra/versão, arredondamento e preço cheio resultante. Falta de parâmetro necessário bloqueia somente o componente/cenário dependente; nunca equivale a zero ou isenção. A ausência/divergência de colunas tributárias não bloqueia preço cheio observado já disponível. Não auditar ou reescrever o histórico fiscal.

**Maior tarifa da série e migração ACL.** Para os novos cenários de demanda/modalidade e demais componentes simuláveis, selecionar a maior tarifa unitária cheia elegível da série, por componente/posto e base compatível; não somar tarifas, escolher pelo maior total da fatura nem confundir preço com maior demanda em kW. Não assumir que a última fatura seja a maior. Em empate, usar a referência mais recente e registrar a escolha. Não comparar máximos entre Azul e Verde ou entre componentes diferentes para eleger a modalidade mais barata.

- Série inteiramente cativa: usar o maior preço elegível de todo o período.
- Migração cativo → ACL dentro da série: identificar o marco por mercado confirmado de cada ciclo (§7.1) e escolher o maior preço no trecho anterior à migração. Descontos ou mudanças posteriores do ACL não substituem essa referência. Ciclo misto sem segmentação confiável ou marco incerto exige conferência; não escolher uma data presumida.
- Série inteiramente no ACL: usar o maior preço elegível do período para os componentes suportados. Isso não inclui energia comprada do fornecedor que não conste da fatura de distribuição nem autoriza calcular conta cativa completa com dados incompletos. Informar o escopo parcial e componentes excluídos.

Para cada componente, congelar conjunto elegível, exclusões, ciclo de origem, preço máximo e data/versão de referência. Na modalidade alternativa ou componente ausente, resolver a tarifa ANEEL e os tributos na mesma referência aplicável; não selecionar uma vigência mais barata para a alternativa. Reprecificar C0 e os cenários comparados na base equivalente, preservando medições/ciclos; a referência pode variar por componente e deve ficar visível. Não substituir os valores históricos observados. Mercado desconhecido, transições múltiplas ou falta de fonte equivalente tornam o trecho dependente parcial/inconclusivo até revisão, sem misturar preços incompatíveis.

Para a parcela ociosa LEI ESTADUAL, preservar a relação de 82% do preço cheio da demanda contratada definida no §8.2, por posto ou demanda única, sem reaplicar uma segunda redução tributária. A nova formação de preço ANEEL não revoga essa regra nem altera o gabarito histórico aceito.

Exemplos matemáticos sintéticos sem tributos continuam identificados como tais e não substituem o preço exigido na simulação real. Esta atualização amplia a formação de preços alternativos e a referência comparativa; não homologa tarifas, fórmulas tributárias, novos layouts ou cálculo integral ACL.

### 8.7 Economia sem dupla contagem

Usar cenários encadeados com a mesma base de preços e lista explícita de componentes:

```text
C0 = contrato e modalidade atuais, sem intervenções
C1 = demanda otimizada na modalidade atual
C2 = modalidade/contrato escolhidos após comparação
C3 = cenário escolhido com correção dos reativos

S_demanda = C0 − C1
S_modalidade = C1 − C2
S_reativos = C2 − C3
S_total = C0 − C3 = S_demanda + S_modalidade + S_reativos
```

Cada cenário inclui os efeitos cruzados suportados pelos dados. Não estimar DRE alterada com fórmula insuficiente só para preencher a sequência. Se C1/C2 estiverem indefinidos por interação com reativos, apresentar subtotal calculável e cenário combinado condicionado, sem decomposição artificial.

Sempre incluir a situação atual entre as opções. Custos adicionais de cenário selecionado não podem ser ocultados por zerar uma parcela negativa. Se não houver vantagem, mostrar economia zero e conclusão correspondente; manter comparações brutas na memória.

Projeção anual = média dos ciclos representativos × 12, com indicação de anualização, não promessa de economia no primeiro ano. Identificar ciclos curtos, longos, sobrepostos, meses ausentes e sazonalidade; bloquear projeção que não tenha base comparável. Doze documentos não equivalem necessariamente a doze meses completos.

Percentual principal = economia do cenário ÷ custo-base dos mesmos componentes e preços. Um percentual sobre o total histórico da fatura é secundário e deve informar a diferença de base. Consumo não é reduzido nesta análise; seu custo pode mudar na troca de modalidade.

### 8.8 Cenário manual e análise de sensibilidade

Além dos candidatos automáticos da seção 8.3, permitir ao cliente e ao administrador testar uma demanda contratada manual em kW, sem alterar as medições extraídas. Na Azul, os controles de ponta e fora de ponta são separados, mas a validação de restrições e ciclos afetados permanece conjunta. Na Verde, usar contratação única.

O painel distingue “Contrato atual”, “Cenário manual” e “Sugestão automática”. Usar campo numérico acessível, com unidade, limites e passo da grade contratável; controle deslizante é opcional e nunca a única entrada. Oferecer “Recalcular cenário”, “Restaurar contrato atual” e “Usar sugestão”. Cada alteração indica resultado desatualizado até concluir o recálculo. Respostas antigas de requisições concorrentes não podem substituir a última escolha.

O cenário manual apresenta custo atual e alternativo no mesmo período/base, diferença em R$ e %, ociosidade física e quantidade/lista de ciclos com ultrapassagem por posto e na união dos postos. Mostrar custo adicional quando a diferença for desfavorável, sem mascará-lo como economia. Informar exposição histórica e margem em relação ao pico; isso não representa probabilidade de risco futuro.

Um candidato manual fora das restrições contratuais é recusado com explicação. Candidato que exceda o limite de ciclos da estratégia automática pode ser apresentado como exploratório, com alerta explícito e sem selo de recomendação. Regras e tarifas não ficam editáveis nesses controles.

O backend realiza todos os cálculos, inclusive prévias. A API recebe demandas candidatas, revisão dos dados e base de preços; devolve indicadores e séries mensais do mesmo motor. Prévia não altera resultado publicado. Ao salvar, registrar parâmetros, origem manual/automática, autor e versões em uma execução da mesma simulação, sem consumir nova vaga. A quantidade de execuções e a frequência de prévias têm limites operacionais próprios.

Como evolução visual, exibir curva “Demanda contratada (kW) × custo no período (R$)”, marcando contrato atual, candidato manual e melhor candidato calculado. Cada ponto respeita a mesma base e restrições; na Azul, declarar qual demanda fica fixa ao variar a outra. Não rotular mínimo fora do conjunto explorado.

## 9. Tarifas e parâmetros

Importação administrativa de CSV oficial ANEEL, com leitura em fluxo, prévia e aprovação antes de ativar. Suportar mapeamento de colunas e detectar mudanças de esquema, separador, codificação e unidade.

Identificação mínima: distribuidora/CNPJ, resolução, início/fim da vigência, base tarifária, subgrupo, modalidade, classe/subclasse quando aplicável, posto, componente, detalhe/desconto, unidade, valor e origem tributária. Não confundir Tarifa de Aplicação com Base Econômica.

- Converter R$/MWh em R$/kWh dividindo por 1.000; demanda segue unidade de origem verificada.
- Guardar hash do arquivo tarifário, URL, data de importação e resumo de linhas aceitas/rejeitadas.
- Detectar repetição e sobreposição; não encerrar vigências silenciosamente nem alterar registros usados em relatórios.
- Importar referências auxiliares de reativos, inclusive B1, além de A4/AS Azul/Verde.
- Tarifa manual só com fonte, justificativa e auditoria.
- Não carregar todo o histórico ANEEL em memória nem no banco do piloto: selecionar distribuidora e vigências necessárias durante a importação.
- Não consultar ANEEL em cada simulação; resolver a partir do catálogo local aprovado.
- Importar tarifas das duas modalidades e dos componentes ausentes necessários ao cenário; associar regras tributárias aprovadas para formar preços cheios (§8.6). Manter tarifa sem impostos e preço formado separados, com referência temporal, origem e versão; catálogo de tarifas e suporte ao layout são capacidades independentes (§4.2).

Parâmetros: tolerância e multiplicador de ultrapassagem; fator de potência; regras de perdas e exceções; janela de reativos; limites contratuais; precisão; restrições de otimização e validade. Parâmetro comercial e regra regulatória têm identificação distinta.

## 10. Persistência, decimal e migrações

### 10.1 Modelo mínimo

| Tabela | Função |
| --- | --- |
| users | Identidade, e-mail e perfil |
| companies | Empresa vinculada à conta cliente |
| leads / crm_notes / crm_activities | Potenciais clientes, vínculo opcional à conta, situação e histórico interno |
| auth_challenges / sessions | Acesso, expiração, revogação e tentativas |
| email_verifications / password_resets | Tokens protegidos de ativação e recuperação, expiração e consumo único |
| quotes / quote_items / quote_revisions | Orçamentos, itens e versões vinculados ao cliente e à execução de origem |
| privacy_events | Aceites, finalidades e solicitações |
| simulations | Dono, estado, unidade, cobertura e versões |
| invoices | Cabeçalho, hash, ciclo e dados por posto |
| invoice_items | Cobranças e medições normalizadas |
| field_provenance | Origem, validações e histórico de correções |
| distributors | Identificação e adaptadores habilitados |
| tariff_imports / tariff_rates | Fonte e tarifas imutáveis por vigência |
| rule_sets | Versões regulatórias, tributárias e parâmetros |
| calculation_runs | Entrada congelada, resultados e versões |
| report_revisions | Textos e apresentação de cada execução |
| contact_requests | Pedido de contato e situação comercial |
| audit_events | Operações privilegiadas sem documentos |

O escopo web inclui CRM para consulta, acompanhamento, recálculos e geração de orçamentos, estes entregues em fase específica. Estoque fica fora do escopo. Usuários guardam hash de senha, estado pendente/ativo/bloqueado, confirmação de e-mail e vínculo à empresa; desativação revoga sessões. Campos tipados ficam em colunas pesquisáveis; snapshots JSON servem à reprodução e não substituem todo o modelo relacional.

### 10.2 Valores e integridade

- Decimal em SQLite: texto canônico por TypeDecorator; PostgreSQL: Numeric com precisão e escala explícitas por campo.
- Conversão nunca passa por float. Agregações e ordenação de valores decimais armazenados como texto são feitas no motor; ordenação lexical não é numérica.
- Datas de competência separadas de instantes UTC; identificadores públicos imprevisíveis não substituem autorização.
- Chaves estrangeiras, índices de dono/data/status e restrições únicas nos identificadores aplicáveis.
- JSON com decimais como strings. Enums portáteis com validação e constraints nomeadas.
- Idempotência em upload, cálculo e contato; correções invalidam a execução anterior e geram nova versão.
- Snapshots contêm dados estruturados mínimos, sem documentos ou texto bruto, e seguem a mesma exclusão do restante da simulação.

### 10.3 Migração para PostgreSQL

Desde a primeira fase: Alembic com migrações versionadas e batch mode onde necessário no SQLite. Desenvolver e testar criação limpa e atualização localmente em SQLite, sem exigir PostgreSQL ou Docker nesta etapa. Manter tipos, constraints e migrações compatíveis com o destino e documentar diferenças. Na preparação de produção, executar a suíte e migrações também no PostgreSQL em container antes de aprovar o uso real. Compatibilidade planejada não significa validação já concluída. Rollback é testado quando seguro; downgrade destrutivo não substitui backup.

Trocar DATABASE_URL muda a conexão, mas não transporta dados. Se houver dados de piloto a preservar, usar exportação/importação tipada com validação de contagem, referências, decimais e relatórios; janela sem escrita; backup e plano de retorno. Se o piloto usar só dados descartáveis, iniciar produção com catálogo e conta administrativa, conforme decisão registrada.

SQLite em disco local, sem compartilhamento de arquivo por rede. Transações curtas, timeout e escritas limitadas. Backup consistente pela API de backup ou procedimento compatível com WAL. Produção usa PostgreSQL antes de receber clientes reais em escala.

### 10.4 Ordem de criação, relacionamentos e gravação

O backend e o esquema precedem a interface completa. Definir PKs, FKs, nulabilidade, unicidade e política de exclusão antes dos endpoints. Usar migrações Alembic encadeadas por `revision/down_revision`; importar os modelos no metadata e revisar o autogenerate. Não depender de `create_all()` no startup como substituto de migrações. Ativar chaves estrangeiras em toda conexão SQLite.

Ordem de dependências proposta para tabelas e inserções:

| Ordem | Grupo | Dependências e vínculos |
| --- | --- | --- |
| 1 | `companies`, `distributors`, `rule_sets` | Cadastros raiz sem referências circulares |
| 2 | `users`, `tariff_imports` | Usuário referencia empresa; importação referencia distribuidora e usuário importador quando aplicável |
| 3 | `sessions`, desafios MFA, `email_verifications`, `password_resets`, `privacy_events`, `leads`, `tariff_rates` | Identidade referencia usuário; lead pode referenciar usuário/empresa; tarifa referencia importação/distribuidora |
| 4 | `simulations`, `crm_notes`, `crm_activities` | Simulação referencia dono, empresa, distribuidora e autor; notas/atividades referenciam lead e autor |
| 5 | `invoices` e metadados de processamento | Fatura referencia simulação; metadados não contêm bytes do documento |
| 6 | `invoice_items`, medições por posto e `field_provenance` | Itens/medições referenciam fatura; proveniência referencia campo e, quando necessário, item; criar itens antes da proveniência |
| 7 | `calculation_runs` | Referencia simulação, autor e conjunto de regras; snapshot estruturado congela revisão e tarifas utilizadas |
| 8 | `report_revisions`, `contact_requests`, `quotes` | Relatório/orçamento referenciam execução; contato referencia cliente/simulação e execução opcional |
| 9 | `quote_revisions`, `quote_items` | Revisão referencia orçamento; itens referenciam a revisão, preservando o conteúdo emitido |
| 10 | `audit_events` | Ator referencia usuário quando existente; recurso é identificado sem FK circular para todas as tabelas |

As tabelas comerciais podem ser criadas na fase do CRM/orçamentos, mantendo essa ordem relativa. Os nomes finais de tabelas auxiliares e FKs devem ser consolidados no diagrama e nas migrações antes da implementação. `users.company_id` aponta para `companies`; evitar FK reversa obrigatória de empresa para usuário que gere ciclo na criação inicial. A titularidade da simulação é explícita, não inferida apenas pelo autor.

Salvar a extração de cada fatura em transação: cabeçalho, medições, itens e proveniência; confirmar a operação inteira ou desfazê-la em caso de falha. Marcar o arquivo como pronto somente após commit. Persistir falha de processamento separadamente, sem deixar itens órfãos ou fatura aparentemente válida. Extração/OCR ocorre fora da transação. Idempotência e unicidade impedem gravação duplicada em retry.

Exclusões respeitam FKs e política de retenção: remover filhos antes de pais ou usar cascatas deliberadas para dados dependentes. Não usar cascata de usuário para tarifas ou regras compartilhadas; autoria pode exigir anonimização/`SET NULL` conforme a política. Exclusão de simulação inclui snapshots, relatórios e vínculos comerciais derivados segundo política explícita; ela não pode falhar por uma FK de orçamento esquecida. Validar criação limpa, upgrades, seed repetido, rollback de gravação e ausência de órfãos.

### 10.5 Configuração local e futura implantação

Nesta etapa, usar `.env` de desenvolvimento e `.env.example` versionados, conforme decisão do projeto, somente com valores locais/sintéticos e credenciais exclusivas de demonstração. Não incluir `.env` em regras de ignore agora. Credenciais reais de serviços externos e tokens pessoais não pertencem a esses arquivos versionados. A regra de produção abaixo trata separadamente os segredos reais.

Configuração centralizada tipada, sem caminhos absolutos do computador, com variáveis para ambiente, `DATABASE_URL`, diretório de dados, chaves locais, provedor de e-mail e seed. Não criar bancos, contas ou importar tarifas ao importar módulos. Arquivo SQLite, temporários, logs, ambiente virtual e uploads não são versionados. Manter API, worker e motor independentes de caminhos e detalhes do banco.

Antes da produção: preparar Dockerfile da aplicação, Compose com PostgreSQL, volume persistente, healthchecks e procedimento de migração executado uma vez antes da subida da aplicação. Segredos de produção vêm do ambiente/gestor da hospedagem; excluir arquivos de segredos do Git e do contexto de build nessa fase, sem presumir que adicionar ao ignore apaga histórico. Não reutilizar credenciais de demonstração. A estrutura `deploy/docker/` é reservada agora; containers não são necessários para o desenvolvimento atual.

## 11. Relatório, gráficos e conversão

Relatório online e PDF gerados do mesmo calculation_run imutável. O template de impressão pode diferir para garantir paginação, legibilidade e gráficos vetoriais.

Conteúdo obrigatório:

1. Identificação mínima da unidade, período e qualidade dos dados.
2. Economia mensal e anual potencial, com indicação clara de cenário condicionado.
3. Barras por competência: demanda medida, contratada e candidata, separando postos da Azul e linha de tolerância.
4. Cobranças de reativos por mês; distinguir observado e potencial evitável.
5. Custos comparáveis Azul/Verde; suprimir gráfico conclusivo quando faltar dado.
6. Composição da economia sem dupla contagem.
7. Tabela dos dados extraídos e corrigidos, com origem e campos faltantes.
8. Memória por ciclo: tarifa, quantidade, regra, custo atual/alternativo, diferença e reconciliação.
9. Fonte e vigência das tarifas, versões, hipóteses e condições contratuais.
10. Próximos passos e botão “Quero validar essa economia com uma consultoria”.

Não usar “selo ANEEL”, “aprovado”, “economia garantida” ou percentuais de confiança sem significado validado. Separar:

| Eixo | Informação exibida |
| --- | --- |
| Cobertura | Quantas competências, lacunas e duração |
| Leitura | Validada automaticamente, conferida ou pendente |
| Cálculo | Completo para o módulo, parcial ou indisponível |
| Viabilidade | Diagnóstico observado ou cenário condicionado |

Impostos, perdas e encargos não podem aparecer simultaneamente como incluídos no cálculo e excluídos do relatório. Listar precisamente os itens considerados e os mantidos constantes. Economia é bruta de honorários e investimento, salvo simulação específica futura.

Admin pode acrescentar comentário técnico; não editar resultado numérico congelado. Nova regra ou correção gera nova execução. PDF é gerado sob demanda, com cache privado opcional sujeito à retenção; nunca URL pública por nome previsível.

### 11.1 Comparação visual de demanda atual e simulada

Referência de experiência: imagens da planilha fornecidas pelo usuário nesta revisão, com período de out/2025 a set/2026. As duas imagens de demanda são iguais e não representam dois casos independentes. As imagens orientam a apresentação; não demonstram as fórmulas, tributos ou unidades dos dados originais.

- Exibir painéis atual/simulado lado a lado no desktop e empilhados no celular, com o mesmo eixo em kW, escala, período e ordem cronológica. Não alterar a escala para ampliar visualmente a diferença.
- Plotar demanda medida e ociosidade física, identificada como `max(contratada − medida, 0)`. A legenda “Excedente” da planilha é ambígua para a área ociosa e deve ser substituída por “Ociosidade contratada”.
- Traçar contratação e limite de tolerância como linhas distintas, identificadas com valores e unidades. O percentual vem da versão de regra aplicada; linhas e cálculos usam precisão integral, mesmo se o rótulo for arredondado.
- Destacar ciclos em que a medição excede a tolerância, com marcador e texto. Se houver segmento acima do contrato, ele deve integrar a própria demanda medida; não empilhar uma cobrança de ultrapassagem em R$ sobre uma barra em kW nem duplicar demanda medida.
- Tooltip e tabela acessível mostram mês/ano, medida, contratada, limite, ociosidade, ocorrência de ultrapassagem e custos regular/adicional. Incluir ano para evitar confusão em séries que cruzam anos.
- Para a Azul, oferecer abas de ponta/fora de ponta e resumo conjunto; para a Verde, mostrar demanda única. Gráficos na web e no PDF usam as mesmas séries calculadas e legendas consistentes.
- Cartões mostram período efetivo, cobertura, demanda atual/candidata, custo atual, custo simulado e diferença. “Custo de demanda na ponta” deve ser distinguido do custo total da conta. Não chamar soma de período incompleto de “custo em 12 meses”; projeção anual aparece separada e identificada.
- Cores devem ser consistentes entre cenários e acompanhadas de traços, marcadores e texto, sem depender exclusivamente de verde/vermelho. No celular, preservar leitura e acesso à tabela dos valores.

### 11.2 Quadro detalhado de reativos

Criar resumo com total observado de cobranças reativas no período, separação entre energia e demanda, postos/naturezas disponíveis, meses com ocorrência e potencial condicionado de recuperação. Acrescentar gráfico mensal em R$ e tabela detalhada expansível, evitando uma grade muito larga como primeira tela.

Na tabela, organizar colunas por energia reativa excedente e demanda reativa excedente, depois posto e natureza indutiva/capacitiva quando identificados. Cada grupo contém quantidade, unidade, preço aplicado e valor cobrado, com origem e estado do campo. Não criar combinações inexistentes nem preencher campos desconhecidos com zero. Valores zero confirmados, ausentes e não aplicáveis têm representações distintas.

Rótulos UFER/UFDR e semelhantes podem aparecer como nomenclatura original da distribuidora, acompanhados do significado normalizado. A imagem usa “kW” em colunas UFER; essa unidade precisa ser conferida no documento e no layout de origem antes da homologação. Não inferir unidade correta apenas pela imagem nem reutilizar automaticamente esse cabeçalho.

Rodapé soma valores monetários compatíveis e apresenta subtotais reconciliáveis por componente e total geral. Não somar tarifas unitárias: uma soma de R$/unidade não constitui tarifa do período. Quantidades de demanda em kW não são somadas como demanda contratável; priorizar valores mensais e máximo do período. Energia pode ser totalizada apenas com unidades e definições compatíveis. Eventual preço médio deve declarar sua ponderação e não substituir a tarifa mensal de origem.

Correções e recuperação hipotética atualizam uma nova execução; a tabela observada permanece distinguível do cenário de recuperação. Não usar o total de reativos como economia garantida nem somá-lo novamente se já estiver incluído no cenário econômico combinado.

### 11.3 Referências visuais e validação com a planilha

Os valores visíveis de demanda de 338 kW e candidato de 290 kW, custos de R$ 136.632,16 e R$ 120.644,48 e diferença de R$ 15.987,68 são referências de apresentação transcritas da imagem. A subtração é consistente, mas não comprova como os custos foram calculados. O total de reativos exibido é R$ 1.413,43; o fechamento deve ser conferido nas linhas originais, sem usar OCR visual como fixture financeira aprovada.

A conferência de 06/11/2026 das planilhas recebidas reproduziu aritmeticamente os totais citados, sob as hipóteses dos próprios arquivos, mas identificou divergências de período, tributação e fórmulas. Evidências: [conferência das planilhas](docs/corpus/workbook-review.md) e [conferência inicial das faturas](docs/corpus/invoice-review.md). Essa reprodução não homologa as premissas nem os valores das imagens.

Homologar a comparação somente com dados estruturados, fórmulas da planilha e preços efetivos cheios por componente e vigência conferidos; não exigir auditoria separada dos impostos. Registrar divergências por mês/componente. Uma captura de gráfico não permite recuperar medições precisas pela altura das barras. Nenhum valor das imagens se torna teste homologado automaticamente; novos exemplos devem ser sintéticos identificados ou derivados de corpus autorizado e conferido.

## 12. Segurança, privacidade e operação

- HTTPS, cookies Secure/HttpOnly/SameSite, CSRF nas operações autenticadas por cookie, incluindo requisições HTMX, escaping nos templates Jinja2 e CSP; HTMX e scripts hospedados localmente. Web e API na mesma origem por padrão; CORS restrito a origens autorizadas quando necessário, sem curinga com credenciais.
- Tokenização web por token de sessão opaco, aleatório e revogável em cookie seguro; identidade, permissões e estado da sessão ficam no servidor. Armazenar apenas representação protegida do token no banco, rotacionar após autenticação/elevação de privilégio e aplicar expiração por inatividade e absoluta. Não expor tokens no HTML ou localStorage. Logout, bloqueio da conta e redefinição de senha revogam as sessões pertinentes. Token não substitui autorização.
- Senhas: política da seção 4.1 validada pelo backend; hash Argon2id com salt gerenciado por biblioteca apropriada e parâmetros calibrados. Nunca registrar senha/confirmadores em logs. Suportar colagem e gerenciadores de senha.
- Ativação de e-mail: token aleatório de uso único com validade inicial de 24 horas. Recuperação de senha: token independente, uso único e validade de 30 minutos. Persistir apenas representação protegida, finalidade e expiração; consumir atomicamente. Reenvio invalida o anterior; links usam origem confiável e não são registrados em logs. Recuperação não ativa silenciosamente conta pendente.
- Mensagens neutras, limites por usuário/IP/e-mail e resposta consistente em login, cadastro, ativação e recuperação. Controlar tentativas de senha e reenvios sem bloqueio permanente provocado por terceiros.
- Autorização por perfil e dono/empresa em todas as rotas, inclusive status, faturas, PDF, exportação, correção e exclusão; testes de acesso cruzado. Payloads do cliente não podem escolher dono, empresa alheia ou perfil privilegiado.
- MFA administrativo, auditoria, revogação de sessões e privilégio mínimo.
- Processamento de PDFs sem rede, usuário sem privilégio, limites de CPU, RAM, tempo e pixels. Assinatura de PDF não é proteção suficiente contra conteúdo malicioso.
- WeasyPrint sem acesso arbitrário a rede ou arquivos locais; permitir somente recursos controlados do relatório.
- Segredos reais fora do repositório e segredos de produção geridos pela hospedagem; `.env` local pode ser versionado com valores exclusivos de desenvolvimento conforme 10.5; dependências fixadas e verificadas.
- Rate limit no proxy e na aplicação; contador consistente entre instâncias em produção.
- Logs técnicos sem PDFs, imagens, códigos, tokens, conteúdo faturável ou dados pessoais desnecessários.
- Política proposta: 180 dias para simulações e relatórios, incluindo snapshots e caches; exclusão diária. Dados de contato seguem finalidade e prazo próprio informado, sem retenção indefinida presumida.
- Solicitação de exclusão abrange conta, dados derivados e documentos gerados, ressalvadas obrigações legais identificadas. Backups têm prazo de expiração e reaplicação de exclusões após restauração.
- Definir controlador, operador, canal do titular, finalidade e base legal antes do lançamento. Aceite genérico não substitui essa definição; marketing separado.
- Backups criptografados e restauração testada. Sem documentos originais nos backups.

## 13. API mínima e telas

Rotas versionadas em `/api/v1`; respostas de erro com `code`, `message`, `fields` e identificador técnico sem conteúdo sensível.

| Área | Operações |
| --- | --- |
| Acesso | Cadastrar, confirmar/reenviar ativação, entrar com e-mail/senha, recuperar/redefinir senha, sair e revogar sessões |
| Perfil e empresa | Consultar e atualizar dados próprios permitidos |
| Simulações | Criar rascunho com cota de duas, listar, consultar, corrigir, confirmar e excluir |
| Faturas | Adicionar incrementalmente, consultar estado/dados e remover por identificador |
| Cálculo | Iniciar execução idempotente e consultar resultado |
| Cenários | Calcular prévia manual/automática pela API e salvar execução com parâmetros e revisão de origem |
| Relatórios | Visualizar, baixar PDF e solicitar exclusão |
| Contato | Criar pedido explícito e consultar situação própria |
| Admin / CRM | Consultar clientes e leads, manter situação/notas internas, corrigir simulações com auditoria, importar tarifas, ativar regras e recalcular em nova versão |
| Orçamentos | Criar, revisar e emitir orçamento vinculado ao cliente e à revisão da simulação; registrar encaminhamento manual por e-mail |
| Operação | Health e readiness sem expor configuração ou dados |

Recursos sob `/api/v1`: `/auth`, `/me`, `/me/company`, `/simulations`, `/simulations/{id}/invoices`, `/simulations/{id}/calculations`, `/simulations/{id}/reports` e `/admin/*`. Usar GET para consulta, POST para criação e comandos explícitos, PATCH para campos editáveis e DELETE para remoção. Upload multipart retorna 202 com identificador e URL de status; a conexão não permanece aberta durante OCR. Listas são paginadas. Conflitos de cota ou revisão retornam 409 com códigos estáveis como `simulation_limit_reached` e `simulation_revision_conflict`. Documentar estados, limites, idempotência e decimais string no OpenAPI.

A web usa sessão segura em cookie. Para o futuro mobile, prever adaptador de autenticação com tokens revogáveis e armazenamento seguro no dispositivo, implementado na fase do app. Autorização e serviços de negócio independem do mecanismo de credenciais.

Telas Jinja2 + HTMX: landing page, cadastro, confirmação de e-mail, login, recuperação/redefinição de senha, painel do cliente, perfil/empresa, dados da unidade, upload/progresso, conferência, relatório, conta/exclusão e painel administrativo com clientes, leads, ficha comercial, edição auditada e orçamentos. Layouts, macros e parciais reutilizáveis de formulário, etapas, lista de faturas, progresso, cartões, tabelas, mensagens e confirmação de exclusão. HTMX atualiza estados, conferência e prévias sem recarregar a página inteira; JavaScript local mínimo complementa progresso de upload, gráficos e descarte de respostas antigas. Responsivo em celular e desktop, contraste AA, tabelas acessíveis e valores com unidade.

Temas claro e escuro fazem parte da entrega, com seletor, preferência persistida e opção de seguir o sistema. Usar paleta profissional e tokens semânticos consistentes em páginas, formulários e gráficos; PDF mantém tema próprio para impressão. Tailwind CSS é adotado para estilização, compilado localmente com varredura dos templates e classes detectáveis, sem CDN/runtime de produção. O build de CSS é uma etapa de desenvolvimento/CI e não obriga Node no servidor de execução; usar CLI standalone ou ferramenta de build dedicada. CSS minificado, assets versionados/cacheáveis, scripts locais e carregamento de gráficos apenas onde necessários sustentam a meta de carregamento rápido.

## 14. Desempenho e observabilidade

Metas iniciais a medir, não resultados já comprovados. Ambiente-base do benchmark: Linux, 2 vCPU, 4 GB RAM, SSD; registrar versões, tamanho e páginas do corpus.

| Operação | Meta inicial |
| --- | --- |
| Rotas leves e status | p95 até 500 ms no piloto com 10 usuários simultâneos |
| Motor para 12 competências | Até 1 s por simulação no corpus de referência |
| 12 PDFs textuais, até 36 páginas | Até 20 s de processamento, excluído upload |
| OCR seletivo | Meta de até 15 s por página típica; limite de 180 s por arquivo |
| PDF do relatório | Até 5 s em relatório de 12 competências |

Um lote não pode ocupar toda a RAM. Limite inicial: processo OCR de até 1 GB e concorrência um; impor limite de duração total do lote e rejeitar carga além da capacidade. Validar metas com documentos difíceis antes de publicar promessa ao cliente.

Medir tempos de extração/OCR/cálculo/PDF separadamente, pico de memória, fila, taxa de revisão e erro por layout. Não registrar conteúdo. Se processamento textual falhar repetidamente, corrigir parser antes de aumentar servidor ou usar IA mais cara.

## 15. Fases e critérios de aceite

Fase 0 concluída com aceite explícito do usuário em 06/11/2026 para os contratos e o gabarito mínimo local (fatura/pipeline v0.2; acesso v0.1). Referências: [contratos](docs/contracts/invoice-data.md) e [corpus](docs/corpus/README.md). As demais fases continuam pendentes; o checklist não representa funcionalidades implementadas.

### Sequência de construção

Construir primeiro o backend: estrutura FastAPI e configuração → modelos/migrações SQLite → usuários/autenticação/permissões → seed admin/cliente → fluxo principal em três fases → interface web completa e CRM → homologação → orçamentos → preparação de produção. Cada módulo pode ter telas mínimas de inspeção, mas o frontend completo não bloqueia a validação dos serviços pela API.

O coração do sistema tem exatamente três fases encadeadas:

1. **Leitura e armazenamento (Fase 2):** dados da unidade → admissão do PDF → extração textual/OCR → validação → persistência relacional → conferência → descarte. Saída: conjunto estruturado versionado, sem PDFs persistentes.
2. **Simulação (Fase 3):** conjunto confirmado + tarifas/regras → cálculos e cenários → execução congelada com séries mensais. Saída: resultado reproduzível e premissas, sem HTML/PDF como dependência do motor.
3. **Relatório (Fase 4):** execução congelada → resumo, gráficos, memória e PDF. Saída: apresentação consistente, respeitando módulos parciais e indisponíveis.

Testar cada fronteira antes da seguinte: a fase de cálculo pode usar fixtures estruturadas enquanto o corpus é homologado, mas a integração final segue leitura → armazenamento → cálculo → relatório. Nenhuma interface calcula valores financeiros por conta própria.

### Checklist de entregas

- [x] **Fase 0 — Contratos e corpus**

  - [x] Preparar contratos e exemplos sintéticos; conferir a série local ENEL SP A4 Azul de agosto/2025 a julho/2026 nos blocos mínimos de faturamento, cliente/UC, classificação, datas e demandas contratadas. Registrar fontes consultadas, proveniência, limites e desconhecidos.

  - [x] Aceite: dicionário mínimo dos blocos faturáveis, cliente/UC, classificação, datas e demandas contratadas, restrições e esperado por fatura aprovado; desconhecidos identificados. Não exigir cadastro fiscal/administrativo completo, auditoria de boleto ou aprovação de informações fora desse escopo.

  Aceite explícito do usuário em 06/11/2026 para o mínimo das doze faturas, com ressalvas no STATUS. Anonimização/publicação de fixtures reais e homologação comercial de parser, motor, tarifas alternativas e vigências permanecem na Fase 5 e nas dependências da seção 16; não foram aprovadas por este aceite.

- [x] **Fase 1 — Base leve e banco**

  - [x] Configurar FastAPI com Jinja2, HTMX local e HTML/CSS, separando rotas web e API JSON dos serviços de aplicação.
  - [x] Definir OpenAPI, cliente HTTP, erros, paginação e idempotência.
  - [x] Definir estrutura futura de layouts/macros; adiar acabamento visual para depois dos serviços centrais.
  - [x] Implementar cadastro com empresa, responsável, endereço, telefone e dupla confirmação de e-mail/senha; validar composição e mínimo de oito caracteres no backend.
  - [x] Implementar ativação por e-mail, login com e-mail/senha, recuperação, logout e vínculo cliente/empresa.
  - [x] Implementar controle de usuários no backend, hash de senha, token de sessão, expiração, rotação e revogação.
  - [x] Criar tabelas/migrações em ordem de dependências conforme 10.4, com FKs e transações validadas.
  - [x] Criar seed explícito e idempotente com admin padrão e cliente teste, empresas sintéticas e credenciais locais; impedir execução em produção.
  - [x] Verificar login, isolamento e fluxo de simulação tanto para admin quanto para cliente teste.
  - [x] Organizar configuração local e diretórios de dados, sem executar containers; documentar o caminho futuro para PostgreSQL/Docker.
  - [x] Provisionar administrador internamente e implementar permissões por perfil e dono.
  - [x] Garantir cota de duas simulações em transação, incluindo criações simultâneas.
  - [x] Implementar exclusão que libere a vaga e impeça recriação por jobs tardios.

  - [x] FastAPI, API REST independente da apresentação, SQLAlchemy, Alembic, DecimalType, autenticação e catálogo. Verificações locais/CI em SQLite; compatibilidade PostgreSQL planejada e validada antes da produção, sem exigir containers agora.

  - [x] Aceite: subida local sem Docker, migrações SQLite do zero e upgrade, seed repetível sem duplicatas, decimal sem perda e acesso isolado por usuário.

  Conclusão local em 06/11/2026, a pedido do usuário: 68 testes com SQLite/migrações/seed/Decimal, HTTP/Edge, sessões, isolamento/concorrência e SMTP sintético. Critério final validado com tarefas reais de controle e executor sintético concorrente: exclusão cancela queued/running, revoga leases e libera slot atomicamente; conclusão tardia não chama persistência. Rollback, revisão alterada, dois executores, heartbeat e expiração também testados. Não foram implementados coordenador/OCR/cálculos: a Fase 2 integra os adaptadores reais ao protocolo existente. Provedor externo não homologado, envio disabled por padrão e catálogo sintético. Interface completa/Tailwind/temas ficam na Fase 4. Ver STATUS/API/SETUP/DATABASE/EMAIL/TASKS; não homologado comercialmente.

- [ ] **Fase 2 — Coração 1/3: leitura e armazenamento de faturas**

  - [ ] Salvar dados da unidade e endereço da ligação antes de liberar faturas; oferecer cópia confirmada do endereço da empresa.
  - [x] Criar/revisar tabelas de faturas, itens, medições e proveniência antes da extração integrada, respeitando a ordem de FKs.
  - [ ] Capturar demandas medidas por posto no quadro de medição Azul/Verde, separadas da contratação/faturamento; preservar mercado por ciclo e evidências de migração ACL, sem inferência por ausência em leitura incompleta.
  - [ ] Identificar distribuidora/layout no cabeçalho da etapa de anexação/leitura; tratar não suportados com bloqueio explícito e pedido de contato, sem fallback silencioso para ENEL.
  - [ ] Persistir cada extração em transação atômica, com retry idempotente e rollback sem órfãos.
  - [ ] Implementar seleção local e botão “Ler fatura” que envia e extrai cada arquivo, permitindo adições incrementais até 12.
  - [ ] Aplicar limites acumulados por simulação e controlar capacidade de admissão.
  - [ ] Exibir progresso de envio separado da leitura e contadores por estado.
  - [ ] Ordenar faturas por ciclo/competência e destacar datas ainda não identificadas.
  - [ ] Permitir remoção, cancelamento e descarte; ignorar resultados tardios.
  - [ ] Restaurar lista e dados estruturados; indicar necessidade de reenvio após interrupção.
  - [ ] Habilitar “Simular” somente com dados válidos e sem pendências; revalidar na API.
  - [ ] Liberar simulação com a primeira fatura válida/conferida e recomendar 12 competências consecutivas, sem exigir lote completo.
  - [ ] Testar remoção durante leitura e conflito entre edição, remoção e cálculo.

  - [ ] Extrator textual, OCR seletivo, duplicidade, refaturamento, ordenação, revisão e descarte.

  - [ ] Aceite: todos os campos críticos do corpus conferidos; nenhum erro crítico aceito silenciosamente. Testar PDF textual, digitalizado, híbrido, protegido, inválido e lote misto. Verificar ausência de arquivos persistentes inclusive no proxy e temporários.

- [ ] **Fase 3 — Coração 2/3: motor independente de simulação**

  - [ ] Implementar candidatos manuais por posto, validando grade, limites e restrições conjuntas.
  - [ ] Retornar custos e séries mensais de prévia com a mesma base do cenário atual.
  - [ ] Distinguir candidato exploratório, sugestão automática e resultado salvo; preservar diferença desfavorável.
  - [ ] Validar que tarifa unitária não seja somada como tarifa do período e que demanda em kW não vire total contratável por soma mensal.
  - [ ] Comparar Azul↔Verde com medições por posto e preços cheios equivalentes; suprir preços ausentes via ANEEL com incidências/alíquotas documentadas, sem tributar duas vezes nem inventar medições.
  - [ ] Testar maior tarifa por componente, máximo anterior ao último mês, empate, série cativa, migração ACL intermediária, série toda ACL e mercado incerto; manter histórico e comparação separados, referência equivalente e bloqueio seletivo por parâmetros ausentes.

  - [ ] Demanda regular/ultrapassagem, ociosidade com relação de 82% do preço da demanda contratada e confronto com os valores observados, otimização, reativos observados, comparação de modalidade e cenários encadeados.

  - [ ] Aceite: testes de fronteira 105%, exemplo 160 × T, ausência versus zero, comparação com preços cheios compatíveis, limite global de ciclos e igualdade entre economia total e diferenças dos cenários. Aumento de demanda contratada não pode reduzir custos por erro de sinal ou duplicação tributária.

- [ ] **Fase 4 — Coração 3/3: relatório, interface e captação**

  - [ ] Implementar controles de demanda manual, recálculo, restauração e aplicação de sugestão automática.
  - [ ] Impedir que resposta antiga de prévia substitua o cenário mais recente; identificar resultados desatualizados.
  - [ ] Comparar gráficos atual/simulado na mesma escala e separar ponta/fora de ponta quando aplicável.
  - [ ] Identificar ociosidade, contratação, tolerância e ultrapassagem sem duplicar grandezas nem misturar kW e R$.
  - [ ] Exibir cartões de custo do componente no período, diferença e projeção anual separada.
  - [ ] Criar resumo, gráfico mensal e tabela expansível de reativos com unidades, estados e subtotais reconciliáveis.
  - [ ] Garantir equivalência das séries na web/PDF e tabela acessível em telas pequenas.

  - [ ] Finalizar landing page elegante com apresentação, exemplo fictício, cadastro e login.
  - [ ] Entregar temas claro/escuro, paleta profissional e estados acessíveis em formulários e gráficos.
  - [ ] Configurar Tailwind compilado localmente e componentes em layouts, macros e parciais Jinja2.
  - [ ] Exibir relatório com destaque à economia em R$, demandas e reativos, mantendo limites e premissas visíveis.
  - [ ] Criar painel do cliente com empresa, cartões e contador de simulações “0/2”.
  - [ ] Bloquear terceira simulação até excluir uma das existentes, com confirmação clara.
  - [ ] Entregar formulário em etapas, acessível, responsivo e com preservação dos dados salvos.
  - [ ] Exibir distribuidora/suporte no cabeçalho da anexação/leitura e contato explícito para layout não suportado; apresentar referência tarifária, recorte ACL, formação do preço cheio e limites da comparação no relatório.
  - [ ] Entregar CRM essencial exclusivo do administrador: clientes, leads, busca, filtros e ficha comercial.
  - [ ] Implementar notas internas, situação comercial e histórico de contatos.
  - [ ] Permitir edição administrativa de dados com justificativa e auditoria, gerando novo cálculo.
  - [ ] Entregar ao admin o mesmo fluxo de leitura, conferência, cálculo e relatório do cliente, com dono e autor distintos quando atuar pelo CRM.
  - [ ] Testar que clientes não acessam rotas administrativas, notas internas ou dados alheios.

  - [ ] Interface completa, gráficos, memória de cálculo, PDF, pedido de contato e administração mínima.

  - [ ] Aceite: um cliente conclui o fluxo no celular; relatório não mostra conclusões de módulos bloqueados; resultados coincidem com execução congelada; correção cria nova versão.

- [ ] **Fase 5 — Homologação técnica**

  - [ ] Conferir dados e fórmulas originais da planilha antes de homologar os números das capturas.
  - [ ] Validar nomenclatura/unidades de UFER/UFDR no layout e documento de origem.
  - [ ] Reconciliar custos atual/manual e reativos por mês, componente, preço efetivo cheio aplicável.

  - [ ] Série real comparada com planilha manual independente, regras e tarifas por vigência. Homologar Azul→Verde; Verde→Azul fica condicionado aos dados disponíveis. AS e outros layouts só são habilitados após testes próprios.

  - [ ] Aceite: diferenças explicadas por item; nenhuma fórmula crítica validada apenas por teste que repete o código. Testes de propriedades, regressões e casos adversos, além de benchmarks.

- [ ] **Fase 6 — Orçamentos no CRM (escopo web)**

  - [ ] Definir serviços, itens, preços, validade e condições comerciais.
  - [ ] Criar tabelas e API de orçamentos vinculados ao cliente e à revisão da simulação.
  - [ ] Implementar rascunho, revisão, emissão PDF e estados emitido/enviado/aprovado/recusado.
  - [ ] Permitir download pelo administrador para envio posterior por e-mail, registrando encaminhamento manual sem disparo automático na geração.
  - [ ] Auditar mudanças e restringir geração ao administrador.
  - [ ] Definir acesso do cliente somente aos orçamentos publicados para ele.
  - [ ] Aceite: orçamento reproduzível, com revisão de origem identificada, sem alterar o diagnóstico.

- [ ] **Fase 7 — Produção**

  - [ ] Iniciar esta fase somente após homologação e orçamentos (Fase 6); produção é a última entrega do escopo web.
  - [ ] Preparar e validar Dockerfile/Compose, PostgreSQL em container, volumes, healthchecks e execução única de migrações.
  - [ ] Executar suíte e migrações no PostgreSQL; validar transporte dos dados SQLite conforme 10.3, com backup e plano de retorno.
  - [ ] Retirar contas/bypasses de teste da produção, provisionar admin real e separar segredos reais do Git e do build.

  - [ ] Validar CORS, sessões, MFA e isolamento entre cliente e administrador.
  - [ ] Verificar cota sob concorrência e exclusão durante processamento.
  - [ ] Aprovar jornada completa em celular e desktop com cliente-piloto.

  - [ ] PostgreSQL, HTTPS, e-mail transacional, MFA, backups/restauração, política de retenção, limites, monitoramento e revisão dos textos de privacidade.

  - [ ] Aceite: controle de acesso, CSRF, abuso de senhas/tokens, ativação, recuperação, isolamento de PDF, rate limit e exclusão testados; restauração verificada; requisitos regulatórios usados no lançamento conferidos em fonte vigente; piloto assistido aprovado.


- [ ] **Fase 8 — Evolução futura: aplicativo mobile**

  - [ ] Reutilizar API REST e autorização existentes, sem duplicar regras de negócio.
  - [ ] Implementar autenticação do app com expiração, revogação e armazenamento seguro.
  - [ ] Integrar envio incremental, status, consulta de resultados e limite de duas simulações.
  - [ ] Aceite: web e app respeitam a mesma cota e o mesmo isolamento de dados.


## 16. Decisões encerradas e informações externas restantes

As escolhas técnicas desta SPEC são a recomendação padrão, sem necessidade de reabrir P1–P5. Ficaram definidos Python/FastAPI, interface Jinja2 + HTMX com templates reutilizáveis, Tailwind compilado localmente, temas claro/escuro, API REST desacoplada preparada para mobile, SQLite→PostgreSQL, cadastro completo, login por e-mail/senha com confirmação inicial de e-mail, tokens revogáveis, OCR local seletivo acionado por “Ler fatura”, conferência de campos críticos, limite de duas simulações por cliente e cobertura de 1–12 faturas por simulação sem falsa garantia de confiança. O CRM inclui acompanhamento, relatórios, novos cenários e geração de orçamentos em fase própria do escopo web, para encaminhamento posterior pelo administrador. Esta revisão substitui o acesso por código de e-mail e a leitura automática ao selecionar arquivo.

Restam informações externas que não podem ser inventadas:

| Informação | Como fechar | Efeito enquanto faltar |
| --- | --- | --- |
| Corpus real ENEL e conferência | Série e planilha de referência do cliente-piloto | Parser e fórmulas não homologados comercialmente |
| Identidade da distribuidora | Cadastro/catálogo e nome/unidade da fatura; CNPJ do catálogo quando necessário | Preços somente para a distribuidora identificada, sem reextração fiscal obrigatória em cada conta |
| Preços cheios por componente e perdas | Fatura validada ou tarifa ANEEL com formação tributária documentada (§8.6); ociosidade com preço próprio | Falta de tarifa, incidência/alíquota necessária ou perdas bloqueia somente o cálculo dependente; não tributar de novo preço já cheio |
| Contrato e restrições de alteração | CUSD, histórico e regra vigente | Potencial técnico sem data de implantação |
| Dados por posto na Verde | Quadro de medição da própria fatura prioritariamente; portal/registros complementares quando faltarem | Contratação única não impede comparação se medições por posto forem suficientes; sem elas, cenário condicionado/inconclusivo |
| Referência e marco ACL | Mercado confirmado por ciclo e preços elegíveis (§§7.1 e 8.6) | Marco incerto exige revisão; não misturar referência cativa com desconto ACL nem inventar preço do fornecedor |
| Dados horários de reativos | Medição ou arquivo da distribuidora | Cobrança observada e potencial condicionado |
| Empresa, canal e política de dados | Dados comerciais do responsável | Publicação comercial bloqueada até configuração |
| Provedor e ambiente de hospedagem | Serviço com e-mail, RAM e isolamento compatíveis | Login real e metas dependem do ambiente |

Esses itens não impedem construir e testar o sistema com fixtures sintéticas identificadas. Impedem somente afirmar homologação, viabilidade ou conformidade que ainda não foi demonstrada.

## 17. Fontes e verificação regulatória

Fontes consultadas em 03/11/2026:

- ANEEL — REN 1000/2021, texto compilado, especialmente faturamento regular, art. 301 e arts. 302–304: https://www2.aneel.gov.br/cedoc/ren20211000.html
- PDF oficial indexado da REN 1000: https://www2.aneel.gov.br/cedoc/ren20211000.pdf
- ANEEL — Tarifas de aplicação das distribuidoras, TE/TUSD e recursos CSV: https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica
- ANEEL — Dicionário de dados tarifários, acessível pelo conjunto acima.
- ANEEL — Ranking das tarifas e limites dos valores publicados (tributos e outros elementos não incluídos; conferir exceções da fonte): https://www.gov.br/aneel/pt-br/assuntos/tarifas/ranking-das-tarifas (consulta em 09/11/2026; não define fórmula tributária universal).
- Energisa — explicação operacional de ultrapassagem: https://www.energisa.com.br/para-sua-empresa/espaco-grandes-clientes/grandes-clientes/tarifas-de-ultrapassagem

Limite desta revisão: os endereços diretos do texto compilado ANEEL retornaram bloqueio de acesso na consulta automatizada; houve acesso ao catálogo tarifário oficial e resultados indexados da norma. Conferir a redação consolidada e eventuais alterações na homologação é requisito antes de liberar cálculos comerciais. Cartilhas antigas baseadas na REN 414 não devem definir automaticamente prazos atuais.

Atualização de 06/11/2026: lida a reprodução local da REN 1000, identificada por metadados Leis.org; o texto oficial compilado continuou retornando 403. Catálogo tarifário acessível, sem importação de preços. Limites e fontes: [conferência regulatória](docs/corpus/regulatory-review.md).

A especificação contém propostas de engenharia e produto; não equivale à homologação do motor, à auditoria de uma conta real ou à implementação do sistema.
