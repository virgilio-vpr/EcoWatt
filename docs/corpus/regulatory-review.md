# Referências regulatórias e tarifárias — conferência de 06/11/2026

Este registro delimita as evidências disponíveis; não é parecer regulatório nem validação integral de vigência.

## PDF local da REN 1000

Arquivo `docs/ANEEL/REN 1000.pdf`, hash registrado no inventário. O leitor identificou 183 páginas. O título dos metadados menciona `Leis.org`; a primeira página apresenta a REN 1000/2021 e as páginas iniciais contêm redações anteriores e alteradas, inclusive referência a alteração de 2026. Portanto é uma reprodução de consulta, sem comprovação de origem oficial ou data exata de consolidação apenas pelo nome.

Leitura dirigida: página física 80 contém o art. 301 e páginas 81–82 tratam de fator de potência e reativos (arts. 302–304). As expressões matemáticas não ficam integralmente representadas na extração textual; não reconstruir equações a partir de fragmentos ou de redação revogada misturada ao texto vigente. O número da página do PDF não equivale ao número da página de publicação oficial.

## Fontes oficiais consultadas

- [Texto compilado ANEEL](https://www2.aneel.gov.br/cedoc/ren20211000.html): nova tentativa retornou HTTP 403. A redação consolidada completa não foi validada nesta entrega.
- [Anexo oficial da REN 1000 indexado](https://www2.aneel.gov.br/cedoc/atren20211000.pdf): resultados oficiais indexados identificam as referências VRERE (TE B1 em bandeira verde) e VRDRE (demanda fora de ponta da Azul). A consulta não fecha todas as alterações e vigências aplicáveis à série.
- [Catálogo oficial de tarifas de aplicação](https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica): página acessível, com recursos CSV e dicionário. Nenhum arquivo CSV foi importado, nenhuma linha tarifária foi aprovada e nenhum preço corrente foi presumido.

Para uma homologação histórica, vincular cada regra e tarifa à distribuidora/CNPJ e vigência do ciclo. Para comparação a uma data de referência, usar essa mesma data para os dois cenários. Tarifas de aplicação, preço efetivo com tributos e Base Econômica são conceitos distintos; o catálogo não preenche medições ausentes.

## Decisão de escopo confirmada com o usuário

Analisar cobranças reativas excedentes observadas. Se a ausência de cobrança estiver confirmada, não criar cenário independente de aparecimento de reativos só porque existe tarifa no catálogo. Leitura incompleta permanece desconhecida. Mudanças de demanda/modalidade com efeito reativo não calculável devem declarar a limitação, sem afirmar que uma ausência histórica comprova ausência futura.

Esses critérios foram explicitados na SPEC §8.4. Não alteram a necessidade de referências auxiliares quando um cálculo efetivamente suportado precisar delas.
