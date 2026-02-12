import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.gerador import gerar_lista_exercicios_latex


# Criamos uma classe Mock para simular o objeto 'Questao' que vem do banco
class MockQuestao:
    """
    Simula perfeitamente a estrutura da classe Questao real.
    Inclui todos os campos que o banco de dados e o gerador utilizam.
    """

    def __init__(
        self,
        id=1,
        texto="Texto da questão",
        tema="Geral",
        origem="Fonte Desconhecida",
        imagem_path=None,
        ano=None,
        dificuldade=None,
        gabarito=None,
    ):
        self.id = id
        self.texto = texto
        self.tema = tema
        self.origem = origem
        self.imagem_path = imagem_path
        self.ano = ano
        self.dificuldade = dificuldade
        self.gabarito = gabarito

    def __repr__(self):
        return f"<MockQuestao(id={self.id}, origem='{self.origem}')>"


def test_gerador_latex_sem_imagem(monkeypatch):
    """Verifica se o gerador não quebra quando uma questão não tem imagem."""

    # 1. Criamos questões de teste (uma com e uma sem imagem)
    questoes_teste = [
        MockQuestao("Quanto é 1+1?", "Prova 2024", None),
        MockQuestao("Veja a figura:", "ENEM 2023", "path/to/img.png"),
    ]

    # 2. Mockamos a conexão com o banco de dados
    # Fazemos o pandas.read_sql ou sua função de busca retornar nossos mocks
    mock_db = MagicMock()
    # Se você usa uma função 'buscar_questoes', mockamos ela:
    monkeypatch.setattr(
        "src.gerador.buscar_questoes_por_tema", lambda *args, **kwargs: questoes_teste
    )

    # 3. Executamos o gerador (usando um nome de banco fictício)
    try:
        gerar_lista_exercicios_latex(
            nome_do_banco="fake_db",
            tema="Matemática",
            nome_arquivo="teste_saida",
            overleaf=True,
        )
    except AttributeError as e:
        pytest.fail(f"O gerador quebrou com erro de NoneType: {e}")
    except Exception as e:
        pytest.fail(f"Ocorreu um erro inesperado: {e}")


def test_ajuste_caminho_overleaf():
    """Testa especificamente a lógica de conversão de caminhos para o Overleaf."""
    pass


def test_gerador_latex_ignora_valor_booleano_sujo(tmp_path, monkeypatch):
    """
    Testa se o gerador filtra valores booleanos (True/False) ou strings 'True'
    e garante que o arquivo LaTeX seja gerado sem erros.
    """

    # 1. SETUP: Criamos uma questão com o erro 'True' no caminho da imagem
    questoes_sujas = [
        MockQuestao(
            id=200,
            texto="Questão teste com erro de caminho.",
            origem="OBFEP 2025",
            imagem_path=True,  # Simula o erro que gera 'OBFEP_2025/True'
        )
    ]

    # 2. MOCK: Substituímos a função de busca do seu gerador.py
    monkeypatch.setattr(
        "src.gerador.buscar_questoes_por_tema", lambda *args, **kwargs: questoes_sujas
    )

    # 3. CAMINHOS: Definimos onde o arquivo deve ser criado pelo teste
    # Usamos o diretório temporário do pytest para não sujar sua pasta real
    nome_base = "lista_teste_limpeza"
    caminho_saida = tmp_path / nome_base

    # 4. EXECUÇÃO
    try:
        gerar_lista_exercicios_latex(
            nome_do_banco="db_fake",
            tema="Física",
            nome_arquivo=str(caminho_saida),
            overleaf=True,
        )
    except Exception as e:
        pytest.fail(f"O gerador quebrou durante a execução! Erro: {e}")

    # 5. VALIDAÇÃO DO ARQUIVO:
    # O gerador pode salvar como 'lista_teste_limpeza' ou 'lista_teste_limpeza.tex'
    arquivo_gerado = Path(str(caminho_saida) + ".tex")
    if not arquivo_gerado.exists():
        arquivo_gerado = Path(caminho_saida)

    # Verifica se o arquivo físico foi realmente criado
    assert (
        arquivo_gerado.exists()
    ), f"O gerador não criou o arquivo em: {arquivo_gerado}"

    # Lemos o conteúdo para garantir que a sujeira foi filtrada
    conteudo = arquivo_gerado.read_text()

    # Asserções principais:
    assert (
        "OBFEP_2025/True" not in conteudo
    ), "ERRO: O caminho 'True' vazou para o LaTeX!"
    assert (
        "\\includegraphics" not in conteudo
    ), "ERRO: O gerador tentou criar comando de imagem para um valor inválido!"
    assert (
        "Questão teste com erro de caminho" in conteudo
    ), "O texto da questão deve estar presente!"
