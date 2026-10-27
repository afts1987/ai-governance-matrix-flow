# A plataforma explicada em linguagem simples

## O que é a plataforma

Imagina uma tabela com 98 linhas. Cada linha é uma obrigação ou um risco que uma empresa que usa inteligência artificial tem de acompanhar: o que a lei europeia exige, o que a lei de proteção de dados exige, o que as normas de qualidade e segurança recomendam. Cada linha diz de onde vem a obrigação, se já está em vigor ou se foi adiada, o que a empresa deve fazer para a cumprir, que prova deve guardar, e quem é responsável.

O problema é que essa tabela envelhece. As normas europeias mudam de fase, os reguladores publicam orientações novas, as datas de aplicação são adiadas. Alguém teria de verificar, todas as semanas, dezenas de fontes para saber se a tabela ainda está certa. Ninguém o faz.

A plataforma faz essa verificação por nós, e depois pergunta-nos o que fazer com o que encontrou.

## O que fazem os agentes

Há três ajudantes automáticos, cada um com uma tarefa só.

O **vigilante** vai às fontes oficiais (o Jornal Oficial da União Europeia, os organismos de normalização, a Comissão, os reguladores portugueses) e verifica, uma a uma, se alguma coisa mudou desde a última vez. Quando encontra algo, escreve uma proposta: o que mudou, onde o viu, com que grau de certeza. Não pode ler sites que não sejam oficiais, e se só encontrou a notícia num blogue, tem de o dizer e marcar a proposta como pouco fiável.

O **auditor** confere se as provas que a empresa diz ter existem mesmo. Vai à pasta onde a empresa guarda os documentos e diz, para cada obrigação, "a prova está lá, com esta data", "não está" ou "não consegui verificar". Não julga se a prova é boa; só se existe.

O **relator** escreve um resumo curto da ronda, em linguagem normal, para quem decide. Está proibido de dizer que está tudo bem quando há coisas por verificar.

Nenhum dos três decide nada. Propõem.

## O que faz a pessoa

A pessoa aparece em dois momentos, e só ela pode avançar.

No primeiro momento, vê as propostas do vigilante no ecrã, cada uma com a fonte e o grau de certeza. Aprova as que têm prova sólida e rejeita as outras. Nada muda na tabela sem esse clique.

No segundo momento, lê o resumo do relator e aprova-o. Só então a ronda fica gravada e sai uma versão nova da tabela em Excel, numerada e datada.

Entre as rondas, a pessoa trabalha na própria tabela, em Excel, como sempre fez: preenche o que a empresa já implementou, quem é o responsável, quando se revê. Depois carrega esse Excel na plataforma e ela absorve essas alterações. Tudo o que a pessoa decide ou altera fica num registo que diz quem fez o quê, quando e com base em quê.

Há coisas que só a pessoa pode escrever e que os ajudantes nunca tocam: se um sistema é de alto risco, se uma obrigação se aplica, se um controlo está implementado, quem é o responsável. Isso não é uma regra de boa educação; é uma barreira construída no programa.

## Com que foi construída

A plataforma foi feita em Python, a linguagem mais comum para trabalhar com inteligência artificial. Para organizar os três ajudantes e os dois pontos de decisão usei o CrewAI, uma biblioteca gratuita e de código aberto que serve exatamente para isso: definir quem faz o quê, por que ordem, e onde o fluxo tem de parar à espera de uma pessoa.

Os ajudantes pensam com o Claude, um modelo de linguagem da Anthropic, ao qual a plataforma liga pela internet. Para procurar as fontes usam um serviço de pesquisa do Google, e para ler as páginas oficiais e os documentos em PDF usam ferramentas simples de leitura, limitadas a uma lista de sítios de confiança.

Tudo o que um ajudante escreve passa por um verificador de formato antes de ser aceite: se a resposta não tiver os campos certos, não entra e vai para revisão manual. É uma das formas de impedir que um ajudante invente.

A informação vive em ficheiros de texto estruturados, simples de ler e de guardar, que são a fonte de verdade. O Excel é gerado a partir deles, com uma biblioteca que escreve folhas de cálculo, e pode ser lido de volta quando a pessoa o preenche.

A página que se vê no navegador foi feita só com as ferramentas que o Python já traz, sem programas adicionais, para correr num portátil de empresa com as restrições habituais. Abre-se com um duplo clique.

Há ainda testes automáticos que confirmam, de cada vez que o programa muda, que a regra mais importante continua a valer: os ajudantes não conseguem escrever nos campos que são das pessoas. E a plataforma está preparada para correr num servidor, em contentor, com uma ronda agendada por semana, embora essa parte ainda não tenha sido testada.

Em resumo: Python e CrewAI para os ajudantes, o Claude para pensar, um verificador de formato para cada resposta, ficheiros de texto como verdade e o Excel como vista.

## Como pôr a plataforma a funcionar

1. Abre-se a plataforma com um duplo clique num ficheiro. Aparece uma página no navegador, com cinco separadores.
2. No separador "Ronda", carrega-se em "Correr uma ronda". Durante uns minutos, uma barra mostra em que passo vai.
3. Quando a barra para no primeiro ponto de decisão, a página mostra as propostas. Lê-se, marcam-se as que têm prova, carrega-se em "Gravar decisão e continuar".
4. A barra avança sozinha pela verificação das provas e pelo resumo, e para no segundo ponto de decisão. Lê-se o resumo e carrega-se em "Aprovar, gravar e exportar o Excel".
5. No separador "Versões Excel" aparece a tabela nova, pronta a descarregar.
6. Durante o mês, trabalha-se nesse Excel. Antes da ronda seguinte, carrega-se o ficheiro no separador "Importar matriz" para a plataforma ler o que a empresa fez.
7. Repete-se uma vez por mês. Na maior parte dos meses, a ronda traz uma ou duas propostas, ou nenhuma. Isso é o funcionamento normal: significa que as fontes foram verificadas e nada mudou.

Os outros separadores servem para consultar: "Estado" mostra uma síntese do que está vigiado e decidido, e "Glossário" explica as siglas.

## O que a plataforma não faz

Não diz se a empresa cumpre a lei. Diz se a tabela que a empresa usa para o saber está atualizada, e deixa a prova de quem decidiu o quê. A conformidade continua a ser trabalho de pessoas; a plataforma garante que elas trabalham com informação verificada e que as decisões ficam registadas.
