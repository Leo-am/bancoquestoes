import re


def limpar_texto_puro(texto: str) -> str:
    """
    Escapa caracteres que o LaTeX interpretaria como comandos,
    mas que no contexto da questão são apenas texto literal.
    """
    if not texto:
        return ""

    # Dividimos o texto em partes: o que é TOKEN e o que não é
    partes = re.split(r"(@@TOKEN\d+@@)", texto)
    reservados = ["%", "_", "&", "#", "{", "}"]

    for i in range(len(partes)):
        # Só limpamos se a parte NÃO for um token
        if not re.match(r"@@TOKEN\d+@@", partes[i]):
            for char in reservados:
                partes[i] = re.sub(
                    rf"(?<!\\){re.escape(char)}", rf"\\{char}", partes[i]
                )

    return "".join(partes)


def formatar_grandeza_fisica(valor_bruto: str, unidade_bruta: str) -> str:
    """
    Transforma um par de strings (valor, unidade) no comando \qty do siunitx.
    Ex: ("10", "%") -> "\qty{10}{\percent}"
    """
    valor = valor_bruto.replace(",", ".")
    # Caso 1: Notação científica clássica (Ex: 2 x 10^5)
    if re.search(r"[xX·*]\s*10", valor):
        valor = re.sub(r"\s*[xX·*]\s*10\^?([-]?\d+)", r"e\1", valor)

    # Caso 2: Potência de base 10 pura (Ex: 10^-4)
    elif valor.startswith("10^") or valor.startswith("10-"):
        valor = re.sub(r"10\^?([-]?\d+)", r"10e\1", valor)

    unidade = unidade_bruta.strip()

    # Traduções de comandos de texto para comandos siunitx
    unidade = unidade.replace(r"\textmu", r"\micro")
    unidade = unidade.replace(r"\textOmega", r"\ohm")
    unidade = unidade.replace(r"\textDelta", r"\delta")

    substituicoes_unidade = {
        "%": r"\percent",
        "°C": r"\celsius",
        "°": r"\degree",
        "Ω": r"\ohm",
        "μ": r"\micro",
    }

    for simbolo, comando in substituicoes_unidade.items():
        unidade = unidade.replace(simbolo, comando)

    # Limpeza de espaços duplos que podem sobrar
    unidade = re.sub(r"\s+", " ", unidade).strip()

    if "^" in unidade and "{" not in unidade:
        unidade = re.sub(r"\^([-]?\d+)", r"^{\1}", unidade)

    return rf"\qty{{{valor}}}{{{unidade}}}"


def proteger_expoentes_matematicos(texto: str) -> str:
    """
    Envolve expressões com ^ em modo matemático $ $,
    mas ignora se já estiverem dentro de tokens ou comandos LaTeX conhecidos.
    """
    if not texto:
        return ""

    # Regex que busca:
    # Letra ou número + ^ + expoente (letras, números ou chaves)
    # Ex: x^2, 10^-4, (a+b)^n
    padrao_exp = r"([a-zA-Z0-9\(\)]+\^\{?[a-zA-Z0-9\-\+\/]+\}?)"

    def envolver(m):
        expr = m.group(1)
        # Se a expressão já começa com $, não fazemos nada
        return f"${expr}$"

    # Evitamos aplicar isso dentro de tokens @@TOKEN@@
    partes = re.split(r"(@@TOKEN\d+@@)", texto)
    for i in range(len(partes)):
        if not partes[i].startswith("@@TOKEN"):
            # Só aplica nos textos que não são tokens
            partes[i] = re.sub(padrao_exp, envolver, partes[i])

    return "".join(partes)


def limpar_para_latex(texto: str) -> str:
    if not texto:
        return ""

    cache_tokens = {}

    # --- PASSO 0: IMUNIDADE DIPLOMÁTICA PARA SIGLAS ---
    # Protegemos "a. C." ANTES de qualquer outra lógica de alternativa ou número
    siglas_map = {r"\ba\. ?C\.": "a.C.", r"\bd\. ?C\.": "d.C."}

    for padrao, valor_real in siglas_map.items():
        # Encontramos todas as ocorrências da sigla
        for m in re.finditer(padrao, texto):
            token_id = f"@@TOKEN{len(cache_tokens)}@@"
            cache_tokens[token_id] = valor_real
            # Substituímos no texto pelo token (ex: @@TOKEN0@@)
            texto = texto.replace(m.group(0), token_id, 1)

    # --- CONFIGURAÇÃO INICIAL ---
    unidades_orfas = {
        "%": r"\percent",
        "°C": r"\celsius",
        "Ω": r"\ohm",
        "°": r"\degree",
        "π": r"\textpi ",  # espaço proposital
        "Δ": r"\textDelta ",  # espaço proposital
    }

    def normalizar_caracteres_pdf(texto: str) -> str:
        # Mapeamento dos códigos fantasmas para comandos LaTeX
        mapeamento_pua = {
            "\uf071": r"\texttheta ",
            "\uf070": r"\textpi ",
            "\uf061": r"\textalpha ",
            "\uf062": r"\textbeta ",
            "\uf044": r"\textDelta ",
            "\uf067": r"\textgamma ",
            "\uf047": r"\textGamma ",
            "\uf064": r"\textdelta ",
            "\uf051": r"\textTheta ",
            "\uf06d": r"\textmu ",
            "\uf068": r"\texteta ",
            "\uf074": r"\texttau ",
        }

        for caractere_pua, comando in mapeamento_pua.items():
            texto = texto.replace(caractere_pua, comando)
        return texto

    texto = normalizar_caracteres_pdf(texto)

    # --- PASSO 1: TOKENIZAÇÃO DE GRANDEZAS COMPLETAS (Prioridade Máxima) ---
    # Capturamos Número + Unidade PRIMEIRO para evitar que se separem
    padrao_qty = r"((?:\d+[,.]?\d*(?:\s*[xX·*]\s*10\^?[-]?\d+)?)|(?:10\^?[-]?\d+))\s*((?!@)[a-zA-Z\\%°ΩμΔπ/]+(?:\^?-?\d+)?)"

    def proteger_e_formatar(m):
        valor_bruto = m.group(1)
        unidade_bruta = m.group(2)
        # FILTRO: Se a unidade for apenas a letra 'e' isolada, ignoramos a captura
        if unidade_bruta.lower() in ["a", "b", "c", "d", "e", "o"]:
            return m.group(0)  # Retorna o texto original sem tokenizar
        # Chama sua função especialista de física
        grandeza_formatada = formatar_grandeza_fisica(valor_bruto, unidade_bruta)

        token_id = f"@@TOKEN{len(cache_tokens)}@@"
        cache_tokens[token_id] = grandeza_formatada
        return token_id

    # Executa a substituição das grandezas completas
    texto = re.sub(padrao_qty, proteger_e_formatar, texto)

    # --- PASSO 1.5: UNIDADES COM EXPOENTE SEM NÚMERO (Ex: m/s^2 solto) ---
    # Captura padrões como m/s^2, cm^3, kg/m^2 que não têm número na frente
    padrao_unidade_expoente = r"(?<!@)\b([a-zA-Z/]+\^[-]?\d+)\b"

    def proteger_unidade_solta(m):
        unidade = m.group(1)
        # Se você usa siunitx, formatamos para \unit{unidade}
        # Se preferir modo matemático puro, use rf"${unidade}$"
        conteudo = rf"\unit{{{unidade}}}"

        token_id = f"@@TOKEN{len(cache_tokens)}@@"
        cache_tokens[token_id] = conteudo
        return token_id

    texto = re.sub(padrao_unidade_expoente, proteger_unidade_solta, texto)

    # --- PASSO 2: TOKENIZAÇÃO DE UNIDADES ÓRFÃS (O que sobrou) ---
    for simbolo, comando in unidades_orfas.items():
        # Como o que tinha número já virou TOKEN, aqui só pegamos o que está solto
        # Removi o \s? para não "roubar" o espaço do texto puro
        padrao_orfa = rf"{re.escape(simbolo)}"

        def substituir_orfa(m):
            simbolo_encontrado = m.group(0).strip()
            comando = unidades_orfas[simbolo_encontrado]

            token_id = f"@@TOKEN{len(cache_tokens)}@@"

            # Se for um comando de texto (grego), não usa \unit
            if "text" in comando:
                cache_tokens[token_id] = comando
            else:
                cache_tokens[token_id] = rf"\unit{{{comando}}}"

            return token_id

        texto = re.sub(padrao_orfa, substituir_orfa, texto)

    # 3. TOKENIZAÇÃO: Números isolados (sem unidade)
    # Captura números decimais ou inteiros que NÃO foram capturados antes
    # O negative lookahead (?!...) garante que não pegaremos números que já são tokens
    # O grupo decimal (?:[.,]\d+) agora exige um dígito após a vírgula/ponto
    padrao_num = r"(?<![\w@])(\d+(?:[.,]\d+)?)(?![@\w])"

    def formatar_numero_isolado(m):
        valor = m.group(1).replace(",", ".")
        # Evita tokenizar números muito pequenos que podem ser parte de IDs (opcional)
        # Se preferir, pode colocar apenas o comando \num
        token_id = f"@@TOKEN{len(cache_tokens)}@@"
        cache_tokens[token_id] = rf"\num{{{valor}}}"
        return token_id

    # Só aplicamos isso se o número estiver "solto" no texto
    texto = re.sub(padrao_num, formatar_numero_isolado, texto)

    # Agora que números e grandezas são TOKENS, o que sobrou com '^'
    # é provavelmente álgebra literal (x^2, v^2).
    texto = proteger_expoentes_matematicos(texto)

    # --- PASSO 3: LIMPEZA DO TEXTO ---
    # Agora o texto só tem palavras e @@TOKENn@@.
    # A função limpar_texto_puro não vai estragar os comandos LaTeX.
    texto = limpar_texto_puro(texto)

    # --- PASSO 4: REIDRATAÇÃO ---

    # Reidratação dos outros tokens (cache_tokens)
    for token_id, conteudo in cache_tokens.items():
        texto = texto.replace(token_id, conteudo)

    return texto
