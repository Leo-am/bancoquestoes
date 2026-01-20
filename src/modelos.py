"""Módulo que contém todas as classes para criar
o banco de dados de questões."""

from typing import Any, Dict, List, Optional, Tuple


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
        temas: Optional[List[str]] = None,
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
            temas_str,
        )
