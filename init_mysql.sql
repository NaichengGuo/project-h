CREATE DATABASE IF NOT EXISTS niuniuh5_db;
CREATE USER IF NOT EXISTS 'bigquery_user'@'%' IDENTIFIED BY 'xdf#42sdfkjdfiyuISYFj76';
GRANT ALL PRIVILEGES ON niuniuh5_db.* TO 'bigquery_user'@'%';
FLUSH PRIVILEGES;

USE niuniuh5_db;

CREATE TABLE IF NOT EXISTS table_web_loginlog (
    nPlayerId INT,
    nClubID INT,
    nAction INT,
    szTime DATETIME,
    loginIp VARCHAR(50)
);

INSERT INTO table_web_loginlog (nPlayerId, nClubID, nAction, szTime, loginIp) VALUES
(133134, 666098, 1, '2022-11-01 10:20:28', '113.118.234.183'),
(133422, 666639, 1, '2022-11-01 10:24:02', '113.118.234.183'),
(133343, 666000, 1, '2022-11-01 10:24:02', '113.118.234.183');
