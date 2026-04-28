CREATE DATABASE IF NOT EXISTS mpesa_system;
USE mpesa_system;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS businesses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    business_name VARCHAR(100) NOT NULL,
    shortcode VARCHAR(20) NOT NULL,
    shortcode_type ENUM('paybill', 'till') DEFAULT 'till',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_shortcode_per_user (user_id, shortcode)
);

CREATE TABLE IF NOT EXISTS payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    business_id INT NOT NULL,
    phone_encrypted TEXT NOT NULL,
    phone_hash VARCHAR(64) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    mpesa_code VARCHAR(50) UNIQUE NOT NULL,
    transaction_time DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_id) REFERENCES businesses(id) ON DELETE CASCADE,
    INDEX idx_phone_hash (phone_hash),
    INDEX idx_business_time (business_id, transaction_time)
);