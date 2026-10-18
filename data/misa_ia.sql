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

#ALTER TABLE animais 
#ADD COLUMN observacao_docente TEXT DEFAULT NULL AFTER quantidade;

-- 3. Sessões de monitoramento
CREATE TABLE IF NOT EXISTS sessoes_monitoramento (
    id VARCHAR(36) PRIMARY KEY,

    animal_id INT NOT NULL,
    iniciado_por INT NOT NULL,

    data_hora_inicio DATETIME(6) NOT NULL,
    data_hora_fim DATETIME(6) DEFAULT NULL,

    status ENUM(
        'ativa',
        'encerrada',
        'cancelada'
    ) NOT NULL DEFAULT 'ativa',

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_sessao_animal
        FOREIGN KEY (animal_id)
        REFERENCES animais(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,

    CONSTRAINT fk_sessao_usuario
        FOREIGN KEY (iniciado_por)
        REFERENCES usuarios(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- 4. Smedições dos sinais vitais dos animais
CREATE TABLE IF NOT EXISTS medicoes_sinais_vitais (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    sessao_id VARCHAR(36) NOT NULL,

    data_hora DATETIME(6) NOT NULL,

    parametro VARCHAR(50) NOT NULL,

    valor DOUBLE NOT NULL,
    unidade VARCHAR(20) NOT NULL,

    fonte VARCHAR(30) NOT NULL,

    qualidade_sinal DOUBLE DEFAULT NULL,

    valida BOOLEAN NOT NULL DEFAULT TRUE,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_medicao_sessao
        FOREIGN KEY (sessao_id)
        REFERENCES sessoes_monitoramento(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    INDEX idx_medicao_sessao_parametro_data (
        sessao_id,
        parametro,
        data_hora
    )
);
-- 5. Eventos e alertas de mudanças 
CREATE TABLE IF NOT EXISTS eventos_alerta (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,

    id_alerta VARCHAR(36) NOT NULL,

    sessao_id VARCHAR(36) NOT NULL,

    tipo_evento ENUM(
        'abertura',
        'encerramento'
    ) NOT NULL,

    parametro VARCHAR(50) NOT NULL,

    data_hora DATETIME(6) NOT NULL,

    estado_monitoramento VARCHAR(30) NOT NULL,

    valor_atual DOUBLE NOT NULL,

    z_robusto DOUBLE DEFAULT NULL,

    ewma DOUBLE DEFAULT NULL,

    inclinacao DOUBLE DEFAULT NULL,

    qualidade_sinal DOUBLE DEFAULT NULL,

    motivo TEXT DEFAULT NULL,

    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_evento_alerta_sessao
        FOREIGN KEY (sessao_id)
        REFERENCES sessoes_monitoramento(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    INDEX idx_evento_alerta_id (
        id_alerta
    ),

    INDEX idx_evento_alerta_sessao_data (
        sessao_id,
        data_hora
    )
);

-- 1. Histórico Permanente de Procedimentos
CREATE TABLE IF NOT EXISTS historico_procedimentos (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    realizado_por INT NOT NULL, -- ID do aluno/docente que realizou
    procedimento VARCHAR(255) NOT NULL,
    descricao_detalhada TEXT DEFAULT NULL,
    data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_proc_animal 
        FOREIGN KEY (animal_id) REFERENCES animais(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_proc_usuario 
        FOREIGN KEY (realizado_por) REFERENCES usuarios(id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_proc_animal_data (animal_id, data_hora)
);

-- 2. Histórico Permanente de Medicações Administradas
CREATE TABLE IF NOT EXISTS historico_medicacoes (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    animal_id INT NOT NULL,
    administrado_por INT NOT NULL, -- ID do aluno/docente que aplicou
    medicamento VARCHAR(100) NOT NULL,
    dose_quantidade VARCHAR(100) NOT NULL,
    via_administracao VARCHAR(50) DEFAULT NULL, -- Ex: IV, IM, SC, Oral
    observacao TEXT DEFAULT NULL,
    data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_med_animal 
        FOREIGN KEY (animal_id) REFERENCES animais(id) 
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_med_usuario 
        FOREIGN KEY (administrado_por) REFERENCES usuarios(id) 
        ON DELETE RESTRICT ON UPDATE CASCADE,

    INDEX idx_med_animal_data (animal_id, data_hora)
);