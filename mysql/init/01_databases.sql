-- Operatives Quellsystem (Uebung 3) und Serving-DB fuer Metabase (Uebung 5).
CREATE DATABASE IF NOT EXISTS qvig_op   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS qvig_mart CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Der Benutzer 'qvig' wird vom MySQL-Image bereits fuer qvig_op angelegt;
-- hier zusaetzlich Rechte auf qvig_mart.
GRANT ALL PRIVILEGES ON qvig_op.*   TO 'qvig'@'%';
GRANT ALL PRIVILEGES ON qvig_mart.* TO 'qvig'@'%';
FLUSH PRIVILEGES;
