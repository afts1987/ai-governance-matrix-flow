# Guião de demonstração — 10 minutos

**Mensagem central:** com tanta legislação, o erro não é falhar um artigo; é misturar o que está em vigor com o que está adiado, o que é lei com o que é norma, e o que se aplica a quem fornece com o que se aplica a quem usa. A matriz impede esses três erros. O agente impede a matriz de envelhecer. As pessoas continuam a decidir.

## Abertura (30 s) — diz isto antes de mostrar o que quer que seja
**Cliente:** o responsável de compliance de uma organização que usa IA de terceiros (uma sociedade de advogados, um banco pequeno, uma PME) e que tem de provar que acompanha a regulação.
**Dor:** a matriz de governação de IA cruza AI Act, RGPD, ISO 27001/42001/27701, uma norma harmonizada e nove rascunhos prEN; as datas de verificação envelhecem e ninguém repara quando um rascunho vira norma.
**Solução:** um catálogo de 98 requisitos filtrado por um perfil, mantido vivo por agentes que vigiam as fontes e propõem; uma pessoa aprova; o código impede os agentes de decidir o que é da pessoa.
**Valor:** horas de verificação manual por semana convertidas em minutos de decisão, com registo de auditoria.

## Antes da aula (5 min) — sem terminal
1. Duplo clique em `start_demo.cmd` na pasta do projeto. Abre a consola em http://localhost:8765 (fica uma janela preta aberta; ignora-a).
2. Põe dois ou três documentos em `data\evidence\` com o ID da linha no início do nome (`R-04.01_registo_formacao.pdf`, `R-GDPR.05_acordo_tratamento_fornecedor.pdf`).
3. Deixa aberto num separador o Excel de base `AI_Governance_Risk_Matrix_v1.2.xlsx`.
4. Opcional, para plano B: corre uma ronda até ao gate 1 e deixa-a parada; a consola mostra as propostas sem precisar de rede.

A consola tem quatro páginas: **Ronda** (correr, decidir nos gates, ver o progresso), **Importar matriz** (carregar a matriz da organização em Excel/CSV, mapear colunas, repor a base), **Versões Excel** (uma por ronda aprovada, com download, com a coluna derivada "Improvement opportunity") e **Estado** (a síntese com fontes, rondas e registo de auditoria).

## 1. O problema (1 min) — Excel, folha "Sources"
Mostra a coluna *Verified on*. Pergunta: quem confirma estas 32 datas todas as semanas? E quem repara quando uma prEN passa a norma harmonizada?

## 2. A matriz (2 min) — Excel, folhas "Profile" e "Matrix"
- Muda uma resposta no Perfil (por exemplo *high_risk* de "To be determined" para "Yes") e mostra a coluna M a recalcular.
- Mostra a coluna *Source status* com as cores: final, adiado, harmonizada, rascunho. É a coluna mais importante.
- Mostra as colunas amarelas: só pessoas as preenchem.

## 3. O agente a trabalhar (3 min) — PowerShell
```powershell
.\.venv\Scripts\python.exe try_one.py
```
Enquanto corre, narra: pesquisa → tenta abrir o EUR-Lex → é bloqueado → não finge → baixa a confiança para "medium" → devolve JSON validado.
Pontos a dizer: lista de domínios oficiais; conteúdo descarregado tratado como dados, não instruções; saída validada por esquema.

**Plano B** (sem rede ou sem créditos): abre `demo\index.html`, secção "Rondas", e lê o relatório da última ronda. Diz que foi gerado por este mesmo processo.

## 4. A ronda e o gate, na consola (4 min)
Na página **Ronda**, "Correr uma ronda". A barra de passos avança sozinha (vigiar fontes → gate 1 → auditar → relatório → gate 2). Quando parar no gate 1, as propostas aparecem com a confiança a cores e as fracas desmarcadas. Aprova só as que têm evidência primária e "Gravar decisão e continuar": a ronda retoma sem repetir pesquisas. No gate 2, "Aprovar, gravar e exportar o Excel". Vai a **Versões Excel** e descarrega a versão nova: é a matriz atualizada, numerada e datada.
Se o tempo apertar: usa a ronda que deixaste parada no gate 1 antes da aula.

Depois, página **Estado** da consola:
- **Fontes vigiadas**: notas de S11 (prEN 18228) e S09 (prEN 18229-1). O agente afirmou "rejeitada" com base em fontes secundárias; a pessoa não aprovou; a nota regista a dúvida. É para isto que o gate existe.
- **Registo de auditoria**: cada escrita tem ator (`human:gate_sources`) e base (URL).
- Caixa laranja: o que os agentes nunca escrevem, imposto em código.

## 4b. Importar a matriz do cliente (2 min, opcional)
Página **Importar matriz**: carrega um Excel com colunas em português (Ref, Tema, Requisito, Base legal, Controlo, Evidência, Responsável, Estado). A consola deteta o cabeçalho e propõe o mapeamento sozinha; confirma e importa. A partir daí as rondas correm sobre a matriz do cliente, com as mesmas fontes. "Repor a matriz de base" volta ao catálogo. Frase: "o catálogo é do cliente; as fontes e as regras são da plataforma."

## 5. O relatório (1 min) — demo\index.html, "Última ronda"
Lê a frase "26 rows could not be checked". O sistema admite o que não sabe. Compara com o primeiro relatório (está em "Rondas"), que dizia "all evidence appears current": foi corrigido porque uma pessoa reparou.

## 6. Fecho (1 min)
Três frases:
1. O ficheiro JSON é a verdade; o Excel é a vista; o relatório é a comunicação.
2. Agentes propõem; pessoas aprovam; o código impede o resto.
3. O próprio agente é um sistema de IA e está na matriz (RK-G.B, RK-G.C, RK-12.A).

## Perguntas prováveis
- **"Isto garante conformidade?"** Não. Garante que as fontes estão verificadas e que as mudanças chegam a uma pessoa. A conformidade são as colunas amarelas.
- **"Porque não correr todos os dias?"** As fontes mudam raramente; um gate diário que diz "nada mudou" deixa de ser lido. Semanal, com aviso imediato só quando há proposta.
- **"E se o agente inventar?"** Aconteceu duas vezes hoje (S09, S11). O gate apanhou. A regra do código obriga a confiança "low" quando só há fontes secundárias.
- **"Quanto custa?"** Cêntimos por ronda no modelo; 50 a 70 pesquisas no Serper (2.500 grátis/mês).
- **"Os dados saem da organização?"** Só os prompts para o modelo e as pesquisas. Telemetria do CrewAI desligada. O auditor de evidência só lê nomes e datas de ficheiros, nunca o conteúdo.
- **"Porque é que a evidência é uma pasta?"** É o backend local, para demonstrar sem ligar ao SharePoint. A interface é a mesma; muda-se o backend, não o agente.
