-- MySQL dump 10.13  Distrib 8.0.21, for Win64 (x86_64)
--
-- Host: localhost    Database: melody
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
-- Table structure for table `user_stats`
--

DROP TABLE IF EXISTS `user_stats`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_stats` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `TopSong` varchar(45) DEFAULT NULL,
  `Top Artist` varchar(45) DEFAULT NULL,
  `TopGenre` varchar(45) DEFAULT NULL,
  `Min Popularity` varchar(45) DEFAULT NULL,
  `Avg Popularity` varchar(45) DEFAULT NULL,
  `Max Popularity` varchar(45) DEFAULT NULL,
  `Min Acoustic` varchar(45) DEFAULT NULL,
  `Avg Acoustic` varchar(45) DEFAULT NULL,
  `Max Acoustic` varchar(45) DEFAULT NULL,
  `Min Dance` varchar(45) DEFAULT NULL,
  `Avg Dance` varchar(45) DEFAULT NULL,
  `Max Dance` varchar(45) DEFAULT NULL,
  `Min Energy` varchar(45) DEFAULT NULL,
  `Avg Energy` varchar(45) DEFAULT NULL,
  `Max Energy` varchar(45) DEFAULT NULL,
  `Min Instrument` varchar(45) DEFAULT NULL,
  `Avg Instrument` varchar(45) DEFAULT NULL,
  `Max Instrument` varchar(45) DEFAULT NULL,
  `Min Live` varchar(45) DEFAULT NULL,
  `Avg Live` varchar(45) DEFAULT NULL,
  `Max Live` varchar(45) DEFAULT NULL,
  `Min Loud` varchar(45) DEFAULT NULL,
  `Avg Loud` varchar(45) DEFAULT NULL,
  `Max Loud` varchar(45) DEFAULT NULL,
  `Min Speech` varchar(45) DEFAULT NULL,
  `Avg Speech` varchar(45) DEFAULT NULL,
  `Max Speech` varchar(45) DEFAULT NULL,
  `Min Valence` varchar(45) DEFAULT NULL,
  `Avg Valence` varchar(45) DEFAULT NULL,
  `Max Valence` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`ID`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_stats`
--

LOCK TABLES `user_stats` WRITE;
/*!40000 ALTER TABLE `user_stats` DISABLE KEYS */;
INSERT INTO `user_stats` VALUES (1,'None',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(2,'None',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),(3,'None',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `user_stats` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-03-06 13:35:33
