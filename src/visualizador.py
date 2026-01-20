"""Módulo que contém todas as funções para visualizar
o banco de dados de questões."""

import sqlite3
from pathlib import Path

import pandas as pd

from src.modelos import Questao


def buscar_todas_questoes(nome_do_banco: str) -> pd.DataFrame:
    db_file = f"{nome_do_banco}.db"
    try:
        # Pandas pode ler SQL diretamente, retornando um DataFrame
        conn = sqlite3.connect(db_file)
        df = pd.read_sql_query("SELECT * FROM questoes", conn)
        conn.close()
        return df
    except Exception as e:
        print(f"❌ Erro ao ler o banco com Pandas: {e}")
        return pd.DataFrame()


def buscar_questao_por_id(id_questao: int, nome_do_banco: str):
    """
    Busca uma questão pelo ID e retorna uma instância da classe Questao.
    """
    # 1. Localiza o caminho absoluto do banco de dados
    raiz_projeto = Path(__file__).resolve().parent.parent
    caminho_db = raiz_projeto / "data" / "database" / f"{nome_do_banco}.db"

    if not caminho_db.exists():
        print(f"❌ Erro: Banco de dados não encontrado em {caminho_db}")
        return None

    try:
        with sqlite3.connect(str(caminho_db)) as conn:
            # Configura o row_factory para acessar as colunas pelo nome
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM questoes WHERE id = ?", (id_questao,))
            row = cursor.fetchone()

            if row:
                # 2. Converte a string de temas do banco de volta para uma lista
                lista_temas = row["temas"].split(", ") if row["temas"] else []

                # 3. Retorna o objeto Questao montado
                return Questao(
                    texto=row["texto"],
                    serie=row["serie"],
                    origem=row["origem"],
                    dificuldade=row["dificuldade"],
                    imagem_path=row["imagem"],
                    temas=lista_temas,
                )

            print(f"⚠️ Questão com ID {id_questao} não encontrada.")
            return None

    except Exception as e:
        print(f"❌ Erro ao buscar questão: {e}")
        return None
