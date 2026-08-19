-- ============================================================
-- Script de criacao do schema MySQL - Projeto Bolsistas
-- Gerado a partir dos models Django em 19/08/2026
-- ============================================================
-- Mapeamento de tipos:
--   Django AutoField       -> BIGINT AUTO_INCREMENT
--   Django CharField       -> VARCHAR(n)
--   Django TextField       -> TEXT / LONGTEXT
--   Django EmailField      -> VARCHAR(254)
--   Django BooleanField    -> TINYINT(1)
--   Django DateField       -> DATE
--   Django DateTimeField   -> DATETIME(6)
--   Django IntegerField    -> INT
--   Django PositiveIntegerField -> INT UNSIGNED
--   Django DecimalField    -> DECIMAL(max_digits, decimal_places)
--   Django FileField       -> VARCHAR(100)
--   Django ImageField      -> VARCHAR(100)
--   Django OneToOneField   -> FK + UNIQUE
--   Django ForeignKey      -> FK + INDEX
-- ============================================================

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;


-- ============================================================
-- 1. DJANGO INTERNALS (auth, contenttypes, sessions, admin)
-- ============================================================

CREATE TABLE IF NOT EXISTS `django_content_type` (
    `id`         INT          NOT NULL AUTO_INCREMENT,
    `app_label`  VARCHAR(100) NOT NULL,
    `model`      VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_content_type_app_model` (`app_label`, `model`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS `auth_permission` (
    `id`               INT          NOT NULL AUTO_INCREMENT,
    `name`             VARCHAR(255) NOT NULL,
    `content_type_id`  INT          NOT NULL,
    `codename`         VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_permission_ct_codename` (`content_type_id`, `codename`),
    CONSTRAINT `fk_permission_content_type`
        FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS `auth_group` (
    `id`   INT          NOT NULL AUTO_INCREMENT,
    `name` VARCHAR(150) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_group_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS `auth_group_permissions` (
    `id`            BIGINT NOT NULL AUTO_INCREMENT,
    `group_id`      INT    NOT NULL,
    `permission_id` INT    NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_group_permission` (`group_id`, `permission_id`),
    CONSTRAINT `fk_agp_group`      FOREIGN KEY (`group_id`)      REFERENCES `auth_group`      (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_agp_permission` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS `django_session` (
    `session_key`  VARCHAR(40)  NOT NULL,
    `session_data` LONGTEXT     NOT NULL,
    `expire_date`  DATETIME(6)  NOT NULL,
    PRIMARY KEY (`session_key`),
    KEY `idx_session_expire` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS `django_admin_log` (
    `id`               BIGINT       NOT NULL AUTO_INCREMENT,
    `action_time`      DATETIME(6)  NOT NULL,
    `object_id`        LONGTEXT     NULL,
    `object_repr`      VARCHAR(200) NOT NULL,
    `action_flag`      SMALLINT UNSIGNED NOT NULL,
    `change_message`   LONGTEXT     NOT NULL,
    `content_type_id`  INT          NULL,
    `user_id`          BIGINT       NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_admin_log_user` (`user_id`),
    KEY `idx_admin_log_ct`   (`content_type_id`),
    CONSTRAINT `fk_admin_log_ct`   FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`) ON DELETE SET NULL
    -- FK para accounts_user adicionada apos criacao dessa tabela
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 2. ACCOUNTS — User (AbstractUser, sem username)
-- ============================================================

CREATE TABLE IF NOT EXISTS `accounts_user` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT,
    `password`      VARCHAR(128) NOT NULL,
    `last_login`    DATETIME(6)  NULL,
    `is_superuser`  TINYINT(1)   NOT NULL DEFAULT 0,
    `email`         VARCHAR(254) NOT NULL,
    `nome_completo` VARCHAR(255) NOT NULL,
    `is_staff`      TINYINT(1)   NOT NULL DEFAULT 0,
    `is_active`     TINYINT(1)   NOT NULL DEFAULT 1,
    `date_joined`   DATETIME(6)  NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- FK do django_admin_log -> accounts_user (deferida)
ALTER TABLE `django_admin_log`
    ADD CONSTRAINT `fk_admin_log_user`
        FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`);


CREATE TABLE IF NOT EXISTS `accounts_user_groups` (
    `id`       BIGINT NOT NULL AUTO_INCREMENT,
    `user_id`  BIGINT NOT NULL,
    `group_id` INT    NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_group` (`user_id`, `group_id`),
    CONSTRAINT `fk_aug_user`  FOREIGN KEY (`user_id`)  REFERENCES `accounts_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_aug_group` FOREIGN KEY (`group_id`) REFERENCES `auth_group`   (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS `accounts_user_user_permissions` (
    `id`            BIGINT NOT NULL AUTO_INCREMENT,
    `user_id`       BIGINT NOT NULL,
    `permission_id` INT    NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_user_permission` (`user_id`, `permission_id`),
    CONSTRAINT `fk_uup_user`       FOREIGN KEY (`user_id`)       REFERENCES `accounts_user`   (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_uup_permission` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 3. ACCOUNTS — Perfil
-- ============================================================

CREATE TABLE IF NOT EXISTS `accounts_perfil` (
    `id`              BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at`      DATETIME(6)  NOT NULL,
    `updated_at`      DATETIME(6)  NOT NULL,
    `user_id`         BIGINT       NOT NULL,
    `telefone`        VARCHAR(20)  NOT NULL DEFAULT '',
    `unidade`         VARCHAR(255) NOT NULL DEFAULT '',
    `data_nascimento` DATE         NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_perfil_user` (`user_id`),
    CONSTRAINT `fk_perfil_user` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 4. ACCOUNTS — DocumentoExterno
-- ============================================================

CREATE TABLE IF NOT EXISTS `accounts_documentoexterno` (
    `id`         BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at` DATETIME(6)  NOT NULL,
    `updated_at` DATETIME(6)  NOT NULL,
    `user_id`    BIGINT       NOT NULL,
    `arquivo`    VARCHAR(100) NOT NULL,
    `tipo`       VARCHAR(10)  NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_docext_user` (`user_id`),
    CONSTRAINT `fk_docext_user` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 5. CADASTRO — CadastroBolsista
-- ============================================================

CREATE TABLE IF NOT EXISTS `cadastro_cadatrobolsista` (
    `id`                                 BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at`                         DATETIME(6)  NOT NULL,
    `updated_at`                         DATETIME(6)  NOT NULL,
    `user_id`                            BIGINT       NOT NULL,
    `numero_serie`                       VARCHAR(4)   NOT NULL,
    `telefone`                           VARCHAR(20)  NOT NULL DEFAULT '',
    `data_nascimento`                    DATE         NOT NULL,
    `rua`                                VARCHAR(255) NOT NULL DEFAULT '',
    `numero`                             VARCHAR(20)  NOT NULL DEFAULT '',
    `bairro`                             VARCHAR(255) NOT NULL DEFAULT '',
    `cidade`                             VARCHAR(255) NOT NULL DEFAULT '',
    `estado`                             VARCHAR(2)   NOT NULL DEFAULT '',
    `curriculo`                          VARCHAR(100) NOT NULL DEFAULT '',
    `foto`                               VARCHAR(100) NOT NULL DEFAULT '',
    `participacao_projetos_anos`         INT UNSIGNED NOT NULL DEFAULT 0,
    `participacao_congressos`            TINYINT(1)   NOT NULL DEFAULT 0,
    `resumo_anais`                       TINYINT(1)   NOT NULL DEFAULT 0,
    `artigo_completo_anais`              TINYINT(1)   NOT NULL DEFAULT 0,
    `artigo_cientifico_nacional`         TINYINT(1)   NOT NULL DEFAULT 0,
    `artigo_cientifico_internacional`    TINYINT(1)   NOT NULL DEFAULT 0,
    `livro_patente`                      TINYINT(1)   NOT NULL DEFAULT 0,
    `participacao_minicurso`             TINYINT(1)   NOT NULL DEFAULT 0,
    `treinamento`                        TINYINT(1)   NOT NULL DEFAULT 0,
    `pontuacao_previa`                   DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_cadbol_user`         (`user_id`),
    UNIQUE KEY `uq_cadbol_numero_serie` (`numero_serie`),
    CONSTRAINT `fk_cadbol_user` FOREIGN KEY (`user_id`) REFERENCES `accounts_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 6. CADASTRO — FormacaoAcademica
-- ============================================================

CREATE TABLE IF NOT EXISTS `cadastro_formacaoacademica` (
    `id`            BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at`    DATETIME(6)  NOT NULL,
    `updated_at`    DATETIME(6)  NOT NULL,
    `bolsista_id`   BIGINT       NOT NULL,
    `tipo`          VARCHAR(20)  NOT NULL,
    `status`        VARCHAR(20)  NOT NULL DEFAULT '',
    `instituicao`   VARCHAR(255) NOT NULL DEFAULT '',
    `curso`         VARCHAR(255) NOT NULL DEFAULT '',
    `area`          VARCHAR(255) NOT NULL DEFAULT '',
    `ano_conclusao` INT          NULL,
    PRIMARY KEY (`id`),
    KEY `idx_form_bolsista` (`bolsista_id`),
    CONSTRAINT `fk_form_bolsista` FOREIGN KEY (`bolsista_id`) REFERENCES `cadastro_cadatrobolsista` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 7. CADASTRO — ExperienciaProfissional
-- ============================================================

CREATE TABLE IF NOT EXISTS `cadastro_experienciaprofissional` (
    `id`               BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at`       DATETIME(6)  NOT NULL,
    `updated_at`       DATETIME(6)  NOT NULL,
    `bolsista_id`      BIGINT       NOT NULL,
    `area_atuacao`     VARCHAR(255) NOT NULL DEFAULT '',
    `anos_experiencia` INT UNSIGNED NOT NULL DEFAULT 0,
    `anexo`            VARCHAR(100) NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    KEY `idx_exp_bolsista` (`bolsista_id`),
    CONSTRAINT `fk_exp_bolsista` FOREIGN KEY (`bolsista_id`) REFERENCES `cadastro_cadatrobolsista` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 8. CADASTRO — AnexoComprobatorio
-- ============================================================

CREATE TABLE IF NOT EXISTS `cadastro_anexocomprobatorio` (
    `id`          BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at`  DATETIME(6)  NOT NULL,
    `updated_at`  DATETIME(6)  NOT NULL,
    `bolsista_id` BIGINT       NOT NULL,
    `tipo`        VARCHAR(40)  NOT NULL,
    `anexo`       VARCHAR(100) NOT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_anexo_bolsista` (`bolsista_id`),
    CONSTRAINT `fk_anexo_bolsista` FOREIGN KEY (`bolsista_id`) REFERENCES `cadastro_cadatrobolsista` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 9. CADASTRO — SolicitacaoEdicao
-- ============================================================

CREATE TABLE IF NOT EXISTS `cadastro_solicitacaoedicao` (
    `id`               BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at`       DATETIME(6)  NOT NULL,
    `updated_at`       DATETIME(6)  NOT NULL,
    `bolsista_id`      BIGINT       NOT NULL,
    `campo`            VARCHAR(100) NOT NULL,
    `valor_original`   TEXT         NOT NULL,
    `valor_novo`       TEXT         NOT NULL,
    `status`           VARCHAR(20)  NOT NULL DEFAULT 'pendente',
    `revisado_por_id`  BIGINT       NULL,
    `data_revisao`     DATETIME(6)  NULL,
    PRIMARY KEY (`id`),
    KEY `idx_sol_bolsista` (`bolsista_id`),
    KEY `idx_sol_status`  (`status`),
    CONSTRAINT `fk_sol_bolsista`     FOREIGN KEY (`bolsista_id`)     REFERENCES `cadastro_cadatrobolsista` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_sol_revisado_por` FOREIGN KEY (`revisado_por_id`) REFERENCES `accounts_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 10. EDITAIS — EditalProvisorio
-- ============================================================

CREATE TABLE IF NOT EXISTS `editais_editalprovisorio` (
    `id`                           BIGINT        NOT NULL AUTO_INCREMENT,
    `created_at`                   DATETIME(6)   NOT NULL,
    `updated_at`                   DATETIME(6)   NOT NULL,
    `nome_edital`                  VARCHAR(255)  NOT NULL DEFAULT '',
    `area_estudo`                  VARCHAR(255)  NOT NULL DEFAULT '',
    `detalhes_edital`              TEXT          NOT NULL,
    `nome_instituto`               VARCHAR(255)  NOT NULL,
    `email_solicitante`            VARCHAR(254)  NOT NULL,
    `telefone`                     VARCHAR(20)   NOT NULL,
    `endereco`                     TEXT          NOT NULL,
    `documento_anexo`              VARCHAR(100)  NOT NULL DEFAULT '',
    `numero_vagas`                 INT UNSIGNED  NOT NULL,
    `modalidade_bolsa`             VARCHAR(50)   NOT NULL,
    `experiencia`                  VARCHAR(50)   NOT NULL DEFAULT '',
    `valor_bolsa`                  DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `valor_total_bolsa`            DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    `valor_minimo`                 DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `valor_maximo`                 DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `modalidade_atuacao`           VARCHAR(50)   NOT NULL DEFAULT 'presencial',
    `plataforma_tecnologica`       VARCHAR(255)  NOT NULL,
    `vigencia`                     INT UNSIGNED  NOT NULL DEFAULT 180,
    `endereco_atuacao`             TEXT          NOT NULL,
    `qualificacao_minima`          VARCHAR(255)  NOT NULL,
    `detalhes_qualificacao_minima` VARCHAR(255)  NOT NULL DEFAULT '',
    `conhecimento_desejavel`       TEXT          NOT NULL,
    `conteudo_prova_teorica`       TEXT          NOT NULL,
    `modalidade_entrevista`        VARCHAR(20)   NOT NULL DEFAULT 'presencial',
    `criterios_desempate`          TEXT          NOT NULL,
    `comentarios`                  TEXT          NOT NULL,
    `numero_serie`                 VARCHAR(4)    NOT NULL,
    `status`                       VARCHAR(20)   NOT NULL DEFAULT 'em_analise',
    `criado_por_id`                BIGINT        NOT NULL,
    `responsavel_id`               BIGINT        NULL,
    `deleted_at`                   DATETIME(6)   NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_edital_numero_serie` (`numero_serie`),
    KEY `idx_edital_status`    (`status`),
    KEY `idx_edital_criado_por` (`criado_por_id`),
    KEY `idx_edital_deleted`   (`deleted_at`),
    CONSTRAINT `fk_edital_criado_por`  FOREIGN KEY (`criado_por_id`)  REFERENCES `accounts_user` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_edital_responsavel` FOREIGN KEY (`responsavel_id`) REFERENCES `accounts_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 11. EDITAIS — CronogramaEvento
-- ============================================================

CREATE TABLE IF NOT EXISTS `editais_cronogramaevento` (
    `id`         BIGINT      NOT NULL AUTO_INCREMENT,
    `created_at` DATETIME(6) NOT NULL,
    `updated_at` DATETIME(6) NOT NULL,
    `edital_id`  BIGINT      NOT NULL,
    `evento`     VARCHAR(50) NOT NULL,
    `data_evento` DATE       NOT NULL,
    `observacao` TEXT        NOT NULL,
    `ordem`      INT UNSIGNED NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    KEY `idx_cronograma_edital` (`edital_id`),
    KEY `idx_cronograma_ordem`  (`edital_id`, `ordem`),
    CONSTRAINT `fk_cronograma_edital` FOREIGN KEY (`edital_id`) REFERENCES `editais_editalprovisorio` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 12. EDITAIS — AplicacaoEdital
-- ============================================================

CREATE TABLE IF NOT EXISTS `editais_aplicacaoedital` (
    `id`                  BIGINT        NOT NULL AUTO_INCREMENT,
    `created_at`          DATETIME(6)   NOT NULL,
    `updated_at`          DATETIME(6)   NOT NULL,
    `bolsista_id`         BIGINT        NOT NULL,
    `edital_id`           BIGINT        NOT NULL,
    `numero_inscricao`    VARCHAR(10)   NOT NULL,
    `status`              VARCHAR(20)   NOT NULL DEFAULT 'pendente',
    `nota`                DECIMAL(5,2)  NULL,
    `nota_entrevista`     DECIMAL(5,2)  NULL,
    `data_entrevista`     DATE          NULL,
    `data_aplicacao`      DATETIME(6)   NOT NULL,
    `documento_resultado` VARCHAR(100)  NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_aplic_numero_inscricao` (`numero_inscricao`),
    UNIQUE KEY `uq_aplic_bolsista_edital` (`bolsista_id`, `edital_id`),
    KEY `idx_aplic_edital`   (`edital_id`),
    KEY `idx_aplic_bolsista` (`bolsista_id`),
    KEY `idx_aplic_status`   (`status`),
    CONSTRAINT `fk_aplic_bolsista` FOREIGN KEY (`bolsista_id`) REFERENCES `cadastro_cadatrobolsista` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_aplic_edital`   FOREIGN KEY (`edital_id`)   REFERENCES `editais_editalprovisorio` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 13. EDITAIS — AplicacaoEditalLog
-- ============================================================

CREATE TABLE IF NOT EXISTS `editais_aplicacaoeditallog` (
    `id`                      BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at`              DATETIME(6)  NOT NULL,
    `updated_at`              DATETIME(6)  NOT NULL,
    `aplicacao_id`            BIGINT       NOT NULL,
    `alterado_por_id`         BIGINT       NULL,
    `nota_anterior`           DECIMAL(5,2) NULL,
    `nota_nova`               DECIMAL(5,2) NULL,
    `nota_entrevista_anterior` DECIMAL(5,2) NULL,
    `nota_entrevista_nova`    DECIMAL(5,2) NULL,
    `data_entrevista_anterior` DATE        NULL,
    `data_entrevista_nova`    DATE         NULL,
    `status_anterior`         VARCHAR(20)  NOT NULL DEFAULT '',
    `status_novo`             VARCHAR(20)  NOT NULL DEFAULT '',
    PRIMARY KEY (`id`),
    KEY `idx_log_aplicacao` (`aplicacao_id`),
    CONSTRAINT `fk_log_aplicacao`    FOREIGN KEY (`aplicacao_id`)    REFERENCES `editais_aplicacaoedital` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_log_alterado_por` FOREIGN KEY (`alterado_por_id`) REFERENCES `accounts_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 14. CLASSIFICACAO — CriterioClassificacao
-- ============================================================

CREATE TABLE IF NOT EXISTS `classificacao_criterioclassificacao` (
    `id`            BIGINT        NOT NULL AUTO_INCREMENT,
    `created_at`    DATETIME(6)   NOT NULL,
    `updated_at`    DATETIME(6)   NOT NULL,
    `nome`          VARCHAR(255)  NOT NULL,
    `tipo_criterio` VARCHAR(30)   NOT NULL DEFAULT 'congressos',
    `descricao`     TEXT          NOT NULL,
    `peso`          DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `peso_maximo`   DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `ativo`         TINYINT(1)    NOT NULL DEFAULT 1,
    PRIMARY KEY (`id`),
    KEY `idx_criterio_tipo` (`tipo_criterio`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 15. CLASSIFICACAO — AvaliacaoBolsista
-- ============================================================

CREATE TABLE IF NOT EXISTS `classificacao_avaliacaobolsista` (
    `id`            BIGINT        NOT NULL AUTO_INCREMENT,
    `created_at`    DATETIME(6)   NOT NULL,
    `updated_at`    DATETIME(6)   NOT NULL,
    `bolsista_id`   BIGINT        NOT NULL,
    `criterio_id`   BIGINT        NOT NULL,
    `pontos`        DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `avaliado_por_id` BIGINT      NULL,
    `observacao`    TEXT          NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uq_avaliacao_bolsista_criterio` (`bolsista_id`, `criterio_id`),
    KEY `idx_avaliacao_criterio` (`criterio_id`),
    CONSTRAINT `fk_avaliacao_bolsista`   FOREIGN KEY (`bolsista_id`)     REFERENCES `cadastro_cadatrobolsista` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_avaliacao_criterio`   FOREIGN KEY (`criterio_id`)     REFERENCES `classificacao_criterioclassificacao` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_avaliacao_avaliado_por` FOREIGN KEY (`avaliado_por_id`) REFERENCES `accounts_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 16. NOTIFICATIONS — Notificacao
-- ============================================================

CREATE TABLE IF NOT EXISTS `notifications_notificacao` (
    `id`           BIGINT       NOT NULL AUTO_INCREMENT,
    `created_at`   DATETIME(6)  NOT NULL,
    `updated_at`   DATETIME(6)  NOT NULL,
    `destinatario_id` BIGINT    NOT NULL,
    `titulo`       VARCHAR(255) NOT NULL,
    `mensagem`     TEXT         NOT NULL,
    `lido`         TINYINT(1)   NOT NULL DEFAULT 0,
    `tipo`         VARCHAR(20)  NOT NULL DEFAULT 'sistema',
    PRIMARY KEY (`id`),
    KEY `idx_notif_destinatario` (`destinatario_id`),
    KEY `idx_notif_lido`         (`lido`),
    KEY `idx_notif_tipo`         (`tipo`),
    CONSTRAINT `fk_notif_destinatario` FOREIGN KEY (`destinatario_id`) REFERENCES `accounts_user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 17. DJANGO MIGRATIONS (controle de versao do schema)
-- ============================================================

CREATE TABLE IF NOT EXISTS `django_migrations` (
    `id`     BIGINT       NOT NULL AUTO_INCREMENT,
    `app`    VARCHAR(255) NOT NULL,
    `name`   VARCHAR(255) NOT NULL,
    `applied` DATETIME(6) NOT NULL,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


SET FOREIGN_KEY_CHECKS = 1;

-- ============================================================
-- FIM DO SCRIPT
-- ============================================================
-- Tabelas criadas: 19
--   django_content_type, auth_permission, auth_group,
--   auth_group_permissions, django_session, django_admin_log,
--   django_migrations,
--   accounts_user, accounts_user_groups, accounts_user_user_permissions,
--   accounts_perfil, accounts_documentoexterno,
--   cadastro_cadatrobolsista, cadastro_formacaoacademica,
--   cadastro_experienciaprofissional, cadastro_anexocomprobatorio,
--   cadastro_solicitacaoedicao,
--   editais_editalprovisorio, editais_cronogramaevento,
--   editais_aplicacaoedital, editais_aplicacaoeditallog,
--   classificacao_criterioclassificacao, classificacao_avaliacaobolsista,
--   notifications_notificacao
-- ============================================================
