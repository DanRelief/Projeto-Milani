
ALTER TABLE historico_procedimentos
ADD COLUMN sessao_id VARCHAR(36) NULL
AFTER animal_id;

ALTER TABLE historico_procedimentos
ADD COLUMN registrado_por INT NULL
AFTER realizado_por;

UPDATE historico_procedimentos
SET registrado_por = realizado_por
WHERE registrado_por IS NULL;

ALTER TABLE historico_procedimentos
MODIFY COLUMN registrado_por INT NOT NULL;

ALTER TABLE historico_procedimentos
ADD CONSTRAINT fk_hist_proc_sessao
FOREIGN KEY (sessao_id)
REFERENCES sessoes_monitoramento(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

ALTER TABLE historico_procedimentos
ADD CONSTRAINT fk_hist_proc_registrador
FOREIGN KEY (registrado_por)
REFERENCES usuarios(id)
ON DELETE RESTRICT
ON UPDATE CASCADE;

CREATE INDEX idx_hist_proc_sessao_data
ON historico_procedimentos (sessao_id, data_hora);


ALTER TABLE historico_medicacoes
ADD COLUMN sessao_id VARCHAR(36) NULL
AFTER animal_id;

ALTER TABLE historico_medicacoes
ADD COLUMN registrado_por INT NULL
AFTER administrado_por;

ALTER TABLE historico_medicacoes
ADD COLUMN quantidade DOUBLE NULL
AFTER medicamento;

ALTER TABLE historico_medicacoes
ADD COLUMN unidade VARCHAR(30) NULL
AFTER quantidade;

UPDATE historico_medicacoes
SET registrado_por = administrado_por
WHERE registrado_por IS NULL;

ALTER TABLE historico_medicacoes
MODIFY COLUMN registrado_por INT NOT NULL;

ALTER TABLE historico_medicacoes
ADD CONSTRAINT fk_hist_med_sessao
FOREIGN KEY (sessao_id)
REFERENCES sessoes_monitoramento(id)
ON DELETE SET NULL
ON UPDATE CASCADE;

ALTER TABLE historico_medicacoes
ADD CONSTRAINT fk_hist_med_registrador
FOREIGN KEY (registrado_por)
REFERENCES usuarios(id)
ON DELETE RESTRICT
ON UPDATE CASCADE;

CREATE INDEX idx_hist_med_sessao_data
ON historico_medicacoes (sessao_id, data_hora);



CREATE INDEX idx_sessao_animal_inicio
ON sessoes_monitoramento (animal_id, data_hora_inicio);


