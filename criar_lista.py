import sqlite3
from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas



def fetch_questions(nome='banco_questoes.db', tema=None,
                    dificuldade=None, serie=None):
    """
    Busca questões no banco de dados 'banco_questoes.db' com base nos critérios fornecidos.

    Parameters
    ----------
    name : str
        String com o nome do banco de dados.
    tema : str, optional
        O tema ou assunto da questão para filtrar os resultados.
    dificuldade : str, optional
        O nível de dificuldade da questão para filtrar os resultados.
    serie : str, optional
        A série ou nível de ensino da questão para filtrar os resultados.

    Returns
    -------
    list of tuples
        Uma lista contendo as questões que correspondem aos critérios de pesquisa. 
        Cada item é uma tupla representando uma questão.

    Notes
    -----
    - Se nenhum parâmetro for fornecido, a função retornará todas as questões.
    - Cada questão retornada contém as colunas da tabela: ID, texto, tema, dificuldade e série.

    Example
    -------
    >>> fetch_questions(tema="Física", dificuldade="Fácil", serie="1º ano")
    Retorna todas as questões de Física, com dificuldade "Fácil" para o "1º ano".
    """
    conn = sqlite3.connect(f'{nome}.db')
    cursor = conn.cursor()
    query = "SELECT * FROM questoes WHERE 1=1"
    if tema:
        query += f" AND tema='{tema}'"
    if dificuldade:
        query += f" AND dificuldade='{dificuldade}'"
    if serie:
        query += f" AND serie='{serie}'"
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results



# def create_pdf(questions, output_pdf_path):
#     """
#     Generates a PDF with a list of questions, supporting Unicode characters.

#     Parameters
#     ----------
#     questions : list of tuples
#         A list of questions, where each question is a tuple.
#     output_pdf_path : str
#         Path where the output PDF file will be saved.

#     """
#     pdf = FPDF()
#     pdf.set_auto_page_break(auto=True, margin=15)
#     pdf.add_page()

#     # Use a standard font that supports Unicode in fpdf2
#     pdf.set_font("Arial", size=12)

#     for idx, question in enumerate(questions, 1):
#         pdf.multi_cell(0, 10, f"Q{idx}. {question[1]}")
#         pdf.ln()

#     pdf.output(output_pdf_path)



def create_pdf(questions, output_pdf_path):
    """
    Generates a PDF with a list of questions, supporting Unicode characters.

    Parameters
    ----------
    questions : list of tuples
        A list of questions, where each question is a tuple.
    output_pdf_path : str
        Path where the output PDF file will be saved.
    """
    c = canvas.Canvas(output_pdf_path, pagesize=letter)
    width, height = letter
    c.setFont("Helvetica", 12)
    y = height - 40  # Start from the top of the page

    for idx, question in enumerate(questions, 1):
        lines = question[1].split("\n")
        # Draw the question number before the lines
        c.drawString(40, y, f"Q{idx}. {lines[0]}")
        y -= 20  # Move down for the next line
        
        # Draw the remaining lines of the question
        for line in lines[1:]:
            c.drawString(40, y, line)
            y -= 20  # Move down for the next line

        y -= 10  # Extra space between questions

        # Check if we are nearing the bottom of the page
        if y < 40:
            c.showPage()  # Start a new page
            c.setFont("Helvetica", 12)
            y = height - 40  # Reset Y position

    c.save()
