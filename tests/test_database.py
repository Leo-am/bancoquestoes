import os
import sqlite3
from typing import List, Optional

import pytest

from src.database import editar_questao_por_id
from src.modelos import Questao  # Ajuste o caminho conforme necessário


@pytest.fixture
def db_teste():
    """Configura um banco de dados temporário para os testes de integração."""
    nome_db = "teste_questoes"
    db_file = f"{nome_db}.db"

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    # Criando a tabela conforme a ordem do seu método to_tuple:
    # (texto, serie, origem, dificuldade, imagem_path, temas)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT,
            serie TEXT,
            origem TEXT,
            dificuldade TEXT,
            imagem_path TEXT,
            temas TEXT
        )
    """
    )
    # Inserindo uma questão inicial
    q_inicial = Questao(
        texto="Qual a velocidade da luz?",
        serie="3º Ano",
        origem="MEC",
        dificuldade="Fácil",
        temas=["Óptica", "Introdução"],
    )

    # Usamos o to_tuple() da sua classe
    cursor.execute(
        "INSERT INTO questoes (texto, serie, origem, dificuldade, imagem_path, temas) VALUES (?,?,?,?,?,?)",
        q_inicial.to_tuple(),
    )
    conn.commit()
    conn.close()

    yield nome_db

    if os.path.exists(db_file):
        os.remove(db_file)


def test_atualizar_temas_lista_para_string(db_teste):
    """
    Testa se a função de edição lida corretamente com a conversão
    de uma lista de temas para a string separada por vírgulas no banco.
    """
    id_alvo = 1
    novos_temas_lista = ["Cinemática", "Movimento Uniforme", "Física 1"]

    # Como o banco espera uma STRING, convertemos antes de enviar para a função de edição
    # Seguindo a lógica do seu método to_tuple()
    temas_formatados = ", ".join(novos_temas_lista)

    updates = {"temas": temas_formatados, "dificuldade": "Média"}

    # Executa a função
    sucesso = editar_questao_por_id(db_teste, id_alvo, updates)

    # Verificações
    assert sucesso is True

    conn = sqlite3.connect(f"{db_teste}.db")
    cursor = conn.cursor()
    cursor.execute("SELECT temas, dificuldade FROM questoes WHERE id = ?", (id_alvo,))
    resultado = cursor.fetchone()
    conn.close()

    # O que está no banco deve ser a string concatenada
    assert resultado[0] == "Cinemática, Movimento Uniforme, Física 1"
    assert resultado[1] == "Média"
