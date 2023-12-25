create table robot_information
(
    BotID        int auto_increment
        primary key,
    BotName      varchar(20)                            null,
    BotKey       varchar(255)                           null,
    BotStatus    tinyint(1) default 1                   null,
    MessageCount int        default 0                   null,
    CreatedAt    timestamp  default current_timestamp() null
);
