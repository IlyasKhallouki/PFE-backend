##### upgrade #####
CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(32) NOT NULL UNIQUE,
    `description` VARCHAR(255)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `full_name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(120) NOT NULL UNIQUE,
    `hashed_password` VARCHAR(128) NOT NULL,
    `current_jti` VARCHAR(36),
    `is_active` BOOL NOT NULL DEFAULT 1,
    `last_login` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `role_id` INT,
    CONSTRAINT `fk_users_roles_2657b48c` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `channels` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(60) NOT NULL,
    `is_private` BOOL NOT NULL DEFAULT 0,
    `role_id` INT,
    UNIQUE KEY `uid_channels_name_794792` (`name`, `is_private`),
    CONSTRAINT `fk_channels_roles_ace65413` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `channel_members` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `joined_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `channel_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    UNIQUE KEY `uid_channel_mem_user_id_95c41a` (`user_id`, `channel_id`),
    CONSTRAINT `fk_channel__channels_c87eba89` FOREIGN KEY (`channel_id`) REFERENCES `channels` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_channel__users_704447b3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `messages` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `content` LONGTEXT NOT NULL,
    `sent_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `author_id` INT NOT NULL,
    `channel_id` INT NOT NULL,
    CONSTRAINT `fk_messages_users_4677258a` FOREIGN KEY (`author_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_messages_channels_5f78b201` FOREIGN KEY (`channel_id`) REFERENCES `channels` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(20) NOT NULL,
    `content` LONGTEXT NOT NULL
) CHARACTER SET utf8mb4;
