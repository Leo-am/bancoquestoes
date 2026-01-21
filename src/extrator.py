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

        # APLICA A LIMPEZA AQUI (Antes de separar as questões)
        document_text = limpar_texto_extracao(document_text)

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

def limpar_texto_extracao(texto: str) -> str:
    """
    Limpa o texto bruto extraído do PDF para armazenamento no Banco de Dados.
    Remove ruídos de formatação e corrige erros comuns de extração.
    """
    if not texto:
        return ""

    # 1. Padronizar Sobrescritos Unicode para formato "Caractere^Número"
    # Isso converte o caractere único '²' em '^2' para facilitar o Regex depois
    superscritos_unicode = {
        '¹': '^1', '²': '^2', '³': '^3',
        '⁴': '^4', '⁵': '^5', '⁶': '^6',
        '⁷': '^7', '⁸': '^8', '⁹': '^9', '⁰': '^0',
        'ⁿ': '^n', 'ª': 'a', 'º': 'o'
    }
    for uni, sub in superscritos_unicode.items():
        texto = texto.replace(uni, sub)

    subscritos_unicode = {
    '₀': '_0', '₁': '_1', '₂': '_2', '₃': '_3', '₄': '_4',
    '₅': '_5', '₆': '_6', '₇': '_7', '₈': '_8', '₉': '_9'
    }
    for uni, sub in subscritos_unicode.items():
        texto = texto.replace(uni, sub)

    # 2. Corrigir Graus e Celsius
    # PDFs costumam usar o caractere '°' (U+00B0) ou 'º' (U+00BA)
    # Vamos padronizar tudo para o símbolo de grau padrão
    texto = texto.replace('º', '°') 
    
    # 3. Corrigir números "flutuantes" que deveriam ser expoentes
    # Em física, se houver um 'm' ou 's' seguido de um espaço e um 2 ou 3 isolado,
    # provavelmente é m² ou s³.
    # Regex: Procura unidade + espaço opcional + número 2 ou 3 no final de palavra
    texto = re.sub(r'\b(m|s|cm|km)\s*([23])\b', r'\1^\2', texto)

    # 4. Tratar Notação Científica "quebrada"
    # Se o 10 e o expoente vieram separados por espaço: "10 5" -> "10^5"
    texto = re.sub(r'10\s+([-]?\d+)', r'10^\1', texto)

    # 1. Corrigir quebras de linha artificiais
    # Remove quebras de linha que ocorrem no meio de uma frase (não seguidas por nova questão)
    # Mas preserva quebras que parecem ser o fim de um parágrafo.
    texto = re.sub(r'(?<![.!?])\n(?![A-Ea-e][\.\)])', ' ', texto)

    # 2. Corrigir hifenização (palavras separadas no fim da linha)
    # Ex: "ace- \nleração" -> "aceleração"
    texto = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', texto)

    # 3. Remover espaços múltiplos
    texto = re.sub(r'[ \t]+', ' ', texto)

    # 4. Corrigir "Ligaduras" comuns em PDFs
    # Às vezes 'fi', 'fl', 'ff' viram caracteres únicos estranhos
    ligaduras = {
        '\ufb01': 'fi',
        '\ufb02': 'fl',
        '\ufb03': 'ffi',
        '\ufb04': 'ffl',
        '\u00a0': ' ',  # Espaço não quebrável
    }
    for original, substituto in ligaduras.items():
        texto = texto.replace(original, substituto)

    # 5. Padronizar símbolos básicos (sem comandos LaTeX ainda!)
    # Isso garante que o DB tenha caracteres que você consiga ler facilmente
    substituicoes_basicas = {
        '': '*',      # Marcadores de lista comuns
        '–': '-',      # En-dash para hífen normal
        '—': '-',      # Em-dash para hífen normal
        '“': '"',      # Aspas inteligentes para normais
        '”': '"',
        '‘': "'",
        '’': "'",
    }
    for original, substituto in substituicoes_basicas.items():
        texto = texto.replace(original, substituto)

    # 1. Normalização Universal de Traços e Sinais
    # Captura todos os tipos de traços (en-dash, em-dash, minus sign unicode) 
    # e converte para o hífen padrão (-) que o Python/LaTeX entendem.
    padrao_tracos = r'[–—−‐⁃]' 
    texto = re.sub(padrao_tracos, '-', texto)

    # 2. Correção Geral de Expoentes Negativos (Unidades e Notação)
    # Busca uma letra ou símbolo (como C ou m) seguido de um sinal de menos e um número
    # Ex: °C-1 -> °C^-1 | s-1 -> s^-1 | 10-6 -> 10^-6
    # O pattern: (\w|°|%)-(\d+) 
    # (Letra ou símbolo) seguido de (-) seguido de (dígitos)
    texto = re.sub(r'(\w|°|%)-(\d+)', r'\1^\2', texto)

    # 3. Proteção para Notação Científica "Quebrada"
    # Se o PDF extraiu "10 -6" ou "10- 6", remove os espaços e garante o ^
    texto = re.sub(r'10\s*\^?\s*-?\s*(\d+)', r'10^-\1', texto)

    # 4. Limpeza de espaços duplos que surgem após as substituições
    texto = re.sub(r'\s+', ' ', texto)

    return texto.strip()