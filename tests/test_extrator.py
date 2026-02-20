from pathlib import Path
from unittest.mock import MagicMock, patch

import pdfplumber
import pytest
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

from src.extrator import auditar_integridade_questao, extrair_questoes_pdf


@pytest.fixture
def caminho_pdf(tmp_path):
    """Cria um caminho temporário para o PDF de teste que o pytest gerencia."""
    return tmp_path / "pdf_de_teste.pdf"


def test_criar_pdf_teste(caminho_pdf):
    c = canvas.Canvas(str(caminho_pdf))

    # --- Questão 1: Unidades e Notação Científica ---
    # Testamos se o 'dot' da notação científica confunde o regex B.1)
    text_q1 = "B.1) Determine a constante k = 8.99 × 10⁹ N·m²/C²."
    c.drawString(100, 800, text_q1)

    # --- Questão 2: Fórmulas Químicas (Subscritos Reais) ---
    # Aqui simulamos o H₂O onde o '2' está abaixo da linha, um desafio para OCR/Extratores
    txt = c.beginText(100, 750)
    txt.textOut("B.2) Reação de combustão do etileno: C")
    txt.setRise(-2)  # Baixa o texto (subscrito)
    txt.textOut("2")
    txt.setRise(0)  # Volta ao normal
    txt.textOut("H")
    txt.setRise(-2)
    txt.textOut("4")
    txt.setRise(0)
    txt.textOut(" + O")
    txt.setRise(-2)
    txt.textOut("2")
    c.drawText(txt)

    # --- Questão 3: Equações Matemáticas (Símbolos e Itálicos) ---
    # Usamos a fonte Symbol para letras gregas como Δ (Delta)
    c.setFont("Times-Italic", 12)
    c.drawString(100, 700, "B.3) Calcule o valor de ")
    c.setFont("Symbol", 12)
    c.drawString(220, 700, "D")  # 'D' na fonte Symbol é Delta (Δ)
    c.setFont("Times-Roman", 12)
    c.drawString(235, 700, "f = b² - 4ac.")

    # --- Questão 4: Figura e Texto ao Redor ---
    c.drawString(100, 650, "B.4) Observe o gráfico abaixo:")
    c.setDash(1, 2)  # Linha pontilhada
    c.line(100, 580, 200, 630)  # Simula um vetor ou linha de gráfico
    c.setDash([])
    c.rect(100, 550, 50, 50)  # Simula um bloco num plano inclinado

    # --- Questão 5: Frações e Unidades Compostas ---
    c.drawString(100, 500, "B.5) A velocidade média foi de 20 m/s⁻¹ em t = 5 s.")

    c.save()


# 1. Teste de Comportamento do Regex
def test_extract_questions_regex_logic():
    """
    Testa se a lógica de split funciona corretamente com o padrão B.1), B.2)
    Simulando o texto que viria do pdfplumber.
    """
    # Texto simulado que o pdfplumber extrairia
    texto_fake = "Cabeçalho B.1) Primeira questão aqui B.2) Segunda questão aqui"

    # Precisamos "mockar" (simular) o pdfplumber para não ler um arquivo real
    with patch("pdfplumber.open") as mock_pdf:
        # Configura o mock para retornar o texto_fake
        mock_page = MagicMock()
        mock_page.extract_text.return_value = texto_fake
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

        # Mockamos também a existência do arquivo para passar no check pdf_path.exists()
        with patch.object(Path, "exists", return_value=True):
            resultado = extrair_questoes_pdf("fake.pdf", base_char="B")

            assert len(resultado) == 2
            assert "Primeira questão aqui" in resultado[0]
            assert "Segunda questão aqui" in resultado[1]


# 2. Teste de Erro: Arquivo Não Encontrado
def test_extract_questions_file_not_found():
    """Verifica se a função lida corretamente com arquivos inexistentes."""
    # Garante que Path.exists retorna False
    with patch.object(Path, "exists", return_value=False):
        resultado = extrair_questoes_pdf("arquivo_fantasma.pdf")
        assert resultado == []


# 3. Teste de Limpeza (Edge Case)
def test_extract_questions_empty_content():
    """Verifica se retorna lista vazia caso o PDF não tenha o padrão de questões."""
    texto_sem_questoes = "Este PDF contém apenas texto informativo sem o padrão B.x)"

    with patch("pdfplumber.open") as mock_pdf:
        mock_page = MagicMock()
        mock_page.extract_text.return_value = texto_sem_questoes
        mock_pdf.return_value.__enter__.return_value.pages = [mock_page]

        with patch.object(Path, "exists", return_value=True):
            resultado = extrair_questoes_pdf("vazio.pdf", base_char="B")
            assert len(resultado) == 0


def test_auditoria_identifica_problemas_comuns():
    """Testa se a função de auditoria detecta os gatilhos de erro."""

    # Caso 1: Raiz quadrada sem chaves (padrão de erro de extração)
    texto_raiz = "Calcule o valor de \sqrt 1-v^2/c^2 ."
    alertas_raiz = auditar_integridade_questao(texto_raiz)
    assert any("Raiz quadrada" in a for a in alertas_raiz)

    # Caso 2: Caractere PUA (Fantasma do PDF)
    texto_pua = "O valor de \uf06d é 10."
    alertas_pua = auditar_integridade_questao(texto_pua)
    assert any("PUA" in a for a in alertas_pua)

    # Caso 3: Fragmentação de fórmula (v seguido de espaço e potência)
    texto_frag = "Sabendo que v  ^2 = 25 m/s."
    alertas_frag = auditar_integridade_questao(texto_frag)
    assert any("fragmentação" in a for a in alertas_frag)


def test_extrair_questoes_com_avisos(tmp_path, monkeypatch):
    """
    Testa a integração da auditoria dentro da função de extração.
    """
    texto_simulado = (
        "B.1) Questão perfeita.\n"
        "B.2) Questão com erro de raiz √ 25 e caractere \uf06d."
    )

    # 1. Mock do pdfplumber (para não abrir um arquivo real)
    class MockPage:
        def extract_text(self):
            return texto_simulado

    class MockPDF:
        def __init__(self, *args, **kwargs):
            self.pages = [MockPage()]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(pdfplumber, "open", lambda x: MockPDF())

    # 2. CORREÇÃO: Mock do Path.exists
    # Isso faz com que a função acredite que o fake.pdf existe

    monkeypatch.setattr(Path, "exists", lambda x: True)

    # Executa a extração
    questoes = extrair_questoes_pdf("fake.pdf", base_char="B")

    # Agora o assert deve passar
    assert len(questoes) == 2
    assert "%% [REVISAR:" in questoes[1]
    assert "Raiz quadrada" in questoes[1]


def test_multiplos_de_dez():
    # Cenário: O texto da questão contém múltiplos de 10 e números grandes
    corpo_questao_original = (
        "O prêmio de 100000 reais foi dividido em 10 parcelas de 10000."
    )
    texto_pdf_completo = f"B.1) {corpo_questao_original}"

    mock_page = MagicMock()
    mock_page.extract_text.return_value = texto_pdf_completo
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open") as mock_open, patch.object(
        Path, "exists", return_value=True
    ):

        mock_open.return_value.__enter__.return_value = mock_pdf

        # Executa a extração
        questoes = extrair_questoes_pdf("teste_numeros.pdf", base_char="B")

    # Verificações
    assert len(questoes) == 1
    # Verifica se os múltiplos de 10 no corpo foram preservados exatamente
    assert "100000" in questoes[0]
    assert "10" in questoes[0]
    assert "10000" in questoes[0]
    assert questoes[0] == corpo_questao_original
