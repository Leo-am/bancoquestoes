import pdfplumber
import sqlite3

def extract_questions_from_pdf(pdf_path, delimiter):
    """
    Extrai questões de um arquivo PDF usando um delimitador específico.

    Parameters
    ----------
    pdf_path : str
        O caminho do arquivo PDF de onde as questões serão extraídas.
    delimiter : str
        Delimitador utilizado para encontrar as questões.

    Returns
    -------
    list of str
        Uma lista contendo as questões extraídas, cada uma como uma
        string.

    Notes
    -----
    A função utiliza a biblioteca `pdfplumber` para abrir o PDF e
    iterar por todas as suas páginas.
    O texto de cada página é extraído e segmentado para identificar
    questões com base em um delimitador.
    Neste exemplo, "Q." é utilizado como delimitador para separar
    as questões.

    Example
    -------
    >>> questions = extract_questions_from_pdf("sample_questions.pdf")
    >>> print(questions[0])
    "Questão 1: Qual é a velocidade da luz no vácuo?"

    Observações
    -----------
    - A função assume que cada questão é precedida pelo marcador "Q."
    no PDF. Esse delimitador pode ser ajustado para outros padrões,
    se necessário.
    - A biblioteca `pdfplumber` precisa estar instalada para que a
    função funcione corretamente.
    """
    questions = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Identificar questões usando regex ou padrões específicos
            # Exemplo básico de separação de questões por "Q."
            questions.extend(text.split(f"{delimiter}")[1:]) 
    return questions



def create_database(nome):
    """
    Cria o banco de dados f'{nome}.db' e a tabela 'questoes'
    se ainda não existirem.

    A função estabelece uma conexão com o banco de dados SQLite
    chamado 'banco_questoes.db'. 
    Em seguida, cria uma tabela chamada 'questoes'
    que armazena informações sobre as questões, 
    incluindo ID, texto, tema, dificuldade e série.

    Parameters
    ----------
    nome : str
        String com o nome do banco de dados.

    Returns
    -------
    None

    Notes
    -----
    - A tabela 'questoes' é criada apenas se ela não existir no banco
    de dados, para evitar substituição de dados.
    - Cada questão é identificada por um ID exclusivo e armazena
    informações sobre o texto da questão, o tema, a dificuldade 
    e a série para categorização.
    
    Example
    -------
    >>> create_database()
    Banco de dados e tabela 'questoes' foram criados se não existiam anteriormente.
    """
    conn = sqlite3.connect(f'{name}.db')
    cursor.execute("PRAGMA encoding = 'UTF-8';")  # Ensure UTF-8 encoding
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS questoes (
                       id INTEGER PRIMARY KEY,
                       texto TEXT,
                       tema TEXT,
                       dificuldade TEXT,
                       serie TEXT)''')
    conn.commit()
    conn.close()

def insert_question(banco, texto, tema, dificuldade, serie):
    """
    Insere uma nova questão na tabela 'questoes' do banco de dados
    f'{banco}.db'.

    Esta função adiciona uma nova questão ao banco de dados,
    especificando o texto da questão, o tema, o nível de dificuldade
    e a série.

    Parameters
    ----------
    banco : str
        Nome do banco a ser atualizado.
    texto : str
        O texto da questão a ser inserida.
    tema : str
        O tema ou assunto da questão.
    dificuldade : str
        O nível de dificuldade da questão (ex.: "Fácil", "Médio", "Difícil").
    serie : str
        A série ou nível de ensino para o qual a questão é destinada
        (ex.: "1º ano", "2º ano").

    Returns
    -------
    None

    Notes
    -----
    - A função assume que o banco de dados e a tabela 'questoes' já
    foram criados.
    - É necessário passar todos os parâmetros corretamente para garantir
    a integridade dos dados.

    Example
    -------
    >>> insert_question("Qual é a fórmula da velocidade?", "Física",
                        "Fácil", "1º ano")
    Inseriu uma nova questão na tabela 'questoes' com os valores
    especificados.
    """
    conn = sqlite3.connect(f'{banco}.db')
    cursor = conn.cursor()
    cursor.execute('''INSERT INTO questoes (texto, tema, dificuldade, serie)
                      VALUES (?, ?, ?, ?)''', (texto, tema, dificuldade, serie))
    conn.commit()
    conn.close()

