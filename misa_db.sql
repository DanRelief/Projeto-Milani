CREATE DATABASE IF NOT EXISTS misa;
USE misa;

-- 1. Tabela de Usuários (com flag de primeiro acesso e identificador único)
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    papel ENUM('student', 'teacher') NOT NULL,
    identificador VARCHAR(100) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    primeiro_acesso BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Tabela de Animais (com relacionamento para o usuário responsável)
CREATE TABLE IF NOT EXISTS animais (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    nome VARCHAR(100) NOT NULL, 
    especie VARCHAR(100) NOT NULL, 
    idade INT NOT NULL, 
    porte ENUM('pequeno', 'medio', 'grande') NOT NULL, 
    procedimento VARCHAR(255) NOT NULL,
    estado_clinico ENUM('estavel', 'moderado', 'grave') NOT NULL,
    ultima_medicacao VARCHAR(100) DEFAULT NULL,
    quantidade VARCHAR(100) DEFAULT NULL,
    responsavel_aplicacao INT NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Chave Estrangeira apontando para o aluno/docente responsável
    CONSTRAINT fk_animais_responsavel 
        FOREIGN KEY (responsavel_aplicacao) 
        REFERENCES usuarios(id) 
        ON DELETE RESTRICT 
        ON UPDATE CASCADE
);