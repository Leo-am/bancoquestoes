# Banco de Questões

![Pylint Status](https://github.com/leo-am/bancoquestoes/actions/workflows/pylint.yml/badge.svg)

Este projeto tem como objetivo reunir questões de física em um banco de dados que permite a geração automática de listas de exercícios em \latex de acordo com a série, tema e nível de dificuldade.

No momento, o foco é adicionar ao banco de dados as questões da Olimpíada Brasileira de Física das Escolas Públicas.

Questões adicionadas:

 - OBFEP 2025 Primeira Fase Nível B
 - OBFEP 2024 Primeira Fase Nível B
 - OBFEP 2023 Primeira Fase Nível B
 - OBFEP 2022 Primeira Fase Nível B
 - OBFEP 2021 Primeira Fase Nível B

## Como utilizar

1. O usuário deve incluir os pdfs com as questões na pasta data/raw.
2. Na pasta data/processed, devem ser incluídos arquivos .csv, com o seguinte formato:
   |numero_questao|serie|origem|dificuldade|imagem|tema1|tema2|tema3|

Exemplo:
|numero_questao|serie|origem|dificuldade|imagem|tema1|tema2|tema3|
|1|Primeiro Ano|OBFEP_2025|7|../data/figuras/B.1|Cinemática|Movimento Retilíneo Uniforme|Velocidade Média|

3. O pacote extrai as questões dos arquivos pdf e as categoriza de acordo com os metadados dos arquivos .csv.
4. O pacote pode ser utilizado para criar listas personalizadas em pdf de acordo com a:
   * Série;
   * Temas;
   * Origem;
   * Tema.
