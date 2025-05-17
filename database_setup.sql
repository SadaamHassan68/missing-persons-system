    -- Create the database
    CREATE DATABASE IF NOT EXISTS missing_persons;
    USE missing_persons;

    -- Create auth_user table (Django's default user table)
    CREATE TABLE IF NOT EXISTS auth_user (
        id INT AUTO_INCREMENT PRIMARY KEY,
        password VARCHAR(128) NOT NULL,
        last_login DATETIME,
        is_superuser TINYINT(1) NOT NULL,
        username VARCHAR(150) NOT NULL UNIQUE,
        first_name VARCHAR(150) NOT NULL,
        last_name VARCHAR(150) NOT NULL,
        email VARCHAR(254) NOT NULL,
        is_staff TINYINT(1) NOT NULL,
        is_active TINYINT(1) NOT NULL,
        date_joined DATETIME NOT NULL
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
        is_verified TINYINT(1) NOT NULL DEFAULT 0,
        verification_notes TEXT,
        missing_person_id INT NOT NULL,
        reported_by_id INT,
        verified_by_id INT,
        FOREIGN KEY (missing_person_id) REFERENCES core_missingperson(id) ON DELETE CASCADE,
        FOREIGN KEY (reported_by_id) REFERENCES auth_user(id) ON DELETE SET NULL,
        FOREIGN KEY (verified_by_id) REFERENCES auth_user(id) ON DELETE SET NULL
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
    CREATE INDEX idx_matchreport_timestamp ON core_matchreport(timestamp);
    CREATE INDEX idx_matchreport_is_verified ON core_matchreport(is_verified);
    CREATE INDEX idx_alert_status ON core_alert(status); 