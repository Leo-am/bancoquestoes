import pdfplumber
import sqlite3
from typing import List, Optional, Tuple

class Questao:
    """
    Representa uma única questão com todos os seus atributos,
    garantindo que os dados sejam agrupados de forma consistente.
    """
    def __init__(
        self,
        texto: str,
        serie: str,
        origem: str,
        dificuldade: str,
        imagem_path: Optional[str] = None,
        temas: Optional[List[str]] = None
    ):
        self.texto = texto
        self.serie = serie
        self.origem = origem
        self.dificuldade = dificuldade
        self.imagem_path = imagem_path
        self.temas = temas if temas is not None else []
    
    def to_tuple(self) -> tuple:
        """
        Converte os dados da questão em uma tupla na ordem esperada pelo SQLite
        (texto, imagem, serie, origem, temas_str, dificuldade).
        """
        # Converte a lista de temas em uma string separada por vírgulas
        temas_str = ", ".join(self.temas)
        
        return (
            self.texto,
            self.serie,
            self.origem,
            self.dificuldade,
            self.imagem_path,
            temas_str
        )

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



def create_database(nome: str) -> None:
    """
    Cria o banco de dados f'{nome}.db' e a tabela 'questoes' (se não existirem),
    utilizando a ordem de colunas especificada:
    (texto, serie, origem, dificuldade, imagem, temas).

    Parameters
    ----------
    nome : str
        String com o nome do banco de dados (ex: 'meu_banco_questoes').

    Returns
    -------
    None
    """
    db_file = f'{nome}.db'
    
    try:
        # Uso do 'with' para garantir que a conexão seja fechada automaticamente
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA encoding = 'UTF-8';")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questoes (
                    id INTEGER PRIMARY KEY,
                    
                    texto TEXT NOT NULL,
                    serie TEXT,              
                    origem TEXT,             
                    dificuldade TEXT,         
                    imagem TEXT,             
                    temas TEXT               
                )
            ''')
            
            print(f"Banco de dados '{db_file}' e tabela 'questoes' criados/verificados.")
            
    except sqlite3.Error as e:
        print(f"Erro ao criar o banco de dados/tabela '{db_file}': {e}")


def insert_question(banco: str, questao: Questao) -> None:
    """
    Insere uma nova questão na tabela 'questoes' do banco de dados f'{banco}.db'
    usando um objeto Questao.

    Parameters
    ----------
    banco : str
        Nome do banco de dados (ex: 'meu_banco'). O arquivo será '{banco}.db'.
    questao : Questao
        Objeto da classe Questao contendo todos os dados a serem inseridos.
    
    Returns
    -------
    None
    """
    try:
        with sqlite3.connect(f'{banco}.db') as conn:
            cursor = conn.cursor()
            
            # A ordem dos campos aqui DEVE CORRESPONDER à ordem da tupla gerada por questao.to_tuple()
            query = """
            INSERT INTO questoes 
            (texto, serie, origem, dificuldade, imagem, temas) 
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            # Utiliza o método to_tuple() da classe Questao para obter os valores na ordem correta
            cursor.execute(query, questao.to_tuple())
            
            conn.commit()
            
    except sqlite3.Error as e:
        print(f"Erro ao inserir questão no banco de dados: {e}")


def checar_questoes_inseridas(nome_do_banco: str, nome_da_tabela: str = 'questoes', limite: int = 10) -> List[Tuple]:
    """
    Conecta-se ao banco de dados, busca as questões adicionadas e as exibe.

    Parameters
    ----------
    nome_do_banco : str
        Nome do banco de dados (sem a extensão .db).
    nome_da_tabela : str
        Nome da tabela a ser consultada ('questoes' por padrão).
    limite : int
        Número máximo de registros a exibir.

    Returns
    -------
    list of tuple
        Uma lista contendo os registros do banco de dados.
    """
    db_file = f'{nome_do_banco}.db'
    
    print(f"\n--- CONSULTANDO DADOS na Tabela '{nome_da_tabela}' em '{db_file}' ---")
    
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            
            # Buscando todos os campos de todas as questões, limitando o resultado
            cursor.execute(f"SELECT * FROM {nome_da_tabela} LIMIT {limite};")
            
            registros = cursor.fetchall()
            
            if not registros:
                print("⚠️ Nenhuma questão encontrada na tabela.")
                return []
            
            # Obtendo os nomes das colunas para exibir o cabeçalho (para melhor debug)
            nomes_colunas = [description[0] for description in cursor.description]
            
            # --- Exibição Formatada ---
            print(f"\n✅ {len(registros)} Questões Encontradas (Limite: {limite}):")
            
            # Exibe o cabeçalho (nomes das colunas)
            print(" | ".join(f"{nome:<15}" for nome in nomes_colunas))
            print("-" * (len(nomes_colunas) * 17))
            
            # Exibe os dados (truncando strings longas como 'texto')
            for registro in registros:
                linha_formatada = []
                for i, valor in enumerate(registro):
                    
                    # CORREÇÃO APLICADA AQUI: Tratamento do campo 'texto'
                    if nomes_colunas[i] == 'texto':
                        valor_str = str(valor)
                        
                        # Limita o texto a 12 caracteres + '...' para caber na coluna de 15
                        if len(valor_str) > 15: 
                            display_text = valor_str[:12] + "..."
                        else:
                            display_text = valor_str
                            
                        linha_formatada.append(f"{display_text:<15}")
                    
                    else:
                        # Aplica a formatação padrão para outros campos
                        linha_formatada.append(f"{str(valor):<15}")
                
                print(" | ".join(linha_formatada))
                
            return registros

    except sqlite3.Error as e:
        print(f"\n❌ Erro ao consultar o banco de dados: {e}")
        return []

