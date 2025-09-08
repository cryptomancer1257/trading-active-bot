USE bot_marketplace;

ALTER TABLE bots
ADD COLUMN code_path_rpa VARCHAR(255) COMMENT 'Path to RPA code',
ADD COLUMN version_rpa VARCHAR(50) DEFAULT '1.0.0' COMMENT 'Version of the RPA code';
COMMIT;