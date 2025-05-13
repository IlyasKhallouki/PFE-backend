##### upgrade #####
ALTER TABLE `users` ADD `full_name` VARCHAR(120)NOT NULL;
##### downgrade #####
ALTER TABLE `users` DROP COLUMN `full_name`;
