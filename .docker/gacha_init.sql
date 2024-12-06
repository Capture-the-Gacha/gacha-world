CREATE DATABASE IF NOT EXISTS ctg;
USE ctg;

CREATE TABLE `gacha` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `image_url` varchar(255) NOT NULL,
  `rarity` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `gacha` VALUES (1,'Vulpeon','/images/Vulpeon.jpg','common'),(2,'Wavebite','/images/Wavebite.jpg','common'),(3,'Cryonix','/images/Cryonix.jpg','common'),(4,'Floranis','/images/Floranis.jpg','common'),(5,'Acquashade','/images/Acquashade.jpg','common'),(6,'Sabeclaw','/images/Sabeclaw.jpg','common'),(7,'Mysthorn','/images/Mysthorn.jpg','rare'),(8,'Thunderfang','/images/Thunderfang.jpg','rare'),(9,'Glacior','/images/Glacior.jpg','rare'),(10,'Jolthowl','/images/Jolthowl.jpg','rare'),(11,'Aureluna','/images/Aureluna.jpg','epic'),(12,'Lunalia','/images/Lunalia.jpg','epic'),(13,'Drakflare','/images/Drakflare.jpg','legendary');
