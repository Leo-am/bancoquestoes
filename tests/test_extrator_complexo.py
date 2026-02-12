from pathlib import Path
from unittest.mock import MagicMock

import pytest
from reportlab.pdfgen import canvas

from src.extrator import extract_questions_from_pdf


# --- FUNÇÃO AUXILIAR (Sem o prefixo 'test_') ---
def gerar_pdf_teste_complexo(caminho_pdf: Path):
    """Cria um PDF com fórmulas, notação científica e símbolos."""
    c = canvas.Canvas(str(caminho_pdf))

    # Q1: Notação Científica e Unidades
    c.drawString(100, 800, "B.1) A constante de Coulomb é k = 8.99e9 N.m2/C2.")

    # Q2: Química (Simulando subscritos)
    txt_q2 = c.beginText(100, 750)
    txt_q2.textOut("B.2) Analise a combustão do etileno: C")
    txt_q2.setRise(-2)
    txt_q2.textOut("2")
    txt_q2.setRise(0)
    txt_q2.textOut("H")
    txt_q2.setRise(-2)
    txt_q2.textOut("4")
    txt_q2.setRise(0)
    c.drawText(txt_q2)

    # Q3: Equação (Usando sobrescrito para o quadrado)
    txt_q3 = c.beginText(100, 700)
    txt_q3.textOut("B.3) Resolva o discriminante da equação: delta = b")
    txt_q3.setRise(3)
    txt_q3.textOut("2")
    txt_q3.setRise(0)
    txt_q3.textOut(" - 4ac.")
    c.drawText(txt_q3)

    # Q4: Gráfico/Figura (Desenhando um elemento gráfico)
    c.drawString(100, 650, "B.4) Com base na figura abaixo, determine a tração:")
    c.rect(100, 600, 50, 30, stroke=1)  # Simula um bloco

    # Q5: Notação e Unidades Compostas
    c.drawString(100, 550, "B.5) A velocidade da luz é aproximadamente 3.0e8 m/s.")

    c.save()


# --- O TESTE UNITÁRIO ---
def test_extracao_elementos_complexos(tmp_path, monkeypatch):
    """
    Testa se o extrator lida com PDFs reais contendo elementos complexos.
    """
    # 1. Configurar estrutura de pastas temporárias
    # Simulando projeto/data/raw/
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    pdf_teste = raw_dir / "prova_teste.pdf"

    # 2. Criar o PDF de fato
    gerar_pdf_teste_complexo(pdf_teste)

    # 3. Monkeypatch: Forçar a função a usar o tmp_path como raiz do projeto
    # Isso faz com que 'project_root / "data" / "raw"' aponte para o nosso diretório temporário
    import src.extrator

    # Mock do Path: quando a função chamar Path(__file__), retornamos um Mock que
    # simula a estrutura de pastas correta dentro do tmp_path.
    mock_root = MagicMock()
    mock_root.resolve.return_value.parent.parent = tmp_path
    monkeypatch.setattr("src.extrator.Path", MagicMock(return_value=mock_root))

    # 4. Executar a função
    resultado = extract_questions_from_pdf("prova_teste.pdf", base_char="B")

    # 5. Asserções
    assert len(resultado) == 5, f"Esperava 5 questões, mas obteve {len(resultado)}"

    # Q1: Notação científica
    assert "8.99e9" in resultado[0]

    # Q2: Química (Remover espaços ajuda a validar se o conteúdo foi pego)
    # O pdfplumber pode extrair 'C 2 H 4', por isso usamos replace(" ", "") no assert
    texto_q2 = resultado[1].replace(" ", "")
    assert "C2H4" in texto_q2

    # Q3: Equação (Sobrescrito)
    # Dependendo de como o pdfplumber lê o 'setRise', o '2' pode aparecer colado ou separado
    assert "b" in resultado[2] and "2" in resultado[2]
    assert "- 4ac" in resultado[2]

    # Q5: Verificação de Unidades
    assert "3.0e8" in resultado[4]
