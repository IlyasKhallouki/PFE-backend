##### upgrade #####
ALTER TABLE `users` DROP COLUMN `full_name`;
##### downgrade #####
ALTER TABLE `users` ADD `full_name` VARCHAR(120)NOT NULL;
