# Pitch de 2 minutos (alinhado com a grelha CRE)

**Valor (30%).** Quem governa IA numa organização tem uma matriz com dezenas de requisitos e de fontes: AI Act, RGPD, normas ISO, uma norma harmonizada, nove rascunhos europeus. Cada fonte tem uma data de verificação que envelhece. Hoje ninguém as confirma; descobre-se tarde que um rascunho virou norma ou que uma orientação foi adotada. Esta solução transforma horas de verificação manual em minutos de decisão, com registo de auditoria de quem aprovou o quê e com base em quê.

**Adequação (20%).** O desafio era [enunciado da Academia]. Respondi com um Flow do CrewAI, não com um chat: agentes com uma tarefa cada, saídas validadas por esquema, dois gates humanos e regras impostas em código. Escolhi Flow em vez de Crew porque agentes que herdam as saídas uns dos outros propagam erros; aqui cada agente recebe uma fonte ou uma linha de cada vez.

**Funcionalidade (15%).** Corre de ponta a ponta no meu portátil: quatro rondas hoje, 32 fontes verificadas, oito fases de normas descobertas, duas datas formais de orientações corrigidas. Em duas delas o agente afirmou mais do que a evidência; o gate apanhou. A auditoria de evidência lê uma pasta local e diz "encontrada, modificada em…" ou "em falta", nunca inventa.

**Utilização (10%).** O responsável decide num browser: propostas com a confiança a cores, as fracas desmarcadas por omissão, dois botões. O resto é uma página de estado que se gera a partir dos dados.

**Inovação (10%).** O que distingue isto de um script com um LLM: deduplicação em código, confiança rebaixada quando só há fontes secundárias, campos que os agentes não podem escrever, e o próprio sistema registado na matriz como sistema de IA.

**Viabilidade (10%).** Cêntimos por ronda, 2.500 pesquisas gratuitas por mês, Docker pronto, cron semanal. O mesmo ficheiro serve outra organização mudando quinze respostas de perfil.

**Fecho.** O JSON é a verdade, o Excel é a vista, o relatório é a comunicação. Agentes propõem, pessoas aprovam, o código impede o resto.
