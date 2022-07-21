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
-- Table structure for table `recommendations`
--

DROP TABLE IF EXISTS `recommendations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recommendations` (
  `DiscordID` varchar(32) NOT NULL,
  `SongCount` int DEFAULT '0',
  `Min Popularity` int DEFAULT NULL,
  `Avg Popularity` int DEFAULT NULL,
  `Max Popularity` int DEFAULT NULL,
  `Min Acoustic` float DEFAULT NULL,
  `Avg Acoustic` float DEFAULT NULL,
  `Max Acoustic` float DEFAULT NULL,
  `Min Dance` float DEFAULT NULL,
  `Avg Dance` float DEFAULT NULL,
  `Max Dance` float DEFAULT NULL,
  `Min Energy` float DEFAULT NULL,
  `Avg Energy` float DEFAULT NULL,
  `Max Energy` float DEFAULT NULL,
  `Min Instrument` float DEFAULT NULL,
  `Avg Instrument` float DEFAULT NULL,
  `Max Instrument` float DEFAULT NULL,
  `Min Live` float DEFAULT NULL,
  `Avg Live` float DEFAULT NULL,
  `Max Live` float DEFAULT NULL,
  `Min Loud` float DEFAULT NULL,
  `Avg Loud` float DEFAULT NULL,
  `Max Loud` float DEFAULT NULL,
  `Min Speech` float DEFAULT NULL,
  `Avg Speech` float DEFAULT NULL,
  `Max Speech` float DEFAULT NULL,
  `Min Valence` float DEFAULT NULL,
  `Avg Valence` float DEFAULT NULL,
  `Max Valence` float DEFAULT NULL,
  PRIMARY KEY (`DiscordID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recommendations`
--

LOCK TABLES `recommendations` WRITE;
/*!40000 ALTER TABLE `recommendations` DISABLE KEYS */;
INSERT INTO `recommendations` VALUES ('925098537539211304',0,0,50,100,0,0.223396,1,0,0.6845,1,0,0.64464,1,0,0.001568,1,0,0.163196,1,-15,-6.25084,0,0,0.106186,1,0,0.521244,1);
/*!40000 ALTER TABLE `recommendations` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-07-18 17:48:55
