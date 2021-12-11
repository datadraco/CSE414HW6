CREATE TABLE caregivers (
    username varchar(255),
    salt BINARY(16),
    hash BINARY(16),
    PRIMARY KEY (username)
);

CREATE TABLE availabilities (
    time date,
    username varchar(255) REFERENCES caregivers,
    PRIMARY KEY (time, username)
);

CREATE TABLE vaccines (
    name varchar(255),
    doses int,
    PRIMARY KEY (name)
);

CREATE TABLE patients (
    username varchar(255),
    salt BINARY(16),
    hash BINARY(16),
    PRIMARY KEY (username)
);

CREATE TABLE appointments (
    id int IDENTITY(1, 1),
    vaccine varchar(255) REFERENCES vaccine (name),
    patient varchar(255) REFERENCES patients (username),
    caregiver varchar(255),
    time date,
    PRIMARY KEY (id)
    FOREIGN KEY(time, caregiver) REFERENCES availabilities (time, username)
);
