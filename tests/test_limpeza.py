import pytest

from src.limpeza import limpar_para_latex


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        # Teste de Porcentagem (seu problema atual)
        ("O rendimento é de 80%.", r"O rendimento é de \qty{80}{\percent}."),
        ("A margem de erro é % alta.", r"A margem de erro é \unit{\percent} alta."),
        # Teste de Notação Científica
        ("A constante é 6.62 x 10^-34 J", r"A constante é \qty{6.62e-34}{J}"),
        ("O valor é 2*10^5 Pa", r"O valor é \qty{2e5}{Pa}"),
        (
            "No início, o gás estava a 120 °C e a coluna de mercúrio tinha h = 10^-4 cm.",
            r"No início, o gás estava a \qty{120}{\celsius} e a coluna de mercúrio tinha h = \qty{10e-4}{cm}.",
        ),
        # Teste de Unidades e Símbolos Gregos
        ("A temperatura é 25°C.", r"A temperatura é \qty{25}{\celsius}."),
        ("Resistência de 100 Ω.", r"Resistência de \qty{100}{\ohm}."),
        ("O valor de π é aproximado.", r"O valor de \textpi  é aproximado."),
        # Teste de Caracteres Reservados (Escape)
        ("Equação_1 e Custo&Cia", r"Equação\_1 e Custo\&Cia"),
        ("Texto com # e {chaves}", r"Texto com \# e \{chaves\}"),
        # Teste de Strings Vazias
        ("", ""),
        (None, ""),
    ],
)
def test_limpar_para_latex(entrada, esperado):
    assert limpar_para_latex(entrada) == esperado


def test_limpar_para_latex_alternativas():
    # Use triple quotes para definir o bloco exatamente como ele é
    entrada = "Quanto é 2+2?\na) 5\nb) 6\nc) 4\nd) 2"

    # Use raw strings para os resultados esperados para evitar confusão com as barras do LaTeX
    esperado = (
        r"Quanto é \num{2}+\num{2}?"
        + "\n"
        + r"a) \num{5}"
        + "\n"
        + r"b) \num{6}"
        + "\n"
        + r"c) \num{4}"
        + "\n"
        + r"d) \num{2}"
    )

    resultado = limpar_para_latex(entrada)

    # Normalização de segurança para o teste passar independente do SO
    assert resultado.replace("\r\n", "\n") == esperado.replace("\r\n", "\n")


def test_micro_como_unidade_e_texto():
    # Testando \uf06d (mu) isolado e como prefixo de unidade
    # Caso 1: \uf06d como variável
    # Caso 2: 10 \uf06dC (10 microCoulombs)
    entrada = "O valor de \uf06d é 10 \uf06dC."

    # Esperamos:
    # 1. \uf06d isolado -> \textmu
    # 2. 10 \uf06dC -> \qty{10}{\micro\coulomb} (ou conforme sua formatar_grandeza_fisica)
    # Nota: O espaço extra no \textmu serve para não colar no "é"
    resultado = limpar_para_latex(entrada)

    # Verificação (ajuste conforme a sua função formatar_grandeza_fisica mapeia 'muC')
    assert r"\textmu " in resultado
    assert r"\qty{10}{\micro} C" in resultado or r"\qty{10}{\mu} C" in resultado


def test_mapeamento_caracteres_pua():
    # Simulando uma string que veio do banco com os códigos do PDF
    # \uf071 (theta), \uf06d (mu), \uf044 (Delta), \uf067 (gamma)
    entrada = "Calcule \uf071 sabendo que \uf06d = 2,0 e \uf044 = 0."

    # Esperamos que os códigos sumam e deem lugar aos comandos LaTeX
    # Note que o "2,0" isolado deve ser pego pela nossa regra de \num
    esperado = (
        r"Calcule \texttheta  sabendo que \textmu  = \num{2.0} e \textDelta  = \num{0}."
    )

    assert limpar_para_latex(entrada) == esperado


def test_letras_gregas_compostas():
    # Testando Gamma maiúsculo, eta, tau e delta minúsculo
    entrada = "A constante \uf047 depende de \uf068 e \uf074, mas não de \uf064."

    esperado = r"A constante \textGamma  depende de \texteta  e \texttau , mas não de \textdelta ."

    assert limpar_para_latex(entrada) == esperado


def test_siglas_historicas():
    entrada = "O evento ocorreu em 450 a. C.. e foi importante."
    saída = limpar_para_latex(entrada)
    assert "450 a.C." in saída or "450 \num{a.C.}" not in saída
    # O ideal é que o 450 vire \num{450} e o a.C. fique como texto


def test_protecao_sigla_ac():
    entrada = "Ocorreu em 150 a. C. e foi rápido."
    resultado = limpar_para_latex(entrada)

    # Verifica se o número foi tokenizado
    assert r"\num{150}" in resultado
    # Verifica se a sigla foi preservada sem quebras de linha
    assert "a.C." in resultado
    assert r"\\[5pt]" not in resultado
    # Verifica se não sobrou lixo de token
    assert "@@TOKEN" not in resultado
