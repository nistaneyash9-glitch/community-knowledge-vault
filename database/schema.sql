-- ==========================================================================
-- COMMUNITY KNOWLEDGE VAULT (CKV) - DATABASE SCHEMA & SEED DATA
-- Database System: MySQL / MariaDB
-- ==========================================================================

CREATE DATABASE IF NOT EXISTS `community_knowledge_vault` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `community_knowledge_vault`;

-- Disable foreign key checks for clean recreation
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS `reports`;
DROP TABLE IF EXISTS `answers`;
DROP TABLE IF EXISTS `questions`;
DROP TABLE IF EXISTS `helpful_votes`;
DROP TABLE IF EXISTS `ratings`;
DROP TABLE IF EXISTS `learning_requests`;
DROP TABLE IF EXISTS `skills`;
DROP TABLE IF EXISTS `knowledge`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `users`;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. USERS TABLE
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(120) NOT NULL,
  `email` VARCHAR(150) NOT NULL UNIQUE,
  `password` VARCHAR(255) NOT NULL,
  `location` VARCHAR(150) DEFAULT 'Amravati',
  `language` VARCHAR(50) DEFAULT 'English',
  `profile_image` VARCHAR(255) DEFAULT 'default_avatar.jpg',
  `role` ENUM('user', 'admin') NOT NULL DEFAULT 'user',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. CATEGORIES TABLE
CREATE TABLE `categories` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL UNIQUE,
  `description` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. KNOWLEDGE TABLE
CREATE TABLE `knowledge` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `category_id` INT NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `description` TEXT NOT NULL,
  `skill_level` ENUM('Beginner', 'Intermediate', 'Advanced') DEFAULT 'Beginner',
  `language` VARCHAR(50) DEFAULT 'English',
  `location` VARCHAR(150) DEFAULT 'Amravati',
  `tags` VARCHAR(255),
  `image` VARCHAR(255),
  `status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
  `is_verified` BOOLEAN DEFAULT FALSE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. SKILLS TABLE
CREATE TABLE `skills` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL UNIQUE,
  `category_id` INT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. LEARNING REQUESTS TABLE
CREATE TABLE `learning_requests` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `knowledge_id` INT NOT NULL,
  `teacher_id` INT NOT NULL,
  `learner_id` INT NOT NULL,
  `message` TEXT,
  `status` ENUM('pending', 'accepted', 'rejected', 'completed') DEFAULT 'pending',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`knowledge_id`) REFERENCES `knowledge`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`teacher_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`learner_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. RATINGS & REVIEWS TABLE
CREATE TABLE `ratings` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `knowledge_id` INT NOT NULL,
  `learner_id` INT NOT NULL,
  `learning_request_id` INT,
  `rating` INT NOT NULL CHECK (`rating` >= 1 AND `rating` <= 5),
  `review` TEXT,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_user_rating` (`knowledge_id`, `learner_id`),
  FOREIGN KEY (`knowledge_id`) REFERENCES `knowledge`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`learner_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`learning_request_id`) REFERENCES `learning_requests`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. HELPFUL VOTES TABLE
CREATE TABLE `helpful_votes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `knowledge_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_helpful_vote` (`knowledge_id`, `user_id`),
  FOREIGN KEY (`knowledge_id`) REFERENCES `knowledge`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. QUESTIONS TABLE
CREATE TABLE `questions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `knowledge_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `question_text` TEXT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`knowledge_id`) REFERENCES `knowledge`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. ANSWERS TABLE
CREATE TABLE `answers` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `question_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `answer_text` TEXT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`question_id`) REFERENCES `questions`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. REPORTS TABLE
CREATE TABLE `reports` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `knowledge_id` INT NOT NULL,
  `reported_by` INT NOT NULL,
  `reason` VARCHAR(100) NOT NULL,
  `description` TEXT,
  `status` ENUM('pending', 'reviewed', 'resolved') DEFAULT 'pending',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`knowledge_id`) REFERENCES `knowledge`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`reported_by`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==========================================================================
-- SEED DATA
-- ==========================================================================

-- Seed Categories (5 Core Disciplines)
INSERT INTO `categories` (`id`, `name`, `description`) VALUES
(1, 'Farming', 'Organic agriculture, soil recharging, and natural pest management'),
(2, 'Gardening', 'Urban terrace planting, compost making, and herbal flora'),
(3, 'Local History', 'Architectural stepwells, historical narratives, and oral folklore'),
(4, 'Cooking', 'Regional culinary heritage, sun-cured pickling, and ancient recipes'),
(5, 'Traditional Skills', 'Indigenous crafts, weaving, carpentry, and hands-on skills');

-- Seed Users (Passwords hashed using Werkzeug scrypt)
-- admin@amravati.in -> admin123
-- ramesh.patel@amravati.in -> masterweaver2026
-- ananya.sharma@amravati.edu -> studentpass123
-- kalyani.devi@amravati.in -> kalyanipass123
-- devraj@amravati.in -> devrajpass123
INSERT INTO `users` (`id`, `name`, `email`, `password`, `location`, `language`, `profile_image`, `role`) VALUES
(1, 'Admin Custodian', 'admin@amravati.in', 'scrypt:32768:8:1$UNB9h47IZ47ecikc$37a6bf1127eb17b1c1abf61418e69e1601631179b168cadc1b9d5ac0c20c0143a1b41f7dc6e1f79bd59b52442cd28f7ffdca82ff5ea7e7a1705cc0d67fa21624', 'Amravati Central', 'English', 'https://ui-avatars.com/api/?name=Admin+Custodian&background=141c16&color=d8f844&bold=true', 'admin'),
(2, 'Ramesh Patel', 'ramesh.patel@amravati.in', 'scrypt:32768:8:1$WFmRfxIwP3uouZbb$d47ac478a7eb20b11f6ab14812291b1639037485f4428b5247c6c444265457f477a4a9d3e002bea2a413dcfed58460f153c65f3f83d38f45d023b1ffe552fd04', 'Amravati Old Artisan Quarter', 'English', 'https://ui-avatars.com/api/?name=Ramesh+Patel&background=141c16&color=d8f844&bold=true', 'user'),
(3, 'Ananya Sharma', 'ananya.sharma@amravati.edu', 'scrypt:32768:8:1$75cQq524oDbvfKjC$094395a540d2e2ae4a10a09f95558f800d94ca6552af376168f97204adfe442dd6e36d86326ff935fea49cbb06831fe9f96b472c64ba56fb09976b7179060cbc', 'Amravati University Campus', 'English', 'https://ui-avatars.com/api/?name=Ananya+Sharma&background=141c16&color=d8f844&bold=true', 'user'),
(4, 'Kalyani Devi', 'kalyani.devi@amravati.in', 'scrypt:32768:8:1$Rml0Y5DQitPz7FND$eaaa222f7e6f7850143d45eed91be3fffcf65511cac66ebbd71744b1b76749c1155c1523ba5863ab29e5419ae08e51b7ce4713f1f5513336fb329891a80d3736', 'Amravati North Valley', 'English', 'https://ui-avatars.com/api/?name=Kalyani+Devi&background=141c16&color=d8f844&bold=true', 'user'),
(5, 'Prof. Devraj', 'devraj@amravati.in', 'scrypt:32768:8:1$7XQ1KTijBbRNKZSv$d3a930f49e3b378accce88e3dc9b7803e378566b411084db22b4f7608a79745304ba3bf05077a6e9d9640ce73f291656f6c9ac6e84f2683f1a22b1cbf7b92b15', 'Amravati Heritage Ward', 'English', 'https://ui-avatars.com/api/?name=Prof+Devraj&background=141c16&color=d8f844&bold=true', 'user');

-- Seed Skills
INSERT INTO `skills` (`id`, `name`, `category_id`) VALUES
(1, 'Bamboo Splint Weaving', 5),
(2, 'Mortise & Tenon Joinery', 5),
(3, 'Python Basic Automation', 5),
(4, 'Sun-Cured Pickling', 4),
(5, 'Rainwater Khadin Construction', 1),
(6, 'Dokra Lost-Wax Casting', 5),
(7, 'Stepwell Architecture Mapping', 3),
(8, 'Natural Indigo Fermentation', 5),
(9, 'Compost & Organic Flora', 2);

-- Seed Knowledge Entries
INSERT INTO `knowledge` (`id`, `user_id`, `category_id`, `title`, `description`, `skill_level`, `language`, `location`, `tags`, `image`, `status`, `is_verified`) VALUES
(1, 2, 5, 'Traditional Bamboo Basket Making', 'Preshaping wild bamboo splints, seasoning with natural smoke, and weaving interlocking tight bottoms. Passed down through five generations for agricultural storage.', 'Intermediate', 'English', 'Amravati Old Quarter', 'bamboo, weaving, traditional skills, craft', 'https://images.unsplash.com/photo-1590736969955-71cc94801759?w=800&auto=format&fit=crop&q=80', 'approved', 1),
(2, 3, 5, 'Basic Python Programming for Beginners', 'A community student mentor guide introducing computational logic, variables, conditional branches, loops, and building simple CLI helper tools.', 'Beginner', 'English', 'Amravati Campus', 'python, programming, education, coding', 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&auto=format&fit=crop&q=80', 'approved', 1),
(3, 4, 4, 'Traditional Mango & Spice Pickle Recipe', 'Sun-cured preservation ratios using cold-pressed mustard oil, fenugreek, rock salt, and spices that preserve taste and medicinal vitality for up to three years.', 'Beginner', 'English', 'Amravati North', 'pickle, cooking, spices, preservation', 'https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=800&auto=format&fit=crop&q=80', 'approved', 1),
(4, 5, 3, 'History of Our Community & Stepwell Systems', 'Oral records and architectural blueprints detailing the medieval settlement, groundwater harvesting stepwells, and stone facades of Amravati.', 'Intermediate', 'English', 'Amravati Ward 4', 'history, stepwell, architecture, heritage', 'https://images.unsplash.com/photo-1599661046289-e31897846e41?w=800&auto=format&fit=crop&q=80', 'approved', 1),
(5, 2, 1, 'Traditional Rainwater Khadin System', 'Constructing low earthen bunds to capture seasonal runoff and recharge dry soil tables for winter wheat and chickpea crops.', 'Intermediate', 'English', 'Amravati Fields', 'farming, rainwater, soil, agriculture', 'https://images.unsplash.com/photo-1500937386664-56d1dfef3854?w=800&auto=format&fit=crop&q=80', 'approved', 1),
(6, 2, 5, 'Lost-Wax Dokra Brass Casting', 'Clay core modeling, beeswax coil wrapping, and ancient kiln firing to create artisanal bell-metal figurines.', 'Advanced', 'English', 'Amravati Old Quarter', 'dokra, brass, metalwork, handicrafts', 'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800&auto=format&fit=crop&q=80', 'approved', 0),
(7, 3, 5, 'Natural Indigo Vat Fermentation', 'Creating active organic reduction vats using limestone, jaggery, and crushed natural indigo leaves for block printing.', 'Intermediate', 'English', 'Amravati Campus', 'indigo, dye, arts, culture, printing', 'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=800&auto=format&fit=crop&q=80', 'approved', 1),
(8, 2, 2, 'Urban Terrace Herb & Plant Gardening', 'Simple compost preparation, pot selection, and nurturing medicinal flora on domestic terrace spaces.', 'Beginner', 'English', 'Amravati West', 'gardening, plants, diy, flora', 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=800&auto=format&fit=crop&q=80', 'approved', 0),
(9, 3, 5, 'Mortise & Tenon Wood Joinery Without Nails', 'The art of interlocking timber joints that withstand earthquake tremors without a single iron nail or screw.', 'Advanced', 'English', 'Amravati Old Quarter', 'wood, joinery, traditional, craft', 'https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=800&auto=format&fit=crop&q=80', 'pending', 0);

-- Seed Learning Requests
INSERT INTO `learning_requests` (`id`, `knowledge_id`, `teacher_id`, `learner_id`, `message`, `status`) VALUES
(1, 1, 2, 3, 'Respected Ramesh Ji, I would love to learn bamboo splint preparation in your weekend workshop.', 'accepted'),
(2, 3, 4, 3, 'Kalyani Ji, please guide me on the mustard oil heating temp for mango pickle curing.', 'completed');

-- Seed Ratings
INSERT INTO `ratings` (`id`, `knowledge_id`, `learner_id`, `learning_request_id`, `rating`, `review`) VALUES
(1, 3, 3, 2, 5, 'Kalyani Ji explained the exact oil temperature and rock salt ratio. The pickle turned out fantastic!');

-- Seed Helpful Votes
INSERT INTO `helpful_votes` (`id`, `knowledge_id`, `user_id`) VALUES
(1, 1, 3), (2, 1, 4), (3, 1, 5),
(4, 2, 2), (5, 2, 4),
(6, 3, 2), (7, 3, 3), (8, 3, 5),
(9, 4, 2), (10, 4, 3);

-- Seed Questions & Answers
INSERT INTO `questions` (`id`, `knowledge_id`, `user_id`, `question_text`) VALUES
(1, 1, 3, 'How long should bamboo splints be soaked in river water before weaving?'),
(2, 3, 2, 'Can we substitute jaggery for rock sugar in this recipe?');

INSERT INTO `answers` (`id`, `question_id`, `user_id`, `answer_text`) VALUES
(1, 1, 2, 'Soak for about 30 to 45 minutes until pliable. Do not over-soak or the fibers will soften excessively.'),
(2, 2, 4, 'Yes, organic dark jaggery works wonderfully and enhances the natural tangy fermentation.');

-- Seed Reports
INSERT INTO `reports` (`id`, `knowledge_id`, `reported_by`, `reason`, `description`, `status`) VALUES
(1, 8, 3, 'Spam or Incomplete', 'Requires clarification on diode safety values for 24V solar setups.', 'pending');
