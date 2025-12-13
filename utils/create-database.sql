-- Create database
CREATE DATABASE IF NOT EXISTS watering
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Create user
CREATE USER IF NOT EXISTS 'wateringuser'@'localhost'
  IDENTIFIED BY 'aiyohd6Usee1phiechaung5ah';

-- Grant privileges
GRANT ALL PRIVILEGES ON watering.* TO 'wateringuser'@'localhost';

-- Apply privileges
FLUSH PRIVILEGES;
