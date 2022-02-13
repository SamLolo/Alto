-- MySQL dump 10.13  Distrib 8.0.21, for Win64 (x86_64)
--
-- Host: localhost    Database: discordmusic
-- ------------------------------------------------------
-- Server version	8.0.21

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `cache`
--

DROP TABLE IF EXISTS `cache`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cache` (
  `SoundcloudID` varchar(16) NOT NULL,
  `SoundcloudURL` varchar(128) NOT NULL,
  `SpotifyID` varchar(32) DEFAULT NULL,
  `Name` varchar(128) DEFAULT NULL,
  `Artists` varchar(1024) DEFAULT NULL,
  `ArtistID` varchar(1024) DEFAULT NULL,
  `Album` varchar(128) DEFAULT NULL,
  `AlbumID` varchar(32) DEFAULT NULL,
  `Art` varchar(128) DEFAULT NULL,
  `Colour` varchar(16) DEFAULT NULL,
  `ReleaseDate` varchar(64) DEFAULT NULL,
  `Popularity` int DEFAULT NULL,
  `Explicit` tinyint DEFAULT NULL,
  `Preview` varchar(128) DEFAULT NULL,
  `LastRefresh` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`SoundcloudID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cache`
--

LOCK TABLES `cache` WRITE;
/*!40000 ALTER TABLE `cache` DISABLE KEYS */;
INSERT INTO `cache` VALUES ('1010903185','https://soundcloud.com/juliamichaelsofficial/all-your-exes','0sm5R6MjXORjLcs1bulN6n','All Your Exes','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,1,NULL,'2022-01-20 18:23:47'),('1025477269','https://soundcloud.com/juliamichaelsofficial/love-is-weird','1g5pB9oVpLUM7dxhGhCOke','Love Is Weird','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,NULL,NULL,'2022-01-20 18:23:50'),('1035037822','https://soundcloud.com/juliamichaelsofficial/undertone','0JeAo18bs3edkTQ30aZtih','Undertone','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,NULL,NULL,'2022-01-20 18:24:10'),('1035038161','https://soundcloud.com/juliamichaelsofficial/thats-the-kind-of-woman','3LS7eIJfb4eajXcqbnlN2b','That\'s The Kind Of Woman','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,NULL,NULL,'2022-01-20 18:24:13'),('1035038299','https://soundcloud.com/juliamichaelsofficial/pessimist','5YAkSJQDoAPx0zGgo8vHU2','Pessimist','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,NULL,NULL,'2022-01-20 18:23:53'),('1035038977','https://soundcloud.com/juliamichaelsofficial/orange-magic','08Ov5PSmldmPxZDGufK6Pj','Orange Magic','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,NULL,NULL,'2022-01-20 18:23:59'),('1035039046','https://soundcloud.com/juliamichaelsofficial/little-did-i-know','6En4n38HDSmtGxQJu2Tekp','Little Did I Know','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,NULL,NULL,'2022-01-20 18:23:56'),('1035039235','https://soundcloud.com/juliamichaelsofficial/wrapped-around','433GlmCc3VnUHqogFFQzq9','Wrapped Around','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,1,NULL,'2022-01-20 18:24:05'),('1143798565','https://soundcloud.com/alfie-templeman/3d-feelings','1OkW0tv1k3kNB0IXDN2oPL','3D Feelings','\'Alfie Templeman\'','\'6QzMY3tnu0m56eKUnr4uCF\'','3D Feelings - Single','0ZY2Lg0utycFyUQSDlK3MZ','https://i.scdn.co/image/ab67616d0000b2735fd6494b0df8d633e01f7cf7','(192, 135, 78)','02th Nov 2021',63,NULL,'https://p.scdn.co/mp3-preview/e33597b5a6eec6cf62149cf91894eb5103c2fd17?cid=710b5d6211ee479bb370e289ed1cda3d','2022-01-05 12:12:21'),('209579854','https://soundcloud.com/nocopyrightsounds/janji-heroes-tonight-feat-johnningncs-release',NULL,'Janji - Heroes Tonight (feat. Johnning)[NCS Release]','\'NCS\'',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2022-01-21 22:44:23'),('301745743','https://soundcloud.com/juliamichaelsofficial/issues','0c35qjZXDGTkNHXUlIc6tY','History','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,NULL,NULL,'2022-01-20 18:24:08'),('890450080','https://soundcloud.com/maisie-peters/maybe-dont-feat-jp-saxe','7ksYNhalX8IWKku513n8QG','Maybe Don\'t (feat. JP Saxe)','\'Maisie Peters\', \'JP Saxe\'','\'2RVvqRBon9NgaGXKfywDSs\', \'66W9LaWS0DPdL7Sz8iYGYe\'','Maybe Don\'t - Single','2X5tbY4Yam5ir3dG8eJSHa','https://i.scdn.co/image/ab67616d0000b273a04dfe86aa8f5dd21b170db2','(32, 31, 22)','21th Sep 2020',64,NULL,'https://p.scdn.co/mp3-preview/bee5979139c734a99e1af92dda1da0e7579f4fc2?cid=710b5d6211ee479bb370e289ed1cda3d','2022-01-06 19:20:09'),('902977084','https://soundcloud.com/juliamichaelsofficial/lie-like-this','1rqIA9CG4Vj44JYVqBpxIj','Lie Like This','\'Julia Michaels\'','\'0ZED1XzwlLHW4ZaG4lOT6m\'','Not In Chronological Order','0tDLeJartXoM4ACuUx2MOu','https://i.scdn.co/image/ab67616d0000b273960eb70ef8f0465a508bd700','(41, 42, 53)','30th Apr 2021',60,1,NULL,'2022-01-20 18:24:02');
/*!40000 ALTER TABLE `cache` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-02-03  8:18:01
