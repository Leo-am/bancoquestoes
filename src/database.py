"""Módulo que contém todas as funções/classes para criar
o banco de dados de questões."""

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.extrator import extract_questions_from_pdf
from src.modelos import Questao


def create_database(nome_do_banco: str):
    """
    Cria o banco de dados SQLite na pasta correta: data/database/

    Parameters:
    -----------
    nome_do_banco : str
        O nome do banco de dados a ser criado (sem a extensão .db).

    Returns:
    --------
    None
    """
    # 1. Localiza a raiz do projeto (assumindo que este arquivo está em src/)
    # .parent é 'src', .parent.parent é a raiz 'bancodequestoes'
    raiz_projeto = Path(__file__).resolve().parent.parent

    # 2. Define o caminho completo para a pasta do banco
    pasta_db = raiz_projeto / "data" / "database"

    # 3. Garante que a pasta existe (cria se não existir)
    pasta_db.mkdir(parents=True, exist_ok=True)

    # 4. Define o caminho final do arquivo .db
    caminho_final_db = pasta_db / f"{nome_do_banco}.db"

    # 5. Conecta (o SQLite criará o arquivo no caminho absoluto especificado)
    try:
        conn = sqlite3.connect(str(caminho_final_db))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                texto TEXT NOT NULL,
                serie TEXT,
                origem TEXT,
                dificuldade TEXT,
                imagem TEXT,
                temas TEXT
            )
        """
        )
        conn.commit()
        conn.close()
        print(f"✅ Banco de dados criado/verificado em: {caminho_final_db}")
    except Exception as e:
        print(f"❌ Erro ao criar o banco de dados: {e}")


# Para garantir que a inserção também use o caminho correto:
def get_db_path(nome_do_banco: str) -> Path:
    """
    Retorna o caminho completo para o arquivo do banco de dados.

    Parameters
    ----------
    nome_do_banco : str
        Nome do banco de dados (sem a extensão .db).

    Returns
    -------
    Path
        O caminho completo para o arquivo do banco de dados.
    """
    raiz = Path(__file__).resolve().parent.parent
    return raiz / "data" / "database" / f"{nome_do_banco}.db"


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
        with sqlite3.connect(f"{banco}.db") as conn:
            cursor = conn.cursor()

            # A ordem dos campos aqui DEVE CORRESPONDER à ordem da tupla gerada
            # por questao.to_tuple()
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


def checar_questoes_inseridas(
    nome_do_banco: str, nome_da_tabela: str = "questoes", limite: int = 10
) -> List[Tuple]:
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
    db_file = f"{nome_do_banco}.db"

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
                    if nomes_colunas[i] == "texto":
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
    db_file = f"{nome_do_banco}.db"

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
                print(
                    f"⚠️ Nenhuma questão encontrada ou deletada com o ID {questao_id}."
                )
                return False

    except sqlite3.Error as e:
        print(f"❌ Erro ao deletar a questão ID {questao_id} no banco de dados: {e}")
        return False


def editar_questao_por_id(
    nome_do_banco: str, questao_id: int, updates: Dict[str, Any]
) -> bool:
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
    db_file = f"{nome_do_banco}.db"

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
                print(
                    f"✅ Questão com ID {questao_id} atualizada com sucesso. Campos alterados: {list(updates.keys())}"
                )
                return True
            else:
                print(
                    f"⚠️ Nenhuma questão encontrada ou alterada com o ID {questao_id}."
                )
                return False

    except sqlite3.Error as e:
        print(f"❌ Erro ao editar a questão ID {questao_id} no banco de dados: {e}")
        return False


def popular_banco_com_classificacao(
    banco_nome: str, pdf_path: str, csv_path: str, pdf_delimiter: str = "Q."
) -> None:
    """
    Lê questões de um PDF e metadados de um CSV, mapeia os dados
    e insere as questões classificadas no banco de dados.

    Parameters
    ----------
    banco_nome : str
        Nome do banco de dados (ex: 'meu_banco_questoes').
    pdf_path : str
        Caminho para o arquivo PDF contendo os textos das questões.
    csv_path : str
        Caminho para o arquivo CSV contendo os metadados de classificação.
    pdf_delimiter : str
        Delimitador usado no PDF para iniciar uma nova questão (ex: "Q.").

    Returns
    -------
    None
    """

    print("--- INICIANDO FLUXO DE MAPEAMENTO E INSERÇÃO (CSV + PDF) ---")

    # --- 1. Leitura e Preparação dos Metadados (CSV) ---
    try:
        # Carrega o CSV usando Pandas para fácil manipulação
        df = pd.read_csv(csv_path)

        # O cabeçalho deve ser:
        # número_questao, serie, origem, dificuldade, imagem, tema1, tema2, tema3

        # Cria um dicionário de metadados, usando o número da questão como chave
        # Isso permite o mapeamento rápido com o índice do PDF
        metadata_map: Dict[int, Dict[str, Any]] = {}

        for index, row in df.iterrows():
            # A chave de mapeamento deve ser o número da questão
            try:
                # O número da questão no CSV (que deve ser 1, 2, 3...)
                num_questao = int(row["numero_questao"])
            except ValueError:
                print(
                    f"⚠️ Aviso: 'numero_questao' inválido na linha {index + 2} do CSV."
                    f"Ignorando linha."
                )
                continue

            # Constrói a lista de temas (ignorando células vazias/NaN)
            temas = [
                str(t)
                for t in [row["tema1"], row["tema2"], row["tema3"]]
                if pd.notna(t) and str(t).strip() and str(t).lower() != "none"
            ]

            # Armazena os metadados
            metadata_map[num_questao] = {
                "serie": row.get("serie"),
                "origem": row.get("origem"),
                "dificuldade": row.get("dificuldade"),
                "imagem_path": row.get("imagem"),
                "temas": temas,
            }

        print(f"✅ CSV Lido: {len(metadata_map)} metadados prontos para mapeamento.")

    except FileNotFoundError:
        print(f"❌ Erro: Arquivo CSV '{csv_path}' não encontrado.")
        return
    except KeyError as e:
        print(
            f"❌ Erro de coluna: Verifique se o CSV tem o cabeçalho correto, faltando a coluna {e}."
        )
        return

    # --- 2. Leitura dos Textos das Questões (PDF) ---
    textos_questoes: List[str] = extract_questions_from_pdf(pdf_path, pdf_delimiter)

    if not textos_questoes:
        print(f"❌ Erro: Não foi possível extrair questões do PDF '{pdf_path}'.")
        return

    print(f"✅ PDF Lido: {len(textos_questoes)} textos de questões extraídos.")

    # --- 3. Mapeamento, Criação de Objeto e Inserção no Banco ---

    total_inserido = 0

    # Iteração sobre a lista de textos. O índice (i) + 1 é o número da questão.
    for i, texto_questao in enumerate(textos_questoes):
        num_questao = i + 1  # Questão 1, 2, 3...

        # Pula a inserção se o metadado não existir para esta questão
        # (ex: se o CSV for menor que o PDF)
        if num_questao not in metadata_map:
            print(
                f"⚠️ Aviso: Questão {num_questao} do PDF não tem metadados no CSV. Pulando."
            )
            continue

        metadata = metadata_map[num_questao]

        try:
            # Criação do objeto Questao com os dados completos
            nova_questao = Questao(
                texto=texto_questao.strip(),  # Limpa o texto
                serie=metadata.get("serie", "N/A"),
                origem=metadata.get("origem", "PDF"),
                dificuldade=metadata.get("dificuldade", "N/A"),
                imagem_path=metadata.get("imagem_path"),
                temas=metadata.get("temas"),
            )

            # 4. Inserção no banco de dados
            insert_question(banco_nome, nova_questao)
            total_inserido += 1

        except Exception as e:
            print(f"❌ Erro ao processar/inserir Questão {num_questao}: {e}")

    print(
        f"\n--- FLUXO CONCLUÍDO. Total de {total_inserido} questões inseridas/atualizadas. ---"
    )


def buscar_questao_por_id(nome_do_banco: str, questao_id: int) -> Optional[Dict]:
    """
    Busca uma questão no banco de dados pelo seu ID e retorna os dados como um dicionário.

    Parameters:
    -----------
    nome_do_banco : str
        O nome do banco de dados a ser utilizado (sem a extensão .db).
    questao_id : int
        O ID da questão a ser buscada.

    Returns:
    --------
    Optional[Dict]
        Um dicionário com os dados da questão, ou None se não encontrada.
    """
    db_file = f"{nome_do_banco}.db"

    try:
        with sqlite3.connect(db_file) as conn:
            # Garante que as linhas sejam retornadas como objetos acessíveis por nome da coluna
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Seleciona todos os campos
            cursor.execute("SELECT * FROM questoes WHERE id = ?", (questao_id,))

            registro = cursor.fetchone()

            if registro:
                # Converte o objeto Row para um dicionário padrão
                return dict(registro)
            else:
                return None

    except sqlite3.Error as e:
        print(f"❌ Erro ao buscar questão no banco de dados: {e}")
        return None


def limpar_para_latex(texto: str) -> str:
    if not texto:
        return ""

    # 1. PADRONIZAÇÃO INICIAL (Símbolos Gregos e Graus)
    # Removido o \ohm daqui para tratar no dicionário de gregas
    texto = texto.replace("°C", r"\celsius")
    texto = texto.replace("°", r"\degree")

    gregas = {"μ": r"\textmu ", "π": r"\textpi ", "Δ": r"\textDelta ", "Ω": r"\ohm "}
    for k, v in gregas.items():
        texto = texto.replace(k, v)

    # 2. TRATAMENTO DE QUANTIDADES (Incluindo o %)
    # Adicionei '%' na lista de unidades capturadas pela Regex
    padrao_qty = (
        r"(\d+[,.]?\d*(?:\s*[xX·*]\s*10\^?[-]?\d+)?)\s*([a-zA-Z\\%]+(?:\^?-?\d+)?)"
    )

    def substituir_qty(m):
        valor_bruto = m.group(1).replace(",", ".")
        valor_limpo = re.sub(r"\s*[xX·*]\s*10\^?", "e", valor_bruto)

        unidade = m.group(2)
        # Se a unidade for o símbolo %, trocamos pelo comando percent do siunitx
        if unidade == "%":
            unidade = r"\percent"

        if "^" in unidade and "{" not in unidade:
            unidade = unidade.replace("^", "^{") + "}"

        return rf"\qty{{{valor_limpo}}}{{{unidade}}}"

    texto = re.sub(padrao_qty, substituir_qty, texto)

    # 3. ESCAPAR CARACTERES RESERVADOS (Apenas o que sobrou fora do \qty)
    # Usamos lookbehind (?<!\\) para não escapar o que já tem barra (ex: \celsius)
    reservados = ["%", "_", "&", "#", "{", "}"]
    for char in reservados:
        # Escapa apenas se não houver uma barra invertida antes
        texto = re.sub(rf"(?<!\\){re.escape(char)}", rf"\\{char}", texto)

    # 4. CASOS SOLTOS (Unidades sem número)
    unidades_soltas = {
        r"\celsius": r"\unit{\celsius}",
        r"\degree": r"\unit{\degree}",
        r"\ohm": r"\unit{\ohm}",
        r"\%": r"\unit{\percent}",  # Caso o % tenha sobrado isolado
    }
    for k, v in unidades_soltas.items():
        if k in texto and v not in texto:  # Evita duplicar \unit{\unit{...}}
            texto = texto.replace(k, v)

    return texto


def exportar_db_para_csv(db_path, csv_path):
    """
    Exporta o conteúdo do banco de dados para um arquivo CSV.

    Parameters:
    -----------
    db_path : str
        O caminho para o arquivo do banco de dados (ex: "data/database/questoes.db").
    csv_path : str
        O caminho para o arquivo CSV de saída (ex: "outputs/questoes.csv").

    Returns:
    --------
    None
    """
    # 1. Conecta ao banco
    conn = sqlite3.connect(db_path)

    # 2. Lê a tabela inteira para um DataFrame
    df = pd.read_sql_query("SELECT * FROM questoes", conn)

    # 3. Remove a coluna 'texto' (se ela existir)
    if "texto" in df.columns:
        df = df.drop(columns=["texto"])

    # 4. Exporta para CSV
    # index=False evita que o Pandas crie uma coluna de números extras
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    conn.close()
    print(f"Exportação concluída: {csv_path}")
