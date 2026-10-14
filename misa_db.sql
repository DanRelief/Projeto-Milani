CREATE DATABASE IF NOT EXISTS misa;
USE misa;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    papel ENUM('student', 'teacher') NOT NULL, -- "student" (aluno) ou "teacher" (docente)
    identificador VARCHAR(100) UNIQUE NOT NULL, -- RA para alunos ou E-mail para docentes
    senha_hash VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);