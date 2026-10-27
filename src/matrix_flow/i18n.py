"""Portuguese labels for the exported workbook. Data stays in English in the JSON store; translation happens at export,
and the Excel sync maps Portuguese values back. Free text of the 98 rows is not translated here."""
SHEETS = {"Read me": "Leia-me", "Profile": "Perfil", "Matrix": "Matriz", "Sources": "Fontes", "Rounds": "Rondas",
          "History": "Histórico", "Glossary": "Glossário"}
HEADERS = {
 "ID": "ID", "Theme": "Tema", "Row type": "Tipo de linha", "Nature": "Natureza", "Requirement / risk": "Requisito / risco",
 "AI Act basis": "Base no AI Act", "Source status (AI Act)": "Estado da fonte (AI Act)", "Application date": "Data de aplicação",
 "Required role": "Papel exigido", "Required risk class": "Classe de risco exigida", "Additional condition": "Condição adicional",
 "Sector": "Setor", "Applicability": "Aplicabilidade", "GDPR": "RGPD",
 "ISO/IEC 27001:2022 Annex A": "ISO/IEC 27001:2022 Anexo A", "ISO/IEC 42001:2023 Annex A": "ISO/IEC 42001:2023 Anexo A",
 "ISO/IEC 27701:2025 Annex A": "ISO/IEC 27701:2025 Anexo A", "European / other standards": "Normas europeias / outras",
 "Standard status": "Estado da norma", "Guidance": "Orientações", "Proposed control": "Controlo proposto",
 "Proportionate variant (SME)": "Variante proporcional (PME)", "Expected evidence": "Evidência esperada",
 "Implemented control": "Controlo implementado", "Owner": "Responsável", "Implementation status": "Estado de implementação",
 "Review date": "Data de revisão", "Improvement opportunity (derived)": "Oportunidade de melhoria (derivada)",
 "Sources": "Fontes", "Verified on": "Verificado em", "To confirm": "A confirmar", "Notes": "Notas",
 "Key": "Chave", "Answer": "Resposta", "Source": "Fonte", "Type": "Tipo", "Status": "Estado", "Stage": "Fase",
 "Reference": "Referência", "How it was verified": "Como foi verificado",
 "Note (agent finding, approved by a person)": "Nota (achado do agente, aprovado por uma pessoa)",
 "Round": "Ronda", "Evidence not checked": "Evidência por verificar", "Evidence missing": "Evidência em falta",
 "Sources changed": "Fontes alteradas", "Summary": "Resumo", "When (UTC)": "Quando (UTC)", "Entity": "Entidade",
 "Field": "Campo", "Before": "Antes", "After": "Depois", "Actor": "Ator", "Basis": "Base",
 "Secção": "Secção", "Sigla / termo": "Sigla / termo", "Significado": "Significado",
}
VALUES = {
 # source status
 "Final text — in force": "Texto final em vigor", "Final text — deferred application": "Texto final — aplicação diferida",
 "Harmonised standard cited in the OJ": "Norma harmonizada citada no JO", "Published standard (not harmonised)": "Norma publicada (não harmonizada)",
 "Draft (prEN)": "Rascunho (prEN)", "Non-binding guidance": "Orientação não vinculativa", "Internal proposal (to validate)": "Proposta interna (a validar)",
 # applicability
 "Applicable": "Aplicável", "Depends": "Depende", "Not applicable": "Não aplicável",
 # row type / nature
 "Legal requirement": "Requisito legal", "Optional legal basis": "Base jurídica facultativa", "Derived good practice": "Boa prática derivada", "Risk": "Risco",
 "Legal obligation": "Exigência legal", "Legal permission (optional)": "Permissão legal (facultativa)", "Standard recommendation": "Recomendação de norma", "Internal decision": "Decisão interna",
 # role / class / sector
 "Provider": "Prestador", "Deployer": "Responsável pela implantação", "Both": "Ambos", "Any": "Qualquer",
 "High-risk": "Alto risco", "High-risk (Annex III)": "Alto risco (anexo III)", "High-risk (Annex I)": "Alto risco (anexo I)",
 "All": "Todos", "Financial": "Financeiro", "Health": "Saúde", "Telecommunications": "Telecomunicações",
 "Legal and professional services": "Jurídico e serviços profissionais", "Public sector": "Setor público",
 # implementation status
 "Not started": "Não iniciado", "In progress": "Em curso", "Implemented": "Implementado", "Risk accepted": "Risco aceite",
 # profile answers
 "Yes": "Sim", "No": "Não", "To be determined": "A determinar", "Annex III": "Anexo III", "Annex I": "Anexo I", "None": "Nenhum",
 # standard status
 "Draft (prEN) / published standard": "Rascunho (prEN) / norma publicada", "Draft (prEN) / harmonised standard cited in the OJ": "Rascunho (prEN) / norma harmonizada citada no JO",
 "Draft (prEN) / final text": "Rascunho (prEN) / texto final",
}
VALUES_BACK = {v: k for k, v in VALUES.items()}

def h(label: str, lang: str) -> str:
    return HEADERS.get(label, label) if lang == "pt" else label

def v(value, lang: str):
    return VALUES.get(value, value) if (lang == "pt" and isinstance(value, str)) else value

def sheet(name: str, lang: str) -> str:
    return SHEETS.get(name, name) if lang == "pt" else name
