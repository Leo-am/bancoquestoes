"""
Módulo para extração de questões de arquivos PDF utilizando Regex.
"""

import re
from pathlib import Path
from typing import List

import pdfplumber

if __name__ == "__main__":
    # Teste rápido se rodar este arquivo diretamente
    res = extract_questions_from_pdf("prova_exemplo.pdf", "B")
    if res:
        print(f"Primeira questão: {res[0][:50]}...")


def extract_questions_from_pdf(filename: str, base_char: str = "B") -> List[str]:
    """
    Localiza o PDF em data/raw e extrai as questões usando Regex.
    Exemplo: base_char='B' busca por 'B.1)', 'B.2)', etc.
    """
    # 1. Localiza a raiz do projeto (src/extractor.py -> projeto/)
    project_root = Path(__file__).resolve().parent.parent
    pdf_path = project_root / "data" / "raw" / filename

    if not pdf_path.exists():
        print(f"❌ Erro: O arquivo {pdf_path} não foi encontrado.")
        return []

    full_text = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)

        document_text = "\n".join(full_text)

        # Regex: Letra + ponto(opcional) + número + parênteses
        # O padrão rf"{re.escape(base_char)}\.?\d+\)" é mais flexível
        pattern = rf"{re.escape(base_char)}\.?\d+\)"

        parts = re.split(pattern, document_text)

        # Filtra strings vazias e remove espaços extras
        questions_list = [q.strip() for q in parts[1:] if q.strip()]

        print(f"✅ Sucesso! {len(questions_list)} questões extraídas de: {filename}")
        return questions_list

    except (FileNotFoundError, PermissionError) as e:
        print(f"❌ Erro de arquivo: {e}")
        return []
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"❌ Erro inesperado na extração: {e}")
        return []
