    -- Create the database
    CREATE DATABASE IF NOT EXISTS missing_persons;
    USE missing_persons;

    -- Create user table
    CREATE TABLE IF NOT EXISTS user (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(120) UNIQUE NOT NULL,
        password VARCHAR(200) NOT NULL,
        name VARCHAR(100) NOT NULL,
        role VARCHAR(20) DEFAULT 'user',
        avatar VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        last_login DATETIME
    );

    -- Create core_missingperson table
    CREATE TABLE IF NOT EXISTS core_missingperson (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        age INT NOT NULL,
        gender CHAR(1) NOT NULL,
        height DECIMAL(5,2) NOT NULL,
        weight DECIMAL(5,2) NOT NULL,
        last_seen DATETIME NOT NULL,
        last_seen_location VARCHAR(200) NOT NULL,
        description TEXT NOT NULL,
        photo VARCHAR(100) NOT NULL,
        face_encoding LONGBLOB,
        face_landmarks JSON,
        face_quality_score FLOAT,
        contact_name VARCHAR(100) NOT NULL,
        contact_phone VARCHAR(15) NOT NULL,
        contact_email VARCHAR(254) NOT NULL,
        is_found TINYINT(1) NOT NULL DEFAULT 0,
        date_found DATETIME,
        created_at DATETIME NOT NULL,
        updated_at DATETIME NOT NULL
    );

    -- Create core_matchreport table
    CREATE TABLE IF NOT EXISTS core_matchreport (
        id INT AUTO_INCREMENT PRIMARY KEY,
        location VARCHAR(200) NOT NULL,
        timestamp DATETIME NOT NULL,
        confidence_score DOUBLE NOT NULL,
        photo VARCHAR(100) NOT NULL,
        face_encoding LONGBLOB,
        face_landmarks JSON,
        face_quality_score FLOAT,
        is_verified TINYINT(1) NOT NULL DEFAULT 0,
        verification_notes TEXT,
        missing_person_id INT NOT NULL,
        reported_by_id INT,
        verified_by_id INT,
        FOREIGN KEY (missing_person_id) REFERENCES core_missingperson(id) ON DELETE CASCADE,
        FOREIGN KEY (reported_by_id) REFERENCES user(id) ON DELETE SET NULL,
        FOREIGN KEY (verified_by_id) REFERENCES user(id) ON DELETE SET NULL
    );

    -- Create core_alert table
    CREATE TABLE IF NOT EXISTS core_alert (
        id INT AUTO_INCREMENT PRIMARY KEY,
        sent_at DATETIME NOT NULL,
        alert_type VARCHAR(20) NOT NULL,
        status VARCHAR(20) NOT NULL,
        response_received TINYINT(1) NOT NULL DEFAULT 0,
        response_notes TEXT,
        missing_person_id INT NOT NULL,
        match_report_id INT NOT NULL,
        FOREIGN KEY (missing_person_id) REFERENCES core_missingperson(id) ON DELETE CASCADE,
        FOREIGN KEY (match_report_id) REFERENCES core_matchreport(id) ON DELETE CASCADE
    );

    -- Create indexes for better performance
    CREATE INDEX idx_missingperson_name ON core_missingperson(name);
    CREATE INDEX idx_missingperson_is_found ON core_missingperson(is_found);
    CREATE INDEX idx_missingperson_face_quality ON core_missingperson(face_quality_score);
    CREATE INDEX idx_matchreport_timestamp ON core_matchreport(timestamp);
    CREATE INDEX idx_matchreport_is_verified ON core_matchreport(is_verified);
    CREATE INDEX idx_matchreport_face_quality ON core_matchreport(face_quality_score);
    CREATE INDEX idx_alert_status ON core_alert(status);

    -- Create admin user with proper password hash
    INSERT INTO user (email, password, name, role)
    VALUES ('admin@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBAQHxQZxQZxQZ', 'Admin', 'admin')
    ON DUPLICATE KEY UPDATE id=id; 