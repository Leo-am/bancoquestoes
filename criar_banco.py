import pdfplumber
import sqlite3
from typing import List, Optional, Tuple, Dict, Any

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

def extract_questions_from_pdf(pdf_path: str, delimiter: str) -> List[str]:
    """
    Extrai questões de um arquivo PDF, tratando questões que abrangem múltiplas páginas.
    
    A correção: Concatena o texto de todas as páginas antes de aplicar o delimitador.

    Parameters
    ----------
    pdf_path : str
        O caminho do arquivo PDF.
    delimiter : str
        Delimitador utilizado para encontrar as questões (ex: "Q.").

    Returns
    -------
    list of str
        Uma lista contendo as questões extraídas.
    """
    full_text = []
    
    try:
        # 1. Extração e Concatenação de Todo o Texto do Documento
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Adiciona o texto de cada página à lista, garantindo um espaço ou quebra
                # de linha para evitar que palavras de páginas diferentes se juntem
                full_text.append(page.extract_text())
                
        # Concatena todo o texto em um único bloco grande
        document_text = "\n".join(full_text)
        
        # 2. Aplicação do Delimitador ao Documento Inteiro
        # Faz o split do texto usando o delimitador, garantindo que mesmo
        # questões que cruzam páginas sejam separadas corretamente.
        
        # [1:] é usado para ignorar o texto antes do primeiro delimitador
        questions = document_text.split(delimiter)[1:]
        
        # Opcional: Limpar espaços em branco e quebras de linha no início de cada questão
        questions = [q.strip() for q in questions]

        return questions
        
    except FileNotFoundError:
        print(f"❌ Erro: Arquivo '{pdf_path}' não encontrado.")
        return []
    except Exception as e:
        print(f"❌ Ocorreu um erro durante a extração do PDF: {e}")
        return []



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


def deletar_questao_por_id(nome_do_banco: str, questao_id: int) -> bool:
    """
    Deleta uma entrada na tabela 'questoes' com base no seu ID.

    Parameters
    ----------
    nome_do_banco : str
        Nome do banco de dados (sem a extensão .db).
    questao_id : int
        O ID (chave primária) da questão a ser deletada.

    Returns
    -------
    bool
        True se a questão foi deletada com sucesso, False caso contrário.
    """
    db_file = f'{nome_do_banco}.db'
    
    try:
        # 1. Conexão e Gerenciamento de Recurso
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            
            # 2. Instrução SQL de Deleção
            # Usamos '?' para evitar ataques de injeção SQL, mesmo com um número inteiro
            sql_delete = "DELETE FROM questoes WHERE id = ?" 
            
            # 3. Execução: passando a tupla (id,)
            cursor.execute(sql_delete, (questao_id,))
            
            # 4. Confirmação da Transação
            conn.commit()
            
            # Verifica quantas linhas foram afetadas para confirmar a deleção
            if cursor.rowcount > 0:
                print(f"✅ Questão com ID {questao_id} deletada com sucesso.")
                return True
            else:
                print(f"⚠️ Nenhuma questão encontrada ou deletada com o ID {questao_id}.")
                return False

    except sqlite3.Error as e:
        print(f"❌ Erro ao deletar a questão ID {questao_id} no banco de dados: {e}")
        return False


def editar_questao_por_id(nome_do_banco: str, questao_id: int, updates: Dict[str, Any]) -> bool:
    """
    Atualiza um ou mais campos de uma questão específica no banco de dados.

    Parameters
    ----------
    nome_do_banco : str
        Nome do banco de dados (sem a extensão .db).
    questao_id : int
        O ID da questão a ser atualizada.
    updates : dict
        Um dicionário onde a chave é o nome da coluna (ex: 'dificuldade')
        e o valor é o novo dado (ex: 'Difícil').

    Returns
    -------
    bool
        True se a questão foi atualizada com sucesso, False caso contrário.
    """
    db_file = f'{nome_do_banco}.db'
    
    # 1. Preparação Dinâmica da Query SQL
    # Ex: 'dificuldade = ?, origem = ?'
    set_clauses = [f"{coluna} = ?" for coluna in updates.keys()]
    set_clause_str = ", ".join(set_clauses)
    
    # Valores a serem atualizados (na mesma ordem das colunas)
    update_values = list(updates.values())
    
    # A tupla final para a execução é: [valores dos updates] + [o ID da questão]
    sql_parameters = update_values + [questao_id]
    
    # 2. Instrução SQL completa
    sql_update = f"UPDATE questoes SET {set_clause_str} WHERE id = ?" 
    
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            
            # 3. Execução da Query
            cursor.execute(sql_update, sql_parameters)
            
            conn.commit()
            
            # 4. Verificação
            if cursor.rowcount > 0:
                print(f"✅ Questão com ID {questao_id} atualizada com sucesso. Campos alterados: {list(updates.keys())}")
                return True
            else:
                print(f"⚠️ Nenhuma questão encontrada ou alterada com o ID {questao_id}.")
                return False

    except sqlite3.Error as e:
        print(f"❌ Erro ao editar a questão ID {questao_id} no banco de dados: {e}")
        return False




