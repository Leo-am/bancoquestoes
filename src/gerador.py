"""Módulo que contém todas as funções/classes para criar
a lista de questões a partir do banco de dados."""

import sqlite3
from typing import Dict, List


def buscar_questoes_por_tema(nome_do_banco: str, tema_alvo: str) -> List[Dict]:
    """
    Busca questões onde o campo 'temas' contém o tema alvo, retornando uma lista de dicionários.
    """
    db_file = f"{nome_do_banco}.db"

    try:
        with sqlite3.connect(db_file) as conn:
            conn.row_factory = sqlite3.Row  # Retorna resultados como dicionários
            cursor = conn.cursor()

            # O operador LIKE com % garante que a busca encontre a string em qualquer parte.
            # Ex: Busca "Calorimetria" dentro de "Física, Termodinâmica, Calorimetria"
            sql_query = "SELECT * FROM questoes WHERE temas LIKE ?"

            # O padrão de busca com curingas (%)
            search_pattern = f"%{tema_alvo}%"

            cursor.execute(sql_query, (search_pattern,))

            registros = [dict(row) for row in cursor.fetchall()]
            return registros

    except sqlite3.Error as e:
        print(f"❌ Erro ao buscar questões por tema: {e}")
        return []


def gerar_lista_exercicios_latex(nome_do_banco: str, tema: str, nome_arquivo: str):
    """
    Gera um arquivo .tex contendo uma lista de exercícios sobre o tema especificado.
    """
    # 1. Obter as questões
    questoes = buscar_questoes_por_tema(nome_do_banco, tema)

    if not questoes:
        print(
            f"⚠️ Nenhuma questão encontrada para o tema '{tema}'. Arquivo LaTeX não gerado."
        )
        return

    # 2. Montar o conteúdo LaTeX
    conteudo_latex = []

    # 2.1. Cabeçalho do Documento
    conteudo_latex.append(r"\documentclass{article}")
    conteudo_latex.append(r"\usepackage[utf8]{inputenc}")
    conteudo_latex.append(r"\usepackage{amsmath}")  # Útil para fórmulas
    conteudo_latex.append(r"\usepackage{graphicx}")  # Para incluir imagens (se houver)
    conteudo_latex.append(r"\geometry{margin=1in}")  # Margens ajustadas
    conteudo_latex.append(r"\title{Lista de Exercícios - " + tema + "}")
    conteudo_latex.append(r"\author{Banco de Questões}")
    conteudo_latex.append(r"\date{\today}")
    conteudo_latex.append(r"\begin{document}")
    conteudo_latex.append(r"\maketitle")

    conteudo_latex.append(r"\section*{Questões de " + tema + r"}")
    conteudo_latex.append(r"\begin{enumerate}")

    # 2.2. Adicionar as Questões
    for q in questoes:
        # \item inicia um novo item na lista enumerada (nova questão)
        conteudo_latex.append(r"\item")

        # O texto da questão pode ter caracteres especiais do LaTeX (como %, $, _).
        # É crucial escapá-los ou usar um pacote como 'verbatim' para texto cru.
        # Aqui, vamos fazer uma substituição simples e crucial:
        texto_limpo = q["texto"].replace(
            "\\", r"\textbackslash{}"
        )  # Escapa barras invertidas
        texto_limpo = texto_limpo.replace("&", r"\&")
        texto_limpo = texto_limpo.replace("%", r"\%")
        texto_limpo = texto_limpo.replace("_", r"\_")
        texto_limpo = texto_limpo.replace(
            "$", r"\$"
        )  # Se houver $, o LaTeX espera modo matemático

        conteudo_latex.append(texto_limpo)

        # 2.3. Adicionar Imagem (se existir)
        if q["imagem"] and q["imagem"] != "None":
            # Nota: O LaTeX precisará da imagem no mesmo diretório ou em um caminho conhecido.
            conteudo_latex.append(r"\begin{figure}[h]")
            conteudo_latex.append(r"    \centering")
            # Ajuste o caminho da imagem e a largura conforme necessário
            conteudo_latex.append(
                r"    \includegraphics[width=0.8\textwidth]{" + q["imagem"] + r"}"
            )
            conteudo_latex.append(
                r"    \caption{Imagem auxiliar da Questão ID " + str(q["id"]) + r"}"
            )
            conteudo_latex.append(r"\end{figure}")

        conteudo_latex.append(r"")  # Linha vazia para separação

    # 2.4. Rodapé do Documento
    conteudo_latex.append(r"\end{enumerate}")
    conteudo_latex.append(r"\end{document}")

    # 3. Geração do Arquivo
    conteudo_final = "\n".join(conteudo_latex)

    with open(f"{nome_arquivo}.tex", "w", encoding="utf-8") as f:
        f.write(conteudo_final)

    print(f"\n✅ Arquivo LaTeX '{nome_arquivo}.tex' gerado com sucesso!")
    print(f"Total de {len(questoes)} questões de '{tema}' incluídas.")
    print("Para gerar o PDF, execute no terminal: pdflatex " + nome_arquivo + ".tex")
