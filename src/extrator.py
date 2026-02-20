"""
Módulo para extração de questões de arquivos PDF utilizando Regex.
"""

import io
import os
import re
from pathlib import Path
from typing import List

import fitz  # PyMuPDF
import pdfplumber
from PIL import Image


def auditar_integridade_questao(texto: str) -> list:
    """Detecta padrões que sugerem falha na extração (raízes, PUA, fórmulas)."""
    alertas = []

    # 1. Alerta de Raiz Quadrada (Símbolo isolado ou comando sem chaves)
    if ("√" in texto or r"\sqrt" in texto) and "{" not in texto:
        alertas.append("Raiz quadrada possivelmente mal formatada")

    # 2. Alerta de Caracteres Fantasmas (PUA)
    if re.search(r"[\uf000-\uf0ff]", texto):
        alertas.append("Detectados caracteres não convertidos (PUA)")

    # 3. Alerta de Fórmulas Fragmentadas (Ex: v 2 ou c 2)
    # Procuramos um espaço, uma letra única, espaço(s) e um dígito.
    # O \b garante que estamos pegando uma letra isolada.
    if re.search(r"\b[a-zA-Z]\s+\^?\d", texto):
        # Filtro extra: ignorar as letras 'e', 'a', 'o' que são comuns sozinhas em português
        # apenas se não houver um circunflexo ^ indicando potência
        match = re.search(r"\b([a-zA-Z])\s+\^?(\d)", texto)
        if match and match.group(1).lower() not in ["a", "e", "o"]:
            alertas.append("Possível fragmentação em potências/fórmulas")

    # 4. Alerta de Alternativas Incompletas
    if "a)" in texto.lower() and "d)" not in texto.lower():
        alertas.append("Múltipla escolha parece estar incompleta")

    return alertas


def extrair_questoes_pdf(filename: str, base_char: str = "B") -> List[str]:
    """
    Localiza o PDF em data/raw e extrai as questões usando Regex.
    Exemplo: base_char='B' busca por 'B.1)', 'B.2)', etc.

    Parameters:
    -----------
    filename : str
        O nome do arquivo PDF a ser processado.
    base_char : str
        O caractere base para identificação das questões (ex: 'B').

    Returns:
    --------
    List[str]
        Uma lista com as questões extraídas do PDF.
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

        # --- LÓGICA DE AUDITORIA ADAPTADA ---
        raw_questions = [q.strip() for q in parts[1:] if q.strip()]
        questions_list = []

        print(f"\n🔍 Auditando {len(raw_questions)} questões de {filename}...")

        for i, texto_questao in enumerate(raw_questions, 1):
            avisos = auditar_integridade_questao(texto_questao)
            label = f"{base_char}.{i})"

            if avisos:
                print(f"⚠️  {label}: {', '.join(avisos)}")
                # Opcional: injeta um comentário LaTeX para facilitar o Ctrl+F depois
                texto_questao = f"%% [REVISAR: {'; '.join(avisos)}]\n" + texto_questao

            questions_list.append(texto_questao)

        print(f"✅ Sucesso! Questões extraídas e auditadas.\n")
        return questions_list

    except Exception as e:
        print(f"❌ Erro inesperado na extração: {e}")
        return []


def limpar_texto_extracao(texto: str) -> str:
    """
    Limpa o texto bruto extraído do PDF para armazenamento no Banco de Dados.
    Remove ruídos de formatação e corrige erros comuns de extração.

    Parameters:
    -----------
    texto : str
        O texto bruto a ser limpo.

    Returns:
    --------
    str
        O texto limpo e formatado para armazenamento no Banco de Dados.
    """
    if not texto:
        return ""

    # 1. Padronizar Sobrescritos Unicode para formato "Caractere^Número"
    # Isso converte o caractere único '²' em '^2' para facilitar o Regex depois
    superscritos_unicode = {
        "¹": "^1",
        "²": "^2",
        "³": "^3",
        "⁴": "^4",
        "⁵": "^5",
        "⁶": "^6",
        "⁷": "^7",
        "⁸": "^8",
        "⁹": "^9",
        "⁰": "^0",
        "ⁿ": "^n",
        "ª": "a",
        "º": "o",
    }
    for uni, sub in superscritos_unicode.items():
        texto = texto.replace(uni, sub)

    subscritos_unicode = {
        "₀": "_0",
        "₁": "_1",
        "₂": "_2",
        "₃": "_3",
        "₄": "_4",
        "₅": "_5",
        "₆": "_6",
        "₇": "_7",
        "₈": "_8",
        "₉": "_9",
    }
    for uni, sub in subscritos_unicode.items():
        texto = texto.replace(uni, sub)

    # 2. Corrigir Graus e Celsius
    # PDFs costumam usar o caractere '°' (U+00B0) ou 'º' (U+00BA)
    # Vamos padronizar tudo para o símbolo de grau padrão
    texto = texto.replace("º", "°")

    # 3. Corrigir números "flutuantes" que deveriam ser expoentes
    # Em física, se houver um 'm' ou 's' seguido de um espaço e um 2 ou 3 isolado,
    # provavelmente é m² ou s³.
    # Regex: Procura unidade + espaço opcional + número 2 ou 3 no final de palavra
    texto = re.sub(r"\b(m|s|cm|km)\s*([23])\b", r"\1^\2", texto)

    # 4. Tratar Notação Científica "quebrada"
    # Se o 10 e o expoente vieram separados por espaço: "10 5" -> "10^5"
    texto = re.sub(r"10\s+([-]?\d+)", r"10^\1", texto)

    # 1. Corrigir quebras de linha artificiais
    # Remove quebras de linha que ocorrem no meio de uma frase (não seguidas por nova questão)
    # Mas preserva quebras que parecem ser o fim de um parágrafo.
    texto = re.sub(r"(?<![.!?])\n(?![A-Ea-e][\.\)])", " ", texto)

    # 2. Corrigir hifenização (palavras separadas no fim da linha)
    # Ex: "ace- \nleração" -> "aceleração"
    texto = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", texto)

    # 3. Remover espaços múltiplos
    texto = re.sub(r"[ \t]+", " ", texto)

    # 4. Corrigir "Ligaduras" comuns em PDFs
    # Às vezes 'fi', 'fl', 'ff' viram caracteres únicos estranhos
    ligaduras = {
        "\ufb01": "fi",
        "\ufb02": "fl",
        "\ufb03": "ffi",
        "\ufb04": "ffl",
        "\u00a0": " ",  # Espaço não quebrável
    }
    for original, substituto in ligaduras.items():
        texto = texto.replace(original, substituto)

    # 5. Padronizar símbolos básicos (sem comandos LaTeX ainda!)
    # Isso garante que o DB tenha caracteres que você consiga ler facilmente
    substituicoes_basicas = {
        "": "*",  # Marcadores de lista comuns
        "–": "-",  # En-dash para hífen normal
        "—": "-",  # Em-dash para hífen normal
        "“": '"',  # Aspas inteligentes para normais
        "”": '"',
        "‘": "'",
        "’": "'",
    }
    for original, substituto in substituicoes_basicas.items():
        texto = texto.replace(original, substituto)

    # --- TRECHO CORRIGIDO ---
    # 1. Normalização de traços (Mantém o hífen padrão)
    texto = re.sub(r"[–—−‐⁃]", "-", texto)

    # 2. Correção de Expoentes (Apenas para LETRAS ou símbolos, NUNCA números)
    # Trocamos \w por [a-zA-Z°%]. Isso impede que o '0' de '10' dispare a regra.
    texto = re.sub(r"([a-zA-Z°%])-(\d+)", r"\1^-\2", texto)

    # 3. Notação Científica rigorosa
    # Caso A: Se houver sinal de menos explícito (ex: 10-6 ou 10^-6)
    texto = re.sub(r"10\s*\^?\s*-\s*(\d+)", r"10^-\1", texto)

    # Caso B: Se houver espaço (ex: 10 6)
    texto = re.sub(r"10\s+(\d+)\b", r"10^\1", texto)

    return texto.strip()


if __name__ == "__main__":
    # Teste rápido se rodar este arquivo diretamente
    res = extrair_questoes_pdf("prova_exemplo.pdf", "B")
    if res:
        print(f"Primeira questão: {res[0][:50]}...")


def extrair_imagens_do_pdf(caminho_pdf, pasta_saida, min_px=100):
    """
    Extrai imagens de um arquivo PDF e as salva em uma pasta de saída.

    Parameters:
    -----------
    caminho_pdf : str
        O caminho para o arquivo PDF de entrada.
    pasta_saida : str
        O caminho para a pasta onde as imagens extraídas serão salvas.
    min_pix : int
        O tamanho mínimo (em pixels) para as imagens a serem extraídas.

    Returns:
    --------
    None
    """
    # Cria a pasta de saída se não existir
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    # Abre o documento
    pdf = fitz.open(caminho_pdf)

    contador = 1
    for num_pagina in range(len(pdf)):
        pagina = pdf[num_pagina]
        lista_imagens = pagina.get_images(full=True)

        for img_index, img in enumerate(lista_imagens):
            xref = img[0]  # Referência do objeto
            base_image = pdf.extract_image(xref)
            image_bytes = base_image["image"]
            extensao = base_image["ext"]  # png, jpeg, etc.

            # --- FILTRO DE TAMANHO ---
            # base_image["width"] e base_image["height"] dão os pixels reais
            largura = base_image["width"]
            altura = base_image["height"]

            if largura < min_px or altura < min_px:
                # Se a imagem for menor que 100x100 (exemplo), ela é ignorada
                continue

            # Carrega a imagem para garantir que não está corrompida
            image = Image.open(io.BytesIO(image_bytes))

            # Nome do arquivo: pagina_X_imagem_Y.png
            nome_arquivo = f"pag_{num_pagina+1}_img_{contador}.{extensao}"
            caminho_final = os.path.join(pasta_saida, nome_arquivo)

            image.save(caminho_final)
            print(f"Salvo: {nome_arquivo}")
            contador += 1

    pdf.close()


def extrair_imagens_por_questao(caminho_pdf, pasta_saida, delimiter=r"Questão\s*(\d+)"):
    pdf = fitz.open(caminho_pdf)

    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    questao_atual = "preambulo"  # Caso haja imagens antes da primeira questão
    contador_img_por_questao = 1

    for num_pagina in range(len(pdf)):
        pagina = pdf[num_pagina]

        # 1. ANALISAR O TEXTO DA PÁGINA PARA ATUALIZAR O DELIMITADOR
        # Extraímos o texto para saber se mudamos de questão nesta página
        texto_pagina = pagina.get_text()
        matches = re.findall(delimiter, texto_pagina)

        # 2. LOCALIZAR IMAGENS E SUAS POSIÇÕES
        lista_imagens = pagina.get_images(full=True)

        # Para maior precisão, pegamos onde cada imagem está na página (y-coordinate)
        # e onde cada "Questão X" está na página.
        items_pagina = []

        # Adiciona as questões encontradas à lista de busca de posição
        for m in re.finditer(delimiter, texto_pagina):
            # Encontra a posição vertical (y) do texto da questão
            areas = pagina.search_for(m.group(0))
            if areas:
                y_pos = areas[0].y1
                items_pagina.append(
                    {"tipo": "questao", "valor": m.group(0), "y": y_pos}
                )

        # Adiciona as imagens encontradas à lista de busca de posição
        for img in lista_imagens:
            xref = img[0]
            # get_image_rects retorna a posição da imagem na página
            rects = pagina.get_image_rects(xref)
            if rects:
                y_pos = rects[0].y1
                items_pagina.append({"tipo": "imagem", "xref": xref, "y": y_pos})

        # Ordena tudo o que foi encontrado na página de cima para baixo (pelo eixo Y)
        items_pagina.sort(key=lambda x: x["y"])

        # 3. PROCESSAR NA ORDEM VISUAL
        for item in items_pagina:
            if item["tipo"] == "questao":
                # Limpa o nome da questão para ser um nome de arquivo válido
                nova_questao = re.sub(r"[^\w\-]", "_", item["valor"])
                if nova_questao != questao_atual:
                    questao_atual = nova_questao
                    contador_img_por_questao = (
                        1  # Reinicia contagem de imagens para a nova questão
                    )

            elif item["tipo"] == "imagem":
                base_image = pdf.extract_image(item["xref"])

                # Filtro de tamanho mínimo (ex: 100px)
                if base_image["width"] < 100 or base_image["height"] < 100:
                    continue

                # Nome final: Questao_01_img_1.png
                nome_arquivo = f"{questao_atual}_img_{contador_img_por_questao}.{base_image['ext']}"
                caminho_final = os.path.join(pasta_saida, nome_arquivo)

                with open(caminho_final, "wb") as f:
                    f.write(base_image["image"])

                print(f"Detectada imagem para {questao_atual} -> {nome_arquivo}")
                contador_img_por_questao += 1

    pdf.close()
