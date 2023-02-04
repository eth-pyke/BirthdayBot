CREATE TABLE Birthdays(
    userID INT,
    guildID INT,
    userName VARCHAR,
    bday DATE NOT NULL,
    PRIMARY KEY(userID, guildID)
);
CREATE TABLE Servers(
    serverID INT PRIMARY KEY,
    serverName VARCHAR,
    channelID INT,
    announceTime timestamp
);