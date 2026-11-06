# E-mail e acesso local — Fase 1

Entrega verificada em 06/11/2026 com dados sintéticos. Adaptador SMTP da biblioteca padrão Python, sem serviço externo contratado ou credenciais reais. `.env` e `.env.example` mantêm EMAIL_PROVIDER=disabled; habilitar envio é uma configuração explícita. Não há caixa de entrada HTTP pública, gravação de mensagens/tokens em arquivos ou log de protocolo SMTP.

## Configuração

| Variável | Valor inicial | Função |
| --- | --- | --- |
| EMAIL_PROVIDER | disabled | disabled ou smtp |
| SMTP_HOST | vazio | Servidor autorizado, obrigatório com smtp |
| SMTP_PORT | 587 | Porta de 1 a 65535 |
| SMTP_SECURITY | starttls | starttls, ssl ou local |
| SMTP_USERNAME / SMTP_PASSWORD | vazios | Informar os dois juntos quando o servidor exigir autenticação |
| SMTP_SENDER | noreply@ecowatt.test | Remetente sintético; substituir pelo autorizado pelo provedor ao homologar |
| SMTP_TIMEOUT_SECONDS | 5 | Timeout de socket entre 1 e 10 segundos |
| PUBLIC_ORIGIN | http://127.0.0.1:8000 | Origem confiável do aplicativo e dos links |

`starttls` exige TLS antes de autenticar ou enviar; não faz fallback se o servidor recusar TLS. `ssl` inicia a conexão cifrada. Ambos usam o trust store/contexto padrão do Python, validando certificado e hostname, conforme [smtplib](https://docs.python.org/3.13/library/smtplib.html). Não há opção para ignorar validação de certificado.

`local` aceita somente 127.0.0.1/::1 numéricos, sem usuário/senha, para um capturador SMTP local de desenvolvimento. Não permite hostname externo ou localhost com resolução de nome. O projeto não instala nem deixa um capturador rodando; a suíte sobe um servidor efêmero em memória que não encaminha mensagens e o encerra ao terminar.

Credenciais reais vêm do ambiente/gestor de segredos, nunca dos arquivos `.env` versionados ou do chat. Não configurar produção nesta entrega: runtime segue restrito a development/test. Remetente, DNS e entregabilidade real precisam ser homologados com o serviço escolhido. Nenhum destinatário externo foi contatado nos testes.

## Comportamento transacional e falhas

Cadastro salva empresa/usuário pendente/token protegido atomicamente e confirma a transação **antes** de enviar. Reenvio também cria/invalida tokens em transação curta. A conexão SMTP ocorre fora de qualquer transação SQLite, em tarefa de background da resposta HTTP: não mantém o lock de escrita nem atrasa a resposta pela latência do provedor, e o link já pode ser consumido quando a mensagem chega. Isso reduz enumeração temporal entre conta existente e desconhecida.

Se o SMTP falhar ou a aceitação da mensagem for incerta, somente o token daquele envio é invalidado; a conta fica pendente para permitir reenvio. Não há retry automático que possa duplicar envios. Um reenvio mais recente não é invalidado pela falha de um envio antigo. A auditoria registra apenas a ação e ID do token, sem endereço, conteúdo ou diagnóstico do servidor.

Com SMTP habilitado, cadastro/reenvio/recuperação retornam 202 e a mesma mensagem neutra para pedido aceito, e-mail desconhecido, conta inelegível ou falha de entrega. **202 não comprova envio.** Essa escolha evita revelar existência de conta por erro do provedor. Em indisponibilidade, aguardar e solicitar reenvio; os limites continuam aplicados. Com provider disabled, a resposta continua 503 uniforme e nenhum cadastro é criado.

Não existe fila/outbox persistente: a interrupção do processo entre commit e conclusão da tarefa pode deixar conta pendente ou pedido sem entrega. Reenvio é a recuperação prevista nesta base. Fila com tokens cifrados e operação de produção exigiria desenho próprio; tokens em claro não serão colocados no banco para resolver isso implicitamente.

## Consumo dos links

Links de ativação e recuperação usam `/auth/activation#token=...` e `/auth/reset#token=...`. JavaScript local lê o fragmento, retira-o do histórico/URL corrente e guarda o valor somente na memória da página. Não usa localStorage/sessionStorage, campo oculto ou token em HTML renderizado. O fragmento não compõe a requisição HTTP; a limpeza usa [replaceState](https://developer.mozilla.org/en-US/docs/Web/API/History/replaceState).

Abrir a página não consome o token. É preciso clicar em Confirmar e-mail ou informar/confirmar a nova senha e enviar. A página obtém CSRF e usa os endpoints JSON já existentes; não duplica regras de autenticação. O servidor mantém finalidade, validade de 24h/30min, consumo único e revogação normal de sessões. A nova senha nunca entra em URL. Após limpar a URL, recarregar a página exige reabrir o link recebido; não se conserva token para reload.

Páginas mínimas: `/auth/register`, `/auth/login`, `/auth/resend-activation`, `/auth/forgot-password`, `/auth/activation`, `/auth/reset`. Há rótulos, política de senha, dupla confirmação, mostrar/ocultar senha e status de envio. CSP mantém scripts locais, sem inline/eval. Interface completa, landing, Tailwind, temas e acabamento continuam na Fase 4.

## Verificações executadas

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_mail_delivery.py -q
$env:ECOWATT_BROWSER_TESTS='1'
try {
  .\.venv\Scripts\python.exe -m pytest tests/test_auth_browser.py -q
} finally {
  Remove-Item Env:ECOWATT_BROWSER_TESTS
}
```

SMTP de loopback real: cadastro, MIME de ativação/recuperação, confirmação por POST e login. Testes de TLS/SSL/autenticação usam doubles, inclusive recusa de STARTTLS sem downgrade. Teste de transação prova que outra conexão pode escrever durante a entrega; outro teste HTTP mantém a entrega bloqueada e confirma que 202 já chegou. Falhas ficam neutras e permitem reenvio.

Navegador: Playwright 1.64.1 instalado somente como dependência dev no `.venv`, usando Edge já instalado, headless, sem baixar navegador/instalar Node global ou mudar políticas. Cadastro → captura SMTP → ativação → reutilização recusada → login → captura de recuperação → troca de senha → sessão anterior revogada → novo login. Nenhum erro JavaScript, token em URL de request ou recurso externo da página. O teste também cobriu reabertura do fragmento na mesma página. Não habilita bypass de CSP ou validação TLS.

O teste de navegador exige ECOWATT_BROWSER_TESTS=1 e Edge instalado. Sem a flag, ele fica explicitamente skipped; não interpretar skip como teste executado. Se houver bloqueio organizacional, não alterar políticas para forçar a execução. O workflow Windows inclui uma etapa explícita para esse teste; homologação com SMTP externo permanece pendente.
