# Arquitetura e princípios

## Fluxo
```
load_state ─► check_sources ─► [gate 1: pessoa] ─► audit_evidence ─► write_report ─► [gate 2: pessoa] ─► persist
   Python      agente ×N           aprova/rejeita       agente ×N          agente            aprova/descarta
```
| Passo | Quem | O quê |
|---|---|---|
| load_state | Python | Recalcula a aplicabilidade a partir do Perfil; escolhe as fontes voláteis (prEN, orientações, textos adiados) |
| check_sources | Vigilante de fontes (um por fonte, em paralelo) | Pesquisa em fontes primárias; devolve `SourceCheck` validado |
| gate 1 | Pessoa | Deduplicação em código (fase já registada = reconfirmação silenciosa); aprova por ID; grava estado, fase, nota, data e URL de evidência |
| audit_evidence | Auditor de evidência (um por linha) | Reporta encontrada / em falta / desatualizada / desconhecida; nunca julga suficiência |
| write_report | Relator | Prosa, < 200 palavras; obrigado a dizer quantas verificações não foram feitas |
| gate 2 | Pessoa | Aprova o relatório; só então a ronda é gravada |

## Ficheiros
- `data/matrix.json` — catálogo (98 linhas). `data/profile.json` — respostas que filtram. `data/sources.json` — fontes com estado, fase, data e nota.
- `data/history.json` — registo imutável: `ts`, `id`, `field`, `old`, `new`, `actor`, `basis`.
- `data/reports.json` — um relatório por ronda.
- `demo/index.html` — vista gerada por `scripts/build_demo.py`.

## Regras impostas em código (não por prompt)
1. Campos só-humanos: `required_risk_class`, `applicability`, `implementation_status`, `implemented_control`, `owner` (`store.py`).
2. Domínios permitidos para descarregar texto: EU, CEN-CENELEC, ISO, organismos nacionais de normalização (`tools.py`).
3. Conteúdo descarregado é marcado como dados, nunca instruções (prompt injection).
4. Saída de agente que não valida o esquema vai para revisão manual.
5. Proposta igual ao que está gravado (estado + fase) não aparece no gate; só atualiza a data.
6. Evidência mais antiga do que a última verificação baixa a confiança para "medium".
7. Agentes nunca correm em paralelo com a mesma instância (`make_source_watcher()`).
8. Telemetria do CrewAI desligada (`CREWAI_TRACING_ENABLED=false`).

## Porquê Flow e não Crew
Agentes herdam saídas uns dos outros sem validação. O Flow dá a cada agente uma fonte ou uma linha de cada vez, valida cada saída e mete uma pessoa entre a proposta e a escrita.

## O que aprendemos nas quatro primeiras rondas (22 out 2026)
- O relator afirmou "evidência em ordem" quando nada tinha sido verificado → passou a receber a contagem de "unknown" e a regra de não afirmar.
- O vigilante reportou "rejeitada" (S09, S11) com base em fontes secundárias → regra: URL de evidência tem de suportar o facto; só secundárias = confiança "low".
- S09 e S20 voltaram a aparecer como mudança → deduplicação por fase, em código.
- EUR-Lex bloqueia scrapers (HTTP 202) → próximo passo: Cellar (publications.europa.eu).

## Pendentes
`scripts/manual_edit.py` (edições manuais com registo) · `find_evidence` ligado ao Microsoft 365 · Cellar para o EUR-Lex · atualizar a folha "Sources" do Excel com as fases encontradas.
