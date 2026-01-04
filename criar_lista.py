import sqlite3
from fpdf import FPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer



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



from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def create_pdf(questions, output_pdf_path):
    """
    Generates a PDF with a list of questions, including the label 'Questão' 
    before each question and a space between the title and question text.

    Parameters
    ----------
    questions : list of tuples
        A list of questions, where each question is a tuple.
    output_pdf_path : str
        Path where the output PDF file will be saved.
    """
    # Configure the PDF document with A4 page size
    doc = SimpleDocTemplate(output_pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Define a style for the "Questão" title
    title_style = ParagraphStyle(name="Title", fontSize=12, leading=14, spaceAfter=6)
    question_style = styles["BodyText"]  # Use a standard text style for the question text

    # Collect elements to add to the PDF
    elements = []

    for idx, question in enumerate(questions, 1):
        # Add the title "Questão {n}" as a paragraph
        title_text = f"<b>Questão {idx}</b>"
        title_paragraph = Paragraph(title_text, title_style)
        elements.append(title_paragraph)
        
        # Add the question text with automatic line breaks
        question_text = question[1]
        question_paragraph = Paragraph(question_text, question_style)
        elements.append(question_paragraph)

        # Add space after each question
        elements.append(Spacer(1, 12))  

    # Build the PDF
    doc.build(elements)
