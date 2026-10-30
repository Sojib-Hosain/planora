CREATE DATABASE IF NOT EXISTS planora;
USE planora;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('standard', 'admin') NOT NULL DEFAULT 'standard',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(60) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS venues (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    address VARCHAR(255) NOT NULL,
    capacity INT NOT NULL,
    suitable_types VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    category_id INT NOT NULL,
    venue_id INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    base_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_tickets INT NOT NULL,
    tickets_left INT NOT NULL,
    last_booking_date DATE NOT NULL,
    description TEXT NOT NULL,
    condition_notes TEXT NOT NULL,
    is_featured TINYINT(1) NOT NULL DEFAULT 0,
    status ENUM('active', 'archived') NOT NULL DEFAULT 'active',
    CONSTRAINT fk_events_category FOREIGN KEY (category_id) REFERENCES categories(id),
    CONSTRAINT fk_events_venue FOREIGN KEY (venue_id) REFERENCES venues(id)
);

CREATE TABLE IF NOT EXISTS event_days (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_id INT NOT NULL,
    event_date DATE NOT NULL,
    day_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT fk_event_days_event FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    quantity INT NOT NULL,
    selected_days TEXT NULL,
    booking_date DATE NOT NULL,
    days_in_advance INT NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    advance_discount_rate DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    advance_discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    student_discount_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_price DECIMAL(10,2) NOT NULL,
    cancellation_charge DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status ENUM('confirmed', 'cancelled') NOT NULL DEFAULT 'confirmed',
    receipt_code VARCHAR(40) NOT NULL UNIQUE,
    CONSTRAINT fk_bookings_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_bookings_event FOREIGN KEY (event_id) REFERENCES events(id)
);

CREATE TABLE IF NOT EXISTS waitlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    event_id INT NOT NULL,
    quantity INT NOT NULL,
    created_at DATETIME NOT NULL,
    status ENUM('waiting', 'offered') NOT NULL DEFAULT 'waiting',
    CONSTRAINT fk_waitlist_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_waitlist_event FOREIGN KEY (event_id) REFERENCES events(id)
);
