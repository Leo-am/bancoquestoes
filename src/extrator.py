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
    Localiza o PDF em data/processed e extrai as questões.
    Exemplo: base_char='B' busca por 'B.1)', 'B.2)', etc.
    """
    # 1. Localiza a raiz do projeto a partir deste arquivo (src/extractor.py)
    # .parent é 'src', .parent.parent é a raiz do projeto
    project_root = Path(__file__).resolve().parent.parent

    # 2. Define o caminho para o PDF
    pdf_path = project_root / "data" / "raw" / filename

    if not pdf_path.exists():
        print(f"❌ Erro: O arquivo {pdf_path} não foi encontrado.")
        return []

    full_text = []

    try:
        # 3. Extração do texto
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    full_text.append(text)

        document_text = "\n".join(full_text)

        # 4. Regex ajustado (sem espaços conforme solicitado)
        # re.escape garante que caracteres especiais no base_char não quebrem o regex
        pattern = rf"{re.escape(base_char)}\.\d+\)"

        # 5. Divisão e limpeza
        parts = re.split(pattern, document_text)
        questions = [q.strip() for q in parts[1:] if q.strip()]

        print(f"✅ Sucesso! {len(questions)} questões extraídas de: {filename}")
        return questions

    except Exception as e:
        print(f"❌ Erro durante a extração: {e}")
        return []


def extract_questions_from_OBFEP(pdf_path: str, base_char: str = "B") -> List[str]:
    """
    Extrai questões de uma prova da OBFEP utilizando um padrão incremental customizável.

    Exemplo:

    Se base_char='A', procura 'A.1)', 'A.2)', etc.
    """
    full_text = []

    try:
        # 1. Extração de todo o texto do PDF
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text.append(page_text)

        document_text = "\n".join(full_text)

        # 2. Construção do Padrão Regex Dinâmico
        # f"{base_char}" -> Letra escolhida seguida de ponto
        # \d+             -> Um ou mais dígitos
        # \)              -> Parênteses de fechamento
        regex_pattern = rf"{re.escape(base_char)}\d+\)"

        # 3. Divisão do texto
        # Usamos o padrão dinâmico para o split
        questions = re.split(regex_pattern, document_text)

        # 4. Limpeza e Filtro
        # Ignora o cabeçalho antes da primeira questão [1:]
        questions = [q.strip() for q in questions[1:] if q.strip()]

        print(
            f"✅ Extração com delimitador '{base_char}.X)' concluída: {len(questions)} questões."
        )
        return questions

    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{pdf_path}' não encontrado.")
        return []
    except Exception as e:
        print(f"❌ Erro na extração: {e}")
        return []
