create table `chatbot`.`thenazigame` (
  `id` int(11)  not null auto_increment,
  `gameid` int(11)  not null,
  `entry` varchar(255)  not null,
  `uid` int(11)  not null,
  primary key(`id`)
);

create table `chatbot`.`thenazigames` (
  `id` int(11) not null auto_increment,
  `azi` varchar(63) not null comment 'the charateristic part of the game',
  `uids` varchar(255) not null comment 'comma-seperated list of the participants of this game',
  primary key(`id`)
);