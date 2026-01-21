"""Módulo que contém todas as funções/classes para criar
a lista de questões a partir do banco de dados."""

import os
import re
import sqlite3
from typing import Dict, List
from pathlib import Path
from src.modelos import Questao
from src.database import limpar_para_latex

def buscar_questoes_por_tema(nome_do_banco: str, tema: str):
    """
    Busca todas as questões que contenham o tema especificado.
    """
    # 1. Localiza a raiz do projeto de forma absoluta
    raiz_projeto = Path(__file__).resolve().parent.parent
    caminho_db = raiz_projeto / "data" / "database" / f"{nome_do_banco}.db"

    # 2. Verifica se o banco realmente existe antes de tentar abrir
    if not caminho_db.exists():
        print(f"❌ Erro: O arquivo do banco não foi encontrado em: {caminho_db}")
        return []

    questoes_encontradas = []

    try:
        # É necessário converter o Path para string no sqlite3.connect
        with sqlite3.connect(str(caminho_db)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 3. Busca usando LIKE para encontrar o tema dentro da string de temas
            query = "SELECT * FROM questoes WHERE temas LIKE ?"
            cursor.execute(query, (f"%{tema}%",))
            
            rows = cursor.fetchall()
            
            for row in rows:
                lista_temas = row["temas"].split(", ") if row["temas"] else []
                q = Questao(
                    texto=row["texto"],
                    serie=row["serie"],
                    origem=row["origem"],
                    dificuldade=row["dificuldade"],
                    imagem_path=row["imagem"],
                    temas=lista_temas
                )
                questoes_encontradas.append(q)
        
        return questoes_encontradas

    except sqlite3.OperationalError as e:
        print(f"❌ Erro operacional no SQLite (verifique permissões): {e}")
        return []


def gerar_lista_exercicios_latex(nome_do_banco: str, tema: str, nome_arquivo: str):
    """
    Gera um arquivo .tex em duas colunas na pasta 'outputs'.
    """
    # 1. Obter as questões
    # Note: inverti a ordem para bater com a assinatura da sua função de busca
    questoes = buscar_questoes_por_tema(nome_do_banco, tema)

    if not questoes:
        print(f"⚠️ Nenhuma questão encontrada para o tema '{tema}'.")
        return

    # 2. Configurar caminhos com Pathlib
    raiz_projeto = Path(__file__).resolve().parent.parent
    pasta_output = raiz_projeto / "outputs"
    pasta_output.mkdir(parents=True, exist_ok=True)
    caminho_final = pasta_output / f"{nome_arquivo}.tex"

    # 3. Montar o conteúdo LaTeX
    conteudo_latex = []

    # 3.1. Cabeçalho com Duas Colunas e Margens de 2cm
    conteudo_latex.append(r"\documentclass[twocolumn]{article}")
    conteudo_latex.append(r"\usepackage[utf8]{inputenc}")
    conteudo_latex.append(r"\usepackage[T1]{fontenc}")
    conteudo_latex.append(r"\usepackage{amsmath, amssymb}")
    conteudo_latex.append(r"\usepackage{graphicx}")
    conteudo_latex.append(r"\usepackage[portuguese]{babel}")
    conteudo_latex.append(r"\usepackage{siunitx}")     # Para \num e \unit
    conteudo_latex.append(r"\usepackage{textgreek}")   # Para letras gregas no texto
    conteudo_latex.append(r"\sisetup{output-decimal-marker = {,}}") # Usa vírgula decimal
    # Define margens de 2cm
    conteudo_latex.append(r"\usepackage[margin=2cm]{geometry}")
    
    conteudo_latex.append(r"\title{Lista de Exercícios: " + tema + "}")
    conteudo_latex.append(r"\author{Banco de Questões}")
    conteudo_latex.append(r"\date{\today}")
    
    conteudo_latex.append(r"\begin{document}")
    conteudo_latex.append(r"\maketitle")
    conteudo_latex.append(r"\section*{Questões}")

    # 3.2. Adicionar as Questões
    for i, q in enumerate(questoes, 1):
        # Adiciona o título da questão formatado
        conteudo_latex.append(rf"\subsubsection*{{Questão {i}}}")

        # Limpeza de caracteres especiais
        texto_final = limpar_para_latex(q.texto)

        # 2. Aplicamos a separação de alternativas
        # Usamos uma versão simplificada do regex diretamente aqui
        padrao_alt = r"\b([A-Ea-e][\.\)])"
        partes = re.split(padrao_alt, texto_final)

        if len(partes) > 1:
            # Adiciona o enunciado primeiro
            conteudo_latex.append(partes[0].strip() + r"\\[5pt]") # Adiciona um pequeno espaço após enunciado
            
            # Reconstrói as alternativas uma em cada linha
            lista_linhas = []
            for j in range(1, len(partes), 2):
                marcador = partes[j].strip()      # Ex: "a)"
                texto_alt = partes[j+1].strip()   # Ex: "40 m/s"
                # Formata como: a) 40 m/s \\
                lista_linhas.append(rf"{marcador} {texto_alt} \\")
            
            # Junta todas as alternativas e adiciona ao conteúdo
            conteudo_latex.append("\n".join(lista_linhas))
        else:
            # Se não encontrar alternativas, coloca o texto original
            conteudo_latex.append(texto_final)

        # 3.3. Adicionar Imagem (ajustada para largura da coluna)
        if q.imagem_path and str(q.imagem_path).lower() != "none":
            conteudo_latex.append(r"\begin{figure}[h!]")
            conteudo_latex.append(r"    \centering")
            # width=\linewidth garante que a imagem caiba na coluna
            conteudo_latex.append(
                r"    \includegraphics[width=\linewidth]{" + str(q.imagem_path) + r"}"
            )
            conteudo_latex.append(r"    \caption*{}") # Caption sem número
            conteudo_latex.append(r"\end{figure}")

    conteudo_latex.append(r"\end{document}")

    # 4. Geração do Arquivo
    conteudo_final = "\n".join(conteudo_latex)

    with open(caminho_final, "w", encoding="utf-8") as f:
        f.write(conteudo_final)

    print(f"\n✅ Arquivo gerado em: {caminho_final}")
    print(f"Total: {len(questoes)} questões. Layout: 2 colunas, Margens: 2cm.")
