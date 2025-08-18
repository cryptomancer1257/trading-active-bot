-- MySQL dump 10.13  Distrib 9.2.0, for macos15.2 (arm64)
--
-- Host: 127.0.0.1    Database: bot_marketplace
-- ------------------------------------------------------
-- Server version	8.0.42

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `bot_categories`
--

DROP TABLE IF EXISTS `bot_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bot_categories` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bot_categories`
--

LOCK TABLES `bot_categories` WRITE;
/*!40000 ALTER TABLE `bot_categories` DISABLE KEYS */;
INSERT INTO `bot_categories` VALUES (1,'Technical Analysis','Bots based on technical indicators and chart patterns'),(2,'Machine Learning','AI-powered bots using machine learning algorithms'),(3,'Arbitrage','Bots that exploit price differences across exchanges'),(4,'Trend Following','Bots that follow market trends'),(5,'Mean Reversion','Bots that trade on price reversals'),(6,'High Frequency','Ultra-fast trading bots'),(7,'Portfolio Management','Bots that manage multiple positions');
/*!40000 ALTER TABLE `bot_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bot_files`
--

DROP TABLE IF EXISTS `bot_files`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bot_files` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bot_id` int NOT NULL,
  `file_type` varchar(50) DEFAULT NULL,
  `file_name` varchar(255) DEFAULT NULL,
  `file_path` varchar(500) DEFAULT NULL,
  `file_size` int DEFAULT NULL,
  `file_hash` varchar(64) DEFAULT NULL,
  `version` varchar(50) DEFAULT '1.0.0',
  `description` text,
  `model_framework` varchar(50) DEFAULT NULL,
  `model_type` varchar(50) DEFAULT NULL,
  `input_shape` json DEFAULT NULL,
  `output_shape` json DEFAULT NULL,
  `upload_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `bot_id` (`bot_id`),
  CONSTRAINT `bot_files_ibfk_1` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bot_files`
--

LOCK TABLES `bot_files` WRITE;
/*!40000 ALTER TABLE `bot_files` DISABLE KEYS */;
INSERT INTO `bot_files` VALUES (1,1,'PYTHON_SCRIPT','binance_futures_bot.py','bot_files/binance_futures_bot.py',40191,NULL,'2.0.0','Binance Futures trading bot with LLM integration',NULL,NULL,NULL,NULL,'2025-08-01 23:55:07',1),(3,1,'code','binance_futures_bot.py','bot_files/binance_futures_bot.py',40191,NULL,'2.0.0','Binance Futures Bot Code',NULL,NULL,NULL,NULL,'2025-08-02 00:41:54',1);
/*!40000 ALTER TABLE `bot_files` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bot_performance`
--

DROP TABLE IF EXISTS `bot_performance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bot_performance` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bot_id` int NOT NULL,
  `period_start` datetime DEFAULT NULL,
  `period_end` datetime DEFAULT NULL,
  `total_subscribers` int DEFAULT '0',
  `active_subscribers` int DEFAULT '0',
  `total_trades` int DEFAULT '0',
  `winning_trades` int DEFAULT '0',
  `win_rate` float DEFAULT '0',
  `average_pnl` decimal(15,8) DEFAULT '0.00000000',
  `total_pnl` decimal(15,8) DEFAULT '0.00000000',
  `max_drawdown` float DEFAULT '0',
  `sharpe_ratio` float DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bot_id` (`bot_id`),
  CONSTRAINT `bot_performance_ibfk_1` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bot_performance`
--

LOCK TABLES `bot_performance` WRITE;
/*!40000 ALTER TABLE `bot_performance` DISABLE KEYS */;
/*!40000 ALTER TABLE `bot_performance` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bot_pricing_plans`
--

DROP TABLE IF EXISTS `bot_pricing_plans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bot_pricing_plans` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bot_id` int NOT NULL,
  `plan_name` varchar(100) NOT NULL,
  `plan_description` text,
  `price_per_month` decimal(10,2) DEFAULT '0.00',
  `price_per_year` decimal(10,2) DEFAULT '0.00',
  `price_per_quarter` decimal(10,2) DEFAULT '0.00',
  `max_trading_pairs` int DEFAULT '1',
  `max_daily_trades` int DEFAULT '10',
  `max_position_size` decimal(5,2) DEFAULT '0.10',
  `advanced_features` json DEFAULT NULL,
  `trial_days` int DEFAULT '0',
  `trial_trades_limit` int DEFAULT '5',
  `is_active` tinyint(1) DEFAULT '1',
  `is_popular` tinyint(1) DEFAULT '0',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_bot_pricing_plans_bot_id` (`bot_id`),
  CONSTRAINT `bot_pricing_plans_ibfk_1` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bot_pricing_plans`
--

LOCK TABLES `bot_pricing_plans` WRITE;
/*!40000 ALTER TABLE `bot_pricing_plans` DISABLE KEYS */;
INSERT INTO `bot_pricing_plans` VALUES (1,1,'Free Plan','Basic trading features with limited functionality',0.00,0.00,0.00,1,10,0.10,NULL,0,5,1,0,'2025-08-01 23:35:18','2025-08-01 23:35:18'),(2,1,'Pro Plan','Advanced features with higher limits',9.99,0.00,0.00,1,10,0.10,NULL,0,5,1,0,'2025-08-01 23:35:18','2025-08-01 23:35:18'),(3,2,'Free Plan','Basic trading features with limited functionality',0.00,0.00,0.00,1,10,0.10,NULL,0,5,1,0,'2025-08-01 23:35:18','2025-08-01 23:35:18'),(4,2,'Pro Plan','Advanced features with higher limits',9.99,0.00,0.00,1,10,0.10,NULL,0,5,1,0,'2025-08-01 23:35:18','2025-08-01 23:35:18'),(5,3,'Free Plan','Basic trading features with limited functionality',0.00,0.00,0.00,1,10,0.10,NULL,0,5,1,0,'2025-08-01 23:35:18','2025-08-01 23:35:18'),(6,3,'Pro Plan','Advanced features with higher limits',9.99,0.00,0.00,1,10,0.10,NULL,0,5,1,0,'2025-08-01 23:35:18','2025-08-01 23:35:18');
/*!40000 ALTER TABLE `bot_pricing_plans` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bot_promotions`
--

DROP TABLE IF EXISTS `bot_promotions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bot_promotions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bot_id` int NOT NULL,
  `promotion_code` varchar(50) NOT NULL,
  `promotion_name` varchar(100) NOT NULL,
  `promotion_description` text,
  `discount_type` varchar(20) NOT NULL,
  `discount_value` decimal(10,2) NOT NULL,
  `max_uses` int DEFAULT '100',
  `used_count` int DEFAULT '0',
  `valid_from` datetime DEFAULT NULL,
  `valid_until` datetime DEFAULT NULL,
  `min_subscription_months` int DEFAULT '1',
  `applicable_plans` json DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `promotion_code` (`promotion_code`),
  KEY `created_by` (`created_by`),
  KEY `idx_bot_promotions_bot_id` (`bot_id`),
  CONSTRAINT `bot_promotions_ibfk_1` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE,
  CONSTRAINT `bot_promotions_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bot_promotions`
--

LOCK TABLES `bot_promotions` WRITE;
/*!40000 ALTER TABLE `bot_promotions` DISABLE KEYS */;
/*!40000 ALTER TABLE `bot_promotions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bot_reviews`
--

DROP TABLE IF EXISTS `bot_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bot_reviews` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `bot_id` int NOT NULL,
  `rating` int NOT NULL,
  `review_text` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `bot_id` (`bot_id`),
  CONSTRAINT `bot_reviews_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `bot_reviews_ibfk_2` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bot_reviews`
--

LOCK TABLES `bot_reviews` WRITE;
/*!40000 ALTER TABLE `bot_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `bot_reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `bots`
--

DROP TABLE IF EXISTS `bots`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `description` text,
  `developer_id` int NOT NULL,
  `category_id` int DEFAULT NULL,
  `status` enum('PENDING','APPROVED','REJECTED','ARCHIVED') DEFAULT 'PENDING',
  `code_path` varchar(500) DEFAULT NULL,
  `version` varchar(50) DEFAULT '1.0.0',
  `bot_type` varchar(50) DEFAULT 'TECHNICAL',
  `model_path` varchar(500) DEFAULT NULL,
  `model_metadata` json DEFAULT NULL,
  `price_per_month` decimal(10,2) DEFAULT '0.00',
  `is_free` tinyint(1) DEFAULT '1',
  `total_subscribers` int DEFAULT '0',
  `average_rating` float DEFAULT '0',
  `total_reviews` int DEFAULT '0',
  `config_schema` json DEFAULT NULL,
  `default_config` json DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `approved_at` datetime DEFAULT NULL,
  `approved_by` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `category_id` (`category_id`),
  KEY `approved_by` (`approved_by`),
  KEY `idx_bots_developer_id` (`developer_id`),
  KEY `idx_bots_status` (`status`),
  CONSTRAINT `bots_ibfk_1` FOREIGN KEY (`developer_id`) REFERENCES `users` (`id`),
  CONSTRAINT `bots_ibfk_2` FOREIGN KEY (`category_id`) REFERENCES `bot_categories` (`id`),
  CONSTRAINT `bots_ibfk_3` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `bots`
--

LOCK TABLES `bots` WRITE;
/*!40000 ALTER TABLE `bots` DISABLE KEYS */;
INSERT INTO `bots` VALUES (1,'Binance Futures LLM Bot','Advanced Binance Futures trading bot with LLM integration, leverage, stop loss, and take profit features',5,1,'APPROVED','bot_files/binance_futures_bot.py','2.0.0','FUTURES',NULL,NULL,0.00,1,1,0,0,NULL,NULL,'2025-08-01 23:35:18','2025-08-07 23:07:45',NULL,NULL),(2,'RSI Divergence Bot','RSI divergence detection for reversal trading',2,1,'APPROVED',NULL,'1.0.0','TECHNICAL',NULL,NULL,0.00,1,1,0,0,NULL,NULL,'2025-08-01 23:35:18','2025-08-01 23:35:18',NULL,NULL),(3,'MACD Signal Bot','MACD signal generation for momentum trading',2,1,'APPROVED',NULL,'1.0.0','TECHNICAL',NULL,NULL,0.00,1,0,0,0,NULL,NULL,'2025-08-01 23:35:18','2025-08-01 23:35:18',NULL,NULL),(4,'Binance Spot Trading Bot','Professional spot trading bot with risk management for BTC, ETH, and major altcoins',5,1,'APPROVED',NULL,'1.0.0','TECHNICAL',NULL,'null',1.50,0,0,0,0,'{\"symbols\": [\"BTCUSDT\", \"ETHUSDT\", \"ADAUSDT\"], \"exchanges\": [\"BINANCE\"], \"risk_level\": \"low\"}','{\"trading_mode\": \"spot\", \"stop_loss_pct\": 0.02, \"take_profit_pct\": 0.05, \"max_position_size\": 0.1}','2025-08-12 07:50:49','2025-08-12 07:50:49','2025-08-12 07:50:50',5);
/*!40000 ALTER TABLE `bots` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `exchange_credentials`
--

DROP TABLE IF EXISTS `exchange_credentials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exchange_credentials` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `principal_id` varchar(255) DEFAULT NULL,
  `exchange` enum('BINANCE','COINBASE','KRAKEN') NOT NULL,
  `api_key` varchar(255) NOT NULL,
  `api_secret` varchar(255) NOT NULL,
  `api_passphrase` varchar(255) DEFAULT NULL,
  `is_testnet` tinyint(1) DEFAULT '1',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `last_validated` datetime DEFAULT NULL,
  `validation_status` varchar(50) DEFAULT 'pending',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_exchange` (`user_id`,`exchange`,`is_testnet`),
  KEY `idx_exchange_credentials_user_id` (`user_id`),
  KEY `idx_exchange_credentials_principal_id` (`principal_id`),
  KEY `idx_exchange_credentials_principal_exchange_testnet` (`principal_id`,`exchange`,`is_testnet`),
  CONSTRAINT `exchange_credentials_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chk_user_or_principal` CHECK ((((`user_id` is not null) and (`principal_id` is null)) or ((`user_id` is null) and (`principal_id` is not null))))
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchange_credentials`
--

LOCK TABLES `exchange_credentials` WRITE;
/*!40000 ALTER TABLE `exchange_credentials` DISABLE KEYS */;
INSERT INTO `exchange_credentials` VALUES (1,1,NULL,'BINANCE','test_api_key_1','test_api_secret_1',NULL,1,1,'2025-08-01 23:35:18','2025-08-01 23:35:18',NULL,'valid'),(2,1,NULL,'BINANCE','test_api_key_2','test_api_secret_2',NULL,0,1,'2025-08-01 23:35:18','2025-08-01 23:35:18',NULL,'valid'),(3,3,NULL,'BINANCE','test_binance_api_key_testnet','test_binance_api_secret_testnet',NULL,1,1,'2025-08-02 00:03:56','2025-08-02 00:04:14','2025-08-02 00:04:14','invalid'),(4,4,NULL,'BINANCE','Z0FBQUFBQm9rVG9zWm40VWs2MTBoSFFyWGgybURfNVJSR3V1LWlPbm5lVGJEWnFCVERIV2dNZFJ3QUp5bFY1ZkxUcm5jYXh3dWhnWWxoLWlhUFBPNGh2RDFGeXJKNEl1UFdQeDV4VDdCUU4tQ3BMNDBrOC1KSUZUamNabmRzNVcxbFpieEpiaGJYSVpjb0RlT0NhelBzN0lTYlhrRENOa1puN2o5R0pPYzVvNk9xc1o3OEVkaWE4PQ==','Z0FBQUFBQm9rVG94WDBRTkJDemxaU2pWZ0RLbFJwV21rMlVyVmFkVVVkaUZ3bWdqVWZRRG9hY1V3VVYzX2JUNzdlOU02cWdwNmI5MDhTTm1namREOHBuYnFxM0ZPdTgxSlMta3FJT0RoQmkzQ2s5UUNsYzJpSU5MOVl5dzFLWW9CSmd2QllzSlJfeWpmU2V1ZVJKMF9KV0tiaXpPaUNZNlNwbFBSTTRIZ2J2QjNORUhyYWdRT0o4PQ==',NULL,1,1,'2025-08-03 03:59:47','2025-08-04 22:55:03',NULL,'pending'),(5,NULL,'ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bqe','BINANCE','Z0FBQUFBQm9rLVN4Z3BZeHA4dU5TanBaRGhEOGR1bjUyU1JkdWxIM2ZWY0R2OVBUNGJGMkZHUk93cjNZMllXV0gwVDFPY0N5b2FVYzRJN0J3eFlvMV80ZjhYakI3Rno5TmNzdkg2d3pKZ3FRUVE2TnY4VEllUzkxV19pTkw2eTNRcVZBdEtRMnNwWDBhNl9IRDhOOHNZVkI5Y1F4QWxPekUtREJhNUFvNmNlTndGVlMtVmY1UnpJPQ==','Z0FBQUFBQm9rLVN4LWxPX183djRQaHF5LTNYNUdIbnozTV9DYkRJcVduU01QWWxqRV9TV2JTQXdBejdCSVZhaDA5Rkw1UmttWjZWLXZmTEptWlJxbUc0OHhCNmlNUkJBNlZ4V05EQ3J4SzBnS2oteUUxTElSbHNRZUt2TkhrSUVvekN3RkVaMS1nNzlUeTIwUXRucDlHcE0wQnY2RjBUUDIybTNGU2FqSGpTR2xOQW85NE9aWUpNPQ==',NULL,1,1,'2025-08-06 01:43:41','2025-08-06 23:26:41',NULL,'pending'),(6,NULL,'debug_principal','BINANCE','Z0FBQUFBQm9tQWdxMnVIaHNxcG5BTHIzUGNIMmkyTWF5YkFCa21OZS1fRHpxU0szaVhhOXB5ZWczNDNDQWZLSkdNbF80dXU3U193SS01WEdmTmtKOENXc0luRHlCQ1JWa3c9PQ==','Z0FBQUFBQm9tQWdxc04yck15OTJSTXl0VmMyUjQ4X2ktVWNFeUlaMnQ5YVhOQ2JOS3J3S3hBYU83SERNZm5VaUsxb0traGlETWRDZ0Q4RF9rRUh2bUtUVzNVTWJuZ2pZVnc9PQ==',NULL,1,1,'2025-08-10 02:47:06','2025-08-10 02:47:06',NULL,'pending'),(7,NULL,'bkwke-64bo2-yipx4-f4zbn-olkgc-tcu2b-pvlsr-wrekw-ahu22-43z25-oqe','BINANCE','Z0FBQUFBQm9tRUlfZzJ4czRQeVItdTNqQVlSVDl0QmN6QnRocWp1cHBhM2FjX1FzaFVDSTNzRGFmY3k5RFdidHlJUmxkbVBJNC10aTdmaG91bzN1VWJwTktJVmg3Y3poSmc9PQ==','Z0FBQUFBQm9tRUlfclEyWGJFVmNfUFJsc1g0Q3A2NUcwTWc4TnpxSTV5ZUxhWUl6MExjVlBfaXJpVnpGVDhUYnZkZ2pqX2FRbnFHRjUzWGFiam1TVXhIQzJuYjBwQUM2Wmc9PQ==',NULL,1,1,'2025-08-10 06:52:33','2025-08-10 06:54:55',NULL,'pending'),(8,NULL,'bkwke-64bo2-yipx4-f4zbn-olkgc-tcu2b-pvlsr-wrekw-ahu22-43z25-oqe','BINANCE','Z0FBQUFBQm9tRUlfZ0tRdUx6dW9PMGRvN0RwaDV2eVE4d3FFdmhiMWJVdWFlUTEtQ1NLaUFLR0ZMbzdsUjhHUXpUTW04aHNmcGpsaXNJRldzNGI4VmNHcDByQ0s1VmdJaUE9PQ==','Z0FBQUFBQm9tRUlfTC1vUFZ5a3V4c1BTd2cxT09PT3Etc0pHSkpMQWhRb1hwY2IxZFlUNzlQaEF2eVdjSnh5Sy1pbWVVS3dJSVVrS0VXZTRqdi1ucy1fcE50bkZQc1ZpR0E9PQ==',NULL,0,1,'2025-08-10 06:52:33','2025-08-10 06:54:55',NULL,'pending'),(9,NULL,'hnymd-a264o-r3pns-3u62v-o2r4e-tnmic-qh77e-leh2u-x6u2y-nwjgr-3qe','BINANCE','Z0FBQUFBQm9tTElPRkNSUkVtY3pBWll5a3VqMFpnT0EtaTd3LXBqcHdkVDlSbmhUdW9hZHdmZ1NQN1kxUExzWXA4TWtGUS1TXzBMRUUxUm90b3BXTUUyWi1FR1YzV1laZGc9PQ==','Z0FBQUFBQm9tTElPZ2FNQk5vWi1CZF9hY19kVE1yWE5yMDJ6UnhGaFBVNFFqeVJKbDE5TklnWUN6SGo0RkFXaWVPRl9XZVM4TzlfWGNabEdvZ2FXeHJNb2FEQXBxMFFreGc9PQ==',NULL,0,1,'2025-08-10 14:51:58','2025-08-10 14:51:58',NULL,'pending'),(10,NULL,'nw247-ow7db-2svhx-uh6w7-cvsn4-lntvw-vexz3-rgxqp-z3236-2bg2i-kae','BINANCE','Z0FBQUFBQm9tVW9WTC1CX05qd3YwU0xZNUlrcHRUM21vc0lIdmNsTlRka2tOUXFaa3dTX2tHcHkzU1NtT1lOcWpoOUthZ19uWWM4cTZyZ1k3Z1Brck91NTg5bkp2dWVsYWc9PQ==','Z0FBQUFBQm9tVW9WWmhSQ20xXzdZOEVLOHV4T1N5eTN2X2JXcjRwbll5dzhnSTRBbDBXV1VPNmx4SUZBb29Pdi1rY1d6VXluMlJQWGZoSHNvMzNSUlZQSXJ2UFhRZ1hkSGc9PQ==',NULL,1,1,'2025-08-11 01:40:37','2025-08-11 01:40:37',NULL,'pending'),(11,NULL,'c57tc-sdknt-ghi5r-k4q43-5fhgv-desnp-bktug-zvds3-kw6zf-s3kuk-tae','BINANCE','Z0FBQUFBQm9tYVB5WlJkWGwxaG5Jb2VRYWVrLUNOSHByS3M3a2NhZ2ZtRndxUVM2RldhQmtPaHR4RzVVX1JaTXpJN2d5ZmV2WGFLMDFxZFV4aHZCWnhXR3p0MjI0MXVlUkE9PQ==','Z0FBQUFBQm9tYVB5a1RMblFKbDNDYWZhMjA2RXE5MGtxSWF2dEdHLVduYzIxenpEUzFnUVRiWDhBemJLN0w1YkJGUUcyZVJyT3cxaW5pWHlRajRhNXg1aGNrLTRva3lkRFE9PQ==',NULL,1,1,'2025-08-11 08:04:02','2025-08-11 08:04:02',NULL,'pending'),(12,NULL,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae','BINANCE','Z0FBQUFBQm9tYXV5amFmNG1oRWxlNDNTSW9mX2cxMXN6NE5sYkhHRFVFTnpJRnp3Q1ZsaDZKbTBzZWJVTFZMbzBjYnNtQmFJU0lrWnlucmVicWFXR3dxS0g3ejB0b2JpZXc9PQ==','Z0FBQUFBQm9tYXV5d2o2ZE0xd3Z1X1RWdnZxVWJsb1RlRnlxSFZTZFJCd2tPRTVkdjI1RkRMV2NPeV9uU29qQ2NiQXRKSEJpMi1DcU5KaFJyQ1RqZHdzWjZlMGZIZGJYR0E9PQ==',NULL,1,1,'2025-08-11 08:37:06','2025-08-11 08:37:06',NULL,'pending');
/*!40000 ALTER TABLE `exchange_credentials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payments`
--

DROP TABLE IF EXISTS `payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int DEFAULT NULL,
  `subscription_id` int DEFAULT NULL,
  `amount` decimal(10,2) DEFAULT NULL,
  `currency` varchar(10) DEFAULT NULL,
  `payment_method` varchar(50) DEFAULT NULL,
  `payment_status` varchar(50) DEFAULT NULL,
  `payment_provider` varchar(50) DEFAULT NULL,
  `external_payment_id` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `processed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  KEY `subscription_id` (`subscription_id`),
  CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `payments_ibfk_2` FOREIGN KEY (`subscription_id`) REFERENCES `subscriptions` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payments`
--

LOCK TABLES `payments` WRITE;
/*!40000 ALTER TABLE `payments` DISABLE KEYS */;
/*!40000 ALTER TABLE `payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `paypal_config`
--

DROP TABLE IF EXISTS `paypal_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paypal_config` (
  `id` int NOT NULL AUTO_INCREMENT,
  `environment` enum('SANDBOX','LIVE') DEFAULT NULL,
  `client_id` varchar(255) NOT NULL,
  `client_secret` varchar(500) NOT NULL,
  `webhook_id` varchar(255) DEFAULT NULL,
  `webhook_secret` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_paypal_config_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paypal_config`
--

LOCK TABLES `paypal_config` WRITE;
/*!40000 ALTER TABLE `paypal_config` DISABLE KEYS */;
INSERT INTO `paypal_config` VALUES (1,'SANDBOX','REPLACE_WITH_SANDBOX_CLIENT_ID','REPLACE_WITH_SANDBOX_CLIENT_SECRET',NULL,NULL,1,'2025-08-14 01:02:49','2025-08-14 01:02:49'),(2,'SANDBOX','REPLACE_WITH_SANDBOX_CLIENT_ID','REPLACE_WITH_SANDBOX_CLIENT_SECRET',NULL,NULL,1,'2025-08-14 06:55:35','2025-08-14 06:55:35');
/*!40000 ALTER TABLE `paypal_config` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `paypal_payment_summary`
--

DROP TABLE IF EXISTS `paypal_payment_summary`;
/*!50001 DROP VIEW IF EXISTS `paypal_payment_summary`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `paypal_payment_summary` AS SELECT 
 1 AS `id`,
 1 AS `user_principal_id`,
 1 AS `bot_name`,
 1 AS `amount_usd`,
 1 AS `status`,
 1 AS `created_at`,
 1 AS `completed_at`,
 1 AS `rental_id`,
 1 AS `overall_status`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `paypal_payments`
--

DROP TABLE IF EXISTS `paypal_payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paypal_payments` (
  `id` varchar(255) NOT NULL,
  `order_id` varchar(255) NOT NULL,
  `user_principal_id` varchar(255) NOT NULL,
  `bot_id` int NOT NULL,
  `duration_days` int NOT NULL,
  `pricing_tier` varchar(50) NOT NULL,
  `amount_usd` decimal(10,2) NOT NULL,
  `amount_icp_equivalent` decimal(18,8) NOT NULL,
  `exchange_rate_usd_to_icp` decimal(18,8) NOT NULL,
  `status` enum('PENDING','APPROVED','COMPLETED','CANCELLED','FAILED','COMPLETED_PENDING_RENTAL') DEFAULT NULL,
  `paypal_order_id` varchar(255) DEFAULT NULL,
  `paypal_payment_id` varchar(255) DEFAULT NULL,
  `paypal_payer_id` varchar(255) DEFAULT NULL,
  `paypal_approval_url` varchar(500) DEFAULT NULL,
  `payer_email` varchar(255) DEFAULT NULL,
  `payer_name` varchar(255) DEFAULT NULL,
  `payer_country_code` varchar(5) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  `completed_at` datetime DEFAULT NULL,
  `rental_id` varchar(255) DEFAULT NULL,
  `error_message` text,
  `retry_count` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `order_id` (`order_id`),
  KEY `bot_id` (`bot_id`),
  KEY `ix_paypal_payments_paypal_order_id` (`paypal_order_id`),
  KEY `ix_paypal_payments_user_principal_id` (`user_principal_id`),
  CONSTRAINT `paypal_payments_ibfk_1` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paypal_payments`
--

LOCK TABLES `paypal_payments` WRITE;
/*!40000 ALTER TABLE `paypal_payments` DISABLE KEYS */;
INSERT INTO `paypal_payments` VALUES ('paypal_019e8bd85382','order_1755215800','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.68,2.50000000,5.47000000,'FAILED','PAYID-NCPHPPA12E183623M489352V',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-1TA969793D259962R',NULL,NULL,NULL,'2025-08-14 23:56:44','2025-08-14 23:57:43','2025-08-15 00:56:44',NULL,NULL,'PayPal execution failed: {\'name\': \'PAYMENT_ALREADY_DONE\', \'message\': \'Payment has been done already for this cart.\', \'information_link\': \'https://developer.paypal.com/docs/api/payments/v1/#error-PAYMENT_ALREADY_DONE\', \'debug_id\': \'efcef2e01df15\'}',0),('paypal_0332ea7238c5','order_1755220300','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.62,2.50000000,5.45000000,'COMPLETED','PAYID-NCPISTY4RM54457KN716105W','PAYID-NCPISTY4RM54457KN716105W','9AUX394F9T93J','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-5M474305RA796211F',NULL,NULL,NULL,'2025-08-15 01:11:43','2025-08-15 01:15:05','2025-08-15 02:11:44','2025-08-15 01:11:54','paypal_rental_paypal_0332ea7238c5_1755220314','Studio sync successful: Subscription created successfully from PayPal payment',0),('paypal_04e7f13363e8','order_1755215922','wcup6-pbb5f-tewqx-tykmj-p24sp-3nzr-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.68,2.50000000,5.47000000,'PENDING','PAYID-NCPHQNI0BR80762WS5127938',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-8AD09945PU739025A',NULL,NULL,NULL,'2025-08-14 23:58:45','2025-08-14 23:58:45','2025-08-15 00:58:46',NULL,NULL,NULL,0),('paypal_0b0c57e17b50','order_1755219673','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.65,2.50000000,5.46000000,'COMPLETED','PAYID-NCPINWY7PD69616HN210084H','PAYID-NCPINWY7PD69616HN210084H','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-1BM99030SN1545105',NULL,NULL,NULL,'2025-08-15 01:01:15','2025-08-15 01:01:27','2025-08-15 02:01:16','2025-08-15 01:01:28','paypal_rental_paypal_0b0c57e17b50_1755219687',NULL,0),('paypal_0e5f0e73c282','order_1755219881','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.60,2.50000000,5.44000000,'COMPLETED','PAYID-NCPIPLA2KE03877CJ073321C','PAYID-NCPIPLA2KE03877CJ073321C','9AUX394F9T93J','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-81927666VN590931S',NULL,NULL,NULL,'2025-08-15 01:04:44','2025-08-15 01:12:25','2025-08-15 02:04:44','2025-08-15 01:05:15','paypal_rental_paypal_0e5f0e73c282_1755219915','Studio sync failed: Studio API returned 500: {\"detail\":\"Failed to create subscription: \'starts_at\' is an invalid keyword argument for Subscription\"}',0),('paypal_16abe18a7a82','order_1755216385','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.62,2.50000000,5.45000000,'COMPLETED','PAYID-NCPHUBA7AG05743X6582552X','PAYID-NCPHUBA7AG05743X6582552X',NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-7ND17126EM431054W',NULL,NULL,NULL,'2025-08-15 00:06:28','2025-08-15 00:12:11','2025-08-15 01:06:29','2025-08-15 00:12:12','paypal_rental_paypal_16abe18a7a82_1755216731',NULL,0),('paypal_18d275ae32d0','order_1755214757','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.70,2.50000000,5.48000000,'PENDING','PAYID-NCPHHKA9E84386160693423M',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-4U9415426V083402F',NULL,NULL,NULL,'2025-08-14 23:39:20','2025-08-14 23:39:20','2025-08-15 00:39:21',NULL,NULL,NULL,0),('paypal_2e1f52517e6e','order_1755217450','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.65,2.50000000,5.46000000,'COMPLETED','PAYID-NCPH4LI6EM11332T1814991B','PAYID-NCPH4LI6EM11332T1814991B','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-88H51311C1423731K',NULL,NULL,NULL,'2025-08-15 00:24:13','2025-08-15 00:24:40','2025-08-15 01:24:13','2025-08-15 00:24:27','paypal_rental_paypal_2e1f52517e6e_1755217480',NULL,0),('paypal_31f7ce425cab','order_1755230439','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.82,2.50000000,5.53000000,'COMPLETED','PAYID-NCPLB2Q9WD46855RS415061E','PAYID-NCPLB2Q9WD46855RS415061E','9AUX394F9T93J','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-41P55489D3047143N',NULL,NULL,NULL,'2025-08-15 04:00:42','2025-08-15 04:00:57','2025-08-15 05:00:42','2025-08-15 04:00:52','paypal_rental_paypal_31f7ce425cab_1755230452','Studio sync successful: Subscription created successfully from PayPal payment',0),('paypal_347d7026f1ca','order_1755218624','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.62,2.50000000,5.45000000,'COMPLETED','PAYID-NCPIFRA4K173581AB6534809','PAYID-NCPIFRA4K173581AB6534809','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-08U35721AB101062F',NULL,NULL,NULL,'2025-08-15 00:43:48','2025-08-15 00:43:59','2025-08-15 01:43:48','2025-08-15 00:43:59','paypal_rental_paypal_347d7026f1ca_1755218639',NULL,0),('paypal_3a81a5ead84b','order_1755216765','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.65,2.50000000,5.46000000,'COMPLETED','PAYID-NCPHXAA7UR18624UU341411S','PAYID-NCPHXAA7UR18624UU341411S',NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-2A233598H80613614',NULL,NULL,NULL,'2025-08-15 00:12:48','2025-08-15 00:23:22','2025-08-15 01:12:49','2025-08-15 00:13:09','paypal_rental_paypal_3a81a5ead84b_1755217402',NULL,0),('paypal_3b41ce41adfd','order_1755213527','csskt-aqfic-ppxxy-6puty-72qzp-zszje-lweuc-i74tu-deuuy-2vb62-oae',1,30,'daily',409.50,75.00000000,5.46000000,'PENDING','PAYID-NCPG5WQ970313730L648193S',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-9F79115507560192X',NULL,NULL,NULL,'2025-08-14 23:18:50','2025-08-14 23:18:50','2025-08-15 00:18:50',NULL,NULL,NULL,0),('paypal_46a5d1be876c','order_1755215278','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.68,2.50000000,5.47000000,'FAILED','PAYID-NCPHLMQ1U6299752R968492S',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-66050145BN476994T',NULL,NULL,NULL,'2025-08-14 23:48:02','2025-08-14 23:48:21','2025-08-15 00:48:02',NULL,NULL,'PayPal execution failed: {\'name\': \'PAYMENT_ALREADY_DONE\', \'message\': \'Payment has been done already for this cart.\', \'information_link\': \'https://developer.paypal.com/docs/api/payments/v1/#error-PAYMENT_ALREADY_DONE\', \'debug_id\': \'a11cf8fc60d1b\'}',0),('paypal_5ea0eed98f16','order_1755219227','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.68,2.50000000,5.47000000,'COMPLETED','PAYID-NCPIKHQ5E107935M9704215T','PAYID-NCPIKHQ5E107935M9704215T','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-82095815DA870461F',NULL,NULL,NULL,'2025-08-15 00:53:50','2025-08-15 00:54:13','2025-08-15 01:53:51','2025-08-15 00:54:01','paypal_rental_paypal_5ea0eed98f16_1755219241','Studio sync failed: Studio API returned 404: ',0),('paypal_5ee3bf40f59b','order_1755219559','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.65,2.50000000,5.46000000,'COMPLETED','PAYID-NCPIM2Y3BH87549GL125802B','PAYID-NCPIM2Y3BH87549GL125802B','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-72Y8301598827583M',NULL,NULL,NULL,'2025-08-15 00:59:23','2025-08-15 00:59:44','2025-08-15 01:59:24','2025-08-15 00:59:34','paypal_rental_paypal_5ee3bf40f59b_1755219574','Studio sync failed: Studio API returned 404: ',0),('paypal_612e8fb54d73','order_1755218728','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.62,2.50000000,5.45000000,'COMPLETED','PAYID-NCPIGLA2EC52681AW390882G','PAYID-NCPIGLA2EC52681AW390882G','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-2AT583366B083994A',NULL,NULL,NULL,'2025-08-15 00:45:32','2025-08-15 00:45:43','2025-08-15 01:45:32','2025-08-15 00:45:43','paypal_rental_paypal_612e8fb54d73_1755218743',NULL,0),('paypal_62c2cf0f0615','order_1755216872','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.65,2.50000000,5.46000000,'COMPLETED','PAYID-NCPHX2Y72J7951050081734V','PAYID-NCPHX2Y72J7951050081734V',NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-1EJ80234XC461811U',NULL,NULL,NULL,'2025-08-15 00:14:35','2025-08-15 00:16:46','2025-08-15 01:14:36','2025-08-15 00:16:46','paypal_rental_paypal_62c2cf0f0615_1755217006',NULL,0),('paypal_66260e50ba02','order_1755214557','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.70,2.50000000,5.48000000,'PENDING','PAYID-NCPHFYI45A67746J58732707',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-32C867708W5318814',NULL,NULL,NULL,'2025-08-14 23:36:01','2025-08-14 23:36:01','2025-08-15 00:36:01',NULL,NULL,NULL,0),('paypal_6c4a5e074392','order_1755217107','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.68,2.50000000,5.47000000,'COMPLETED','PAYID-NCPHZVQ0V5518335Y969420F','PAYID-NCPHZVQ0V5518335Y969420F',NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-46P9792569372335J',NULL,NULL,NULL,'2025-08-15 00:18:31','2025-08-15 00:19:00','2025-08-15 01:18:31','2025-08-15 00:18:54','paypal_rental_paypal_6c4a5e074392_1755217141',NULL,0),('paypal_7558a4b7bdf4','order_1755217417','wcup6-pbb5f-tewqx-tykmj-p24sp-3nzr-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.65,2.50000000,5.46000000,'PENDING','PAYID-NCPH4DA9DL03384450315106',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-6JX332488K586262J',NULL,NULL,NULL,'2025-08-15 00:23:40','2025-08-15 00:23:40','2025-08-15 01:23:41',NULL,NULL,NULL,0),('paypal_7c4182c8244d','order_1755217831','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.62,2.50000000,5.45000000,'COMPLETED','PAYID-NCPH7KY5SH01193XP3996912','PAYID-NCPH7KY5SH01193XP3996912','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-21G35721S45987846',NULL,NULL,NULL,'2025-08-15 00:30:35','2025-08-15 00:30:51','2025-08-15 01:30:35','2025-08-15 00:30:51','paypal_rental_paypal_7c4182c8244d_1755217851',NULL,0),('paypal_90314358718d','order_1755231811','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.78,2.50000000,5.51000000,'COMPLETED','PAYID-NCPLMRQ9NM344235T771080P','PAYID-NCPLMRQ9NM344235T771080P','9AUX394F9T93J','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-82N9544767591680R',NULL,NULL,NULL,'2025-08-15 04:23:34','2025-08-15 04:34:38','2025-08-15 05:23:35','2025-08-15 04:23:53','paypal_rental_paypal_90314358718d_1755232478',NULL,0),('paypal_92245a37e78b','order_1755215874','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.68,2.50000000,5.47000000,'FAILED','PAYID-NCPHQBI9BD03425R98136107',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-6DN80132SX0188055',NULL,NULL,NULL,'2025-08-14 23:57:57','2025-08-15 00:00:37','2025-08-15 00:57:57',NULL,NULL,'PayPal execution failed: {\'name\': \'INVALID_PAYER_ID\', \'message\': \'Payer ID is invalid\', \'information_link\': \'https://developer.paypal.com/docs/api/payments/v1/#error-INVALID_PAYER_ID\', \'debug_id\': \'7c6e3cc3d0f6f\'}',0),('paypal_984ab27b73b0','order_1755216149','mjdcz-hj5hr-37via-lr3bf-4asqe-5gnvi-lewlh-3pkkh-i3h2t-z6ovp-iqe',1,1,'daily',13.62,2.50000000,5.45000000,'FAILED','PAYID-NCPHSGA26323900ML832383B',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-443634208C294374P',NULL,NULL,NULL,'2025-08-15 00:02:32','2025-08-15 00:06:17','2025-08-15 01:02:32',NULL,NULL,'PayPal execution failed: {\'name\': \'PAYMENT_ALREADY_DONE\', \'message\': \'Payment has been done already for this cart.\', \'information_link\': \'https://developer.paypal.com/docs/api/payments/v1/#error-PAYMENT_ALREADY_DONE\', \'debug_id\': \'2691cc805523d\'}',0),('paypal_9b9e9176d8cd','order_1755217181','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.68,2.50000000,5.47000000,'COMPLETED','PAYID-NCPH2IA0MG11166V0673135S','PAYID-NCPH2IA0MG11166V0673135S',NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-296478242L910411C',NULL,NULL,NULL,'2025-08-15 00:19:44','2025-08-15 00:22:48','2025-08-15 01:19:45','2025-08-15 00:22:48','paypal_rental_paypal_9b9e9176d8cd_1755217368',NULL,0),('paypal_a0863d290193','order_1755216002','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.68,2.50000000,5.47000000,'FAILED','PAYID-NCPHRBI0F9339532Y492335A',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-61P105637P634972J',NULL,NULL,NULL,'2025-08-15 00:00:05','2025-08-15 00:00:19','2025-08-15 01:00:05',NULL,NULL,'PayPal execution failed: {\'name\': \'PAYMENT_ALREADY_DONE\', \'message\': \'Payment has been done already for this cart.\', \'information_link\': \'https://developer.paypal.com/docs/api/payments/v1/#error-PAYMENT_ALREADY_DONE\', \'debug_id\': \'dee11a30463a5\'}',0),('paypal_a30f2ef2bc04','order_1755215411','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.68,2.50000000,5.47000000,'FAILED','PAYID-NCPHMNQ1U599138L8027121W',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-24306941T5691670F',NULL,NULL,NULL,'2025-08-14 23:50:14','2025-08-14 23:52:10','2025-08-15 00:50:14',NULL,NULL,'PayPal execution failed: {\'name\': \'INVALID_PAYER_ID\', \'message\': \'Payer ID is invalid\', \'information_link\': \'https://developer.paypal.com/docs/api/payments/v1/#error-INVALID_PAYER_ID\', \'debug_id\': \'aaaa9de0918d6\'}',0),('paypal_bdd910234754','order_1755219061','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.68,2.50000000,5.47000000,'COMPLETED','PAYID-NCPII6A2RN79558RT4713731','PAYID-NCPII6A2RN79558RT4713731','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-3LU01249TD4872136',NULL,NULL,NULL,'2025-08-15 00:51:04','2025-08-15 00:51:27','2025-08-15 01:51:05','2025-08-15 00:51:16','paypal_rental_paypal_bdd910234754_1755219076','Studio sync failed: Studio API returned 404: ',0),('paypal_bf1a701c4a32','order_1755229758','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.85,2.50000000,5.54000000,'COMPLETED','PAYID-NCPK4QI17X00098FS597494Y','PAYID-NCPK4QI17X00098FS597494Y','9AUX394F9T93J','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-2WM30774GX0198047',NULL,NULL,NULL,'2025-08-15 03:49:21','2025-08-15 03:49:46','2025-08-15 04:49:22','2025-08-15 03:49:41','paypal_rental_paypal_bf1a701c4a32_1755229781','Studio sync successful: Subscription created successfully from PayPal payment',0),('paypal_c96854096655','order_1755220541','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.62,2.50000000,5.45000000,'COMPLETED','PAYID-NCPIUQA8C7599622V292921C','PAYID-NCPIUQA8C7599622V292921C','9AUX394F9T93J','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-29D10158JM515983L',NULL,NULL,NULL,'2025-08-15 01:15:45','2025-08-15 01:16:01','2025-08-15 02:15:45','2025-08-15 01:15:56','paypal_rental_paypal_c96854096655_1755220556','Studio sync successful: Subscription created successfully from PayPal payment',0),('paypal_ddf3b29c5fb9','order_1755220240','wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',1,1,'daily',13.62,2.50000000,5.45000000,'COMPLETED','PAYID-NCPISFA6LD33088UY010750P','PAYID-NCPISFA6LD33088UY010750P','9AUX394F9T93J','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-5F325526JH234180K',NULL,NULL,NULL,'2025-08-15 01:10:44','2025-08-15 01:18:32','2025-08-15 02:10:44','2025-08-15 01:10:55','paypal_rental_paypal_ddf3b29c5fb9_1755220255','Studio sync successful: Subscription created successfully from PayPal payment',0),('paypal_e2411b872bc9','order_1755216654','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.65,2.50000000,5.46000000,'COMPLETED','PAYID-NCPHWEQ17R52173W99816519','PAYID-NCPHWEQ17R52173W99816519',NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-3K2205256Y810881W',NULL,NULL,NULL,'2025-08-15 00:10:58','2025-08-15 00:11:15','2025-08-15 01:10:58','2025-08-15 00:11:15','paypal_rental_paypal_e2411b872bc9_1755216675',NULL,0),('paypal_e27d3b738155','order_1755213690','wcup6-pbb5f-tewqx-tykmj-p24sp-3nzr-pfevf-34zwm-lqk2d-sy55u-rae',1,30,'daily',409.50,75.00000000,5.46000000,'PENDING','PAYID-NCPG67I49H22126SS812442C',NULL,NULL,'https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-70Y241930H671650S',NULL,NULL,NULL,'2025-08-14 23:21:33','2025-08-14 23:21:33','2025-08-15 00:21:34',NULL,NULL,NULL,0),('paypal_f0bb734f02df','order_1755218179','5p7lz-4ttxz-gworn-fevmd-rdq42-dnyio-ku2fw-jfwaf-sp3ba-owloy-aqe',1,1,'daily',13.62,2.50000000,5.45000000,'COMPLETED','PAYID-NCPICBQ1VS92460KT999813J','PAYID-NCPICBQ1VS92460KT999813J','GSG6KNKFUDVBY','https://www.sandbox.paypal.com/cgi-bin/webscr?cmd=_express-checkout&token=EC-7B719607AN276640Y',NULL,NULL,NULL,'2025-08-15 00:36:22','2025-08-15 00:36:33','2025-08-15 01:36:23','2025-08-15 00:36:33','paypal_rental_paypal_f0bb734f02df_1755218193',NULL,0);
/*!40000 ALTER TABLE `paypal_payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `paypal_webhook_events`
--

DROP TABLE IF EXISTS `paypal_webhook_events`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `paypal_webhook_events` (
  `id` varchar(255) NOT NULL,
  `event_type` varchar(100) NOT NULL,
  `event_data` json NOT NULL,
  `payment_id` varchar(255) DEFAULT NULL,
  `processed` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `payment_id` (`payment_id`),
  CONSTRAINT `paypal_webhook_events_ibfk_1` FOREIGN KEY (`payment_id`) REFERENCES `paypal_payments` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `paypal_webhook_events`
--

LOCK TABLES `paypal_webhook_events` WRITE;
/*!40000 ALTER TABLE `paypal_webhook_events` DISABLE KEYS */;
/*!40000 ALTER TABLE `paypal_webhook_events` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `performance_logs`
--

DROP TABLE IF EXISTS `performance_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `performance_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subscription_id` int NOT NULL,
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  `action` varchar(50) DEFAULT NULL,
  `price` decimal(15,8) DEFAULT NULL,
  `quantity` decimal(15,8) DEFAULT NULL,
  `balance` decimal(15,8) DEFAULT NULL,
  `signal_data` json DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `subscription_id` (`subscription_id`),
  CONSTRAINT `performance_logs_ibfk_1` FOREIGN KEY (`subscription_id`) REFERENCES `subscriptions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=102 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `performance_logs`
--

LOCK TABLES `performance_logs` WRITE;
/*!40000 ALTER TABLE `performance_logs` DISABLE KEYS */;
INSERT INTO `performance_logs` VALUES (42,22,'2025-08-06 01:26:14','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"Advanced workflow error: \'BinanceFuturesBot\' object has no attribute \'check_account_status\'. Value: 0.0. Price: $113651.87\"}'),(43,22,'2025-08-06 01:26:15','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"Advanced workflow error: \'BinanceFuturesBot\' object has no attribute \'check_account_status\'. Value: 0.0. Price: $113651.88\"}'),(44,23,'2025-08-06 01:46:20','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"Advanced workflow error: \'BinanceFuturesBot\' object has no attribute \'check_account_status\'. Value: 0.0. Price: $113827.17\"}'),(45,23,'2025-08-06 01:46:21','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"Advanced workflow error: \'BinanceFuturesBot\' object has no attribute \'check_account_status\'. Value: 0.0. Price: $113827.17\"}'),(46,22,'2025-08-06 03:29:35','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"LLM analysis error: OpenAI client not available. Value: 0.0. Price: $113427.32\"}'),(47,23,'2025-08-06 03:30:51','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"LLM analysis error: OpenAI client not available. Value: 0.0. Price: $113427.02\"}'),(48,22,'2025-08-06 03:57:07','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(49,23,'2025-08-06 03:57:13','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(50,22,'2025-08-06 04:29:36','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(51,22,'2025-08-06 04:54:33','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"[LLM-MULTI-TF] The 1h timeframe shows a downtrend with price between key Fibonacci levels, suggesting a potential reversal. The 4h timeframe indicates strong momentum but is overbought, suggesting caution. The 1d timeframe shows a downtrend with potential for reversal. Overall, a HOLD position is recommended until clearer signals emerge.. Value: 0.7. Price: $113428.77\"}'),(52,23,'2025-08-07 00:08:56','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"[LLM-MULTI-TF] The current price is between the 50% and 61.8% Fibonacci retracement levels, indicating a potential continuation of the uptrend. The daily MACD and RSI suggest bullish momentum, but the 1H and 4H indicators show mixed signals, warranting a cautious approach.. Value: 0.75. Price: $114903.24\"}'),(53,23,'2025-08-07 00:08:58','BUY',0.00000000,0.00000000,0.00000000,'{\"details\": \"[LLM-MULTI-TF] The current price is near the 61.8% Fibonacci retracement level, which is a significant support level in an uptrend. Technical indicators suggest oversold conditions in shorter timeframes, while the daily trend remains bullish. This presents a potential buying opportunity with a favorable risk/reward ratio.. Value: 0.75. Price: $114903.25\"}'),(54,22,'2025-08-07 00:08:59','HOLD',0.00000000,0.00000000,0.00000000,'{\"details\": \"[LLM-MULTI-TF] The current price is in a bullish trend across multiple timeframes, supported by moving averages and MACD. However, the overbought conditions in Stochastic RSI and decreasing volume suggest caution. Holding is recommended until a clearer breakout or reversal signal is observed.. Value: 0.7. Price: $114903.25\"}'),(55,22,'2025-08-07 00:09:02','BUY',0.00000000,0.00000000,0.00000000,'{\"details\": \"[LLM-MULTI-TF] The current price is positioned between the 50% and 61.8% Fibonacci retracement levels, indicating potential for further upward movement. The RSI and MACD indicators across multiple timeframes suggest a bullish trend, supporting a buy recommendation. The stop loss is set at the 50% retracement level to minimize risk, while the take profit is set at the 78.6% level to capture potential gains.. Value: 0.75. Price: $114903.25\"}'),(56,22,'2025-08-07 00:09:03','TRADE_ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"Failed to execute trade: \'bool\' object has no attribute \'get\'\"}'),(57,23,'2025-08-07 00:09:03','TRADE_ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"Failed to execute trade: \'bool\' object has no attribute \'get\'\"}'),(58,83,'2025-08-15 00:45:00','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(59,84,'2025-08-15 00:45:00','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(60,82,'2025-08-15 00:45:00','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(61,83,'2025-08-15 00:45:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(62,82,'2025-08-15 00:45:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(63,84,'2025-08-15 00:45:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(64,85,'2025-08-15 01:03:59','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(65,86,'2025-08-15 01:04:09','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(66,85,'2025-08-15 01:04:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(67,86,'2025-08-15 01:04:24','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(68,87,'2025-08-15 01:04:24','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(69,87,'2025-08-15 01:04:31','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(70,88,'2025-08-15 01:04:46','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(71,88,'2025-08-15 01:05:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(72,89,'2025-08-15 01:15:24','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(73,90,'2025-08-15 01:15:24','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(74,89,'2025-08-15 01:15:40','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(75,90,'2025-08-15 01:15:41','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(76,91,'2025-08-15 01:16:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(77,92,'2025-08-15 01:16:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(78,91,'2025-08-15 01:16:35','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(79,92,'2025-08-15 01:16:36','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(80,85,'2025-08-15 02:41:55','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(81,86,'2025-08-15 02:41:55','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(82,92,'2025-08-15 02:41:55','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(83,90,'2025-08-15 02:41:55','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(84,89,'2025-08-15 02:41:55','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(85,88,'2025-08-15 02:41:55','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(86,91,'2025-08-15 02:41:55','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(87,87,'2025-08-15 02:41:57','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(88,85,'2025-08-15 03:42:03','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(89,86,'2025-08-15 03:42:03','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(90,87,'2025-08-15 03:42:03','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(91,88,'2025-08-15 03:42:03','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(92,90,'2025-08-15 03:42:03','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(93,89,'2025-08-15 03:42:03','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(94,91,'2025-08-15 03:42:03','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(95,92,'2025-08-15 03:42:03','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(96,96,'2025-08-15 03:50:16','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(97,95,'2025-08-15 03:50:16','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(98,96,'2025-08-15 03:50:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(99,95,'2025-08-15 03:50:21','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(100,98,'2025-08-15 04:01:16','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}'),(101,97,'2025-08-15 04:01:16','ERROR',0.00000000,0.00000000,0.00000000,'{\"details\": \"No exchange API credentials configured. Please add your exchange credentials in settings.\"}');
/*!40000 ALTER TABLE `performance_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `register_bot`
--

DROP TABLE IF EXISTS `register_bot`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `register_bot` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_principal_id` varchar(255) NOT NULL,
  `bot_id` int NOT NULL,
  `api_key` varchar(255) NOT NULL,
  `status` enum('PENDING','APPROVED','REJECTED') DEFAULT 'APPROVED',
  `marketplace_name` varchar(255) DEFAULT NULL,
  `marketplace_description` text,
  `price_on_marketplace` decimal(10,2) DEFAULT NULL,
  `commission_rate` float DEFAULT '0.1',
  `registered_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `is_featured` tinyint(1) DEFAULT '0',
  `display_order` int DEFAULT '0',
  `is_active` tinyint(1) DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_register_bot_principal_bot` (`user_principal_id`,`bot_id`),
  UNIQUE KEY `uq_register_bot_api_key` (`api_key`),
  KEY `idx_user_principal_id` (`user_principal_id`),
  KEY `idx_bot_id` (`bot_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `register_bot_ibfk_1` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `register_bot`
--

LOCK TABLES `register_bot` WRITE;
/*!40000 ALTER TABLE `register_bot` DISABLE KEYS */;
INSERT INTO `register_bot` VALUES (22,'bkwke-64bo2-yipx4-f4zbn-olkgc-tcu2b-pvlsr-wrekw-ahu22-43z25-oqe',1,'bot_feg9b9xunwts9uy2wff5','APPROVED','Binance Futures LLM Bot','Advanced Binance Futures trading bot with LLM integration, leverage, stop loss, and take profit features',2.50,0.1,'2025-08-10 13:13:26',0,0,1),(23,'bkwke-64bo2-yipx4-f4zbn-olkgc-tcu2b-pvlsr-wrekw-ahu22-43z25-oqe',4,'bot_nagzzjhd32wlfq537c1h','APPROVED','Binance Spot Trading Bot','Professional spot trading bot with risk management for BTC, ETH, and major altcoins',0.05,0.1,'2025-08-12 07:51:29',0,0,1),(24,'dpene-vokts-sc5pf-o3etf-nmiwo-5n3e3-tq5me-hwamm-mw6g2-d3vuv-aae',1,'bot_sloyihnh5mf7tolvfhag','APPROVED','Binance Futures LLM Bot','Advanced Binance Futures trading bot with LLM integration, leverage, stop loss, and take profit features',2.50,0.1,'2025-08-13 22:51:35',0,0,1),(26,'j57al-3una4-thpap-jthsm-uy3gz-cgsot-s5fni-5cbqs-uio23-gcsgd-oqe',1,'bot_o136be7hrmoeevlo2z44','APPROVED','Binance Futures LLM Bot','Advanced Binance Futures trading bot with LLM integration, leverage, stop loss, and take profit features',2.50,0.1,'2025-08-14 00:06:54',0,0,1),(27,'ngdfh-vpgro-77fk7-2nsal-odkkr-i7236-iov6q-u2nxr-6fn6x-64gve-vqe',1,'bot_npx17j23n1k5ma28nikh','APPROVED','Binance Futures LLM Bot','Advanced Binance Futures trading bot with LLM integration, leverage, stop loss, and take profit features',2.50,0.1,'2025-08-14 23:03:55',0,0,1),(29,'jzflm-bqeyp-zckv7-pnaqa-oh43o-gdawr-7ucy3-ffewe-oasrb-4rymq-yae',1,'bot_1u6z6ih9lddu1dstx2e6','APPROVED','Binance Futures LLM Bot','Advanced Binance Futures trading bot with LLM integration, leverage, stop loss, and take profit features',2.50,0.1,'2025-08-14 23:12:19',0,0,1);
/*!40000 ALTER TABLE `register_bot` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `schema_migrations`
--

DROP TABLE IF EXISTS `schema_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `schema_migrations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `version` varchar(255) NOT NULL,
  `applied_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `version` (`version`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `schema_migrations`
--

LOCK TABLES `schema_migrations` WRITE;
/*!40000 ALTER TABLE `schema_migrations` DISABLE KEYS */;
INSERT INTO `schema_migrations` VALUES (1,'001_initial_schema','2025-08-01 23:37:31'),(2,'002_bot_registration_features','2025-08-01 23:38:02'),(3,'003_add_bot_marketplace_registration','2025-08-01 23:38:07'),(4,'007_create_user_settings','2025-08-10 06:50:38'),(5,'008_enforce_unique_register_bot','2025-08-10 13:10:37'),(6,'004_create_user_principals','2025-08-14 06:50:08'),(7,'005_marketplace_subscription_support','2025-08-14 06:52:51'),(8,'006_add_principal_id_to_exchange_credentials','2025-08-14 06:54:37'),(9,'009_paypal_integration','2025-08-14 06:55:35'),(10,'005_marketplace_subscription_support_safe','2025-08-14 09:48:29');
/*!40000 ALTER TABLE `schema_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subscription_invoices`
--

DROP TABLE IF EXISTS `subscription_invoices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subscription_invoices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subscription_id` int NOT NULL,
  `user_id` int NOT NULL,
  `invoice_number` varchar(50) NOT NULL,
  `amount` decimal(10,2) NOT NULL,
  `currency` varchar(10) DEFAULT 'USD',
  `base_price` decimal(10,2) NOT NULL,
  `discount_amount` decimal(10,2) DEFAULT '0.00',
  `tax_amount` decimal(10,2) DEFAULT '0.00',
  `final_amount` decimal(10,2) NOT NULL,
  `billing_period_start` datetime DEFAULT NULL,
  `billing_period_end` datetime DEFAULT NULL,
  `status` varchar(20) DEFAULT 'PENDING',
  `payment_method` varchar(50) DEFAULT NULL,
  `payment_date` datetime DEFAULT NULL,
  `promotion_code` varchar(50) DEFAULT NULL,
  `promotion_discount` decimal(10,2) DEFAULT '0.00',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `due_date` datetime DEFAULT NULL,
  `paypal_payment_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `invoice_number` (`invoice_number`),
  KEY `user_id` (`user_id`),
  KEY `idx_subscription_invoices_subscription_id` (`subscription_id`),
  CONSTRAINT `subscription_invoices_ibfk_1` FOREIGN KEY (`subscription_id`) REFERENCES `subscriptions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `subscription_invoices_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subscription_invoices`
--

LOCK TABLES `subscription_invoices` WRITE;
/*!40000 ALTER TABLE `subscription_invoices` DISABLE KEYS */;
/*!40000 ALTER TABLE `subscription_invoices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subscriptions`
--

DROP TABLE IF EXISTS `subscriptions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `subscriptions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `instance_name` varchar(255) NOT NULL,
  `user_id` int DEFAULT NULL COMMENT 'Studio user ID (NULL for marketplace-only subscriptions)',
  `bot_id` int NOT NULL,
  `pricing_plan_id` int DEFAULT NULL,
  `status` enum('ACTIVE','PAUSED','CANCELLED','EXPIRED','ERROR') DEFAULT 'ACTIVE',
  `is_testnet` tinyint(1) DEFAULT '0',
  `is_trial` tinyint(1) DEFAULT '0',
  `trial_expires_at` datetime DEFAULT NULL,
  `exchange_type` enum('BINANCE','COINBASE','KRAKEN') DEFAULT 'BINANCE',
  `trading_pair` varchar(20) DEFAULT NULL,
  `timeframe` varchar(10) DEFAULT NULL,
  `strategy_config` json DEFAULT NULL,
  `execution_config` json DEFAULT NULL,
  `risk_config` json DEFAULT NULL,
  `started_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `expires_at` datetime DEFAULT NULL,
  `last_run_at` datetime DEFAULT NULL,
  `next_run_at` datetime DEFAULT NULL,
  `total_trades` int DEFAULT '0',
  `winning_trades` int DEFAULT '0',
  `total_pnl` decimal(15,8) DEFAULT '0.00000000',
  `billing_cycle` varchar(20) DEFAULT 'MONTHLY',
  `next_billing_date` datetime DEFAULT NULL,
  `auto_renew` tinyint(1) DEFAULT '1',
  `user_principal_id` varchar(255) DEFAULT NULL COMMENT 'ICP Principal ID của user',
  `timeframes` json DEFAULT NULL COMMENT 'List of timeframes',
  `trade_evaluation_period` int DEFAULT NULL COMMENT 'Minutes for analysis',
  `network_type` enum('TESTNET','MAINNET') DEFAULT 'TESTNET',
  `trade_mode` enum('SPOT','MARGIN','FUTURES') DEFAULT 'SPOT',
  `marketplace_user_email` varchar(255) DEFAULT NULL COMMENT 'Email from marketplace user',
  `marketplace_user_telegram` varchar(255) DEFAULT NULL COMMENT 'Telegram from marketplace user',
  `marketplace_user_discord` varchar(255) DEFAULT NULL COMMENT 'Discord from marketplace user',
  `is_marketplace_subscription` tinyint(1) DEFAULT '0' COMMENT 'True if subscription from marketplace without studio account',
  `marketplace_subscription_start` datetime DEFAULT NULL COMMENT 'Start time specified by marketplace',
  `marketplace_subscription_end` datetime DEFAULT NULL COMMENT 'End time specified by marketplace',
  `paypal_payment_id` varchar(255) DEFAULT NULL,
  `payment_method` enum('STRIPE','PAYPAL') DEFAULT 'STRIPE',
  PRIMARY KEY (`id`),
  KEY `idx_subscriptions_user_id` (`user_id`),
  KEY `idx_subscriptions_bot_id` (`bot_id`),
  KEY `idx_subscriptions_status` (`status`),
  KEY `idx_subscriptions_pricing_plan` (`pricing_plan_id`),
  KEY `idx_marketplace_subscription` (`is_marketplace_subscription`,`user_principal_id`),
  KEY `idx_marketplace_email` (`marketplace_user_email`),
  CONSTRAINT `subscriptions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`),
  CONSTRAINT `subscriptions_ibfk_2` FOREIGN KEY (`bot_id`) REFERENCES `bots` (`id`),
  CONSTRAINT `subscriptions_ibfk_3` FOREIGN KEY (`pricing_plan_id`) REFERENCES `bot_pricing_plans` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=99 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subscriptions`
--

LOCK TABLES `subscriptions` WRITE;
/*!40000 ALTER TABLE `subscriptions` DISABLE KEYS */;
INSERT INTO `subscriptions` VALUES (22,'Fixed Trading Bot Test',1,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-05 00:00:00','2025-08-10 23:59:59',NULL,'2025-08-18 01:18:07',0,0,0.00000000,'MONTHLY',NULL,1,'ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bqe',NULL,NULL,'TESTNET','FUTURES','user@marketplace.com',NULL,NULL,1,'2025-08-05 00:00:00','2025-08-10 23:59:59',NULL,'STRIPE'),(23,'Active Trading Bot',1,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-03 00:00:00','2025-08-08 23:59:59',NULL,'2025-08-07 01:07:07',0,0,0.00000000,'MONTHLY',NULL,1,'ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bqe',NULL,NULL,'TESTNET','FUTURES','user@marketplace.com',NULL,NULL,1,'2025-08-03 00:00:00','2025-08-08 23:59:59',NULL,'STRIPE'),(24,'studio_1_1754700324',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-09 00:45:17','2025-08-10 00:45:17',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'gkwb5-66h5b-mbrsb-l6ecz-wc5jp-hnzfb-cfw3m-irfgb-inum4-cn44o-dae',NULL,NULL,'TESTNET','FUTURES','gkwb5-66h5@trading-marketplace.icp','@chaulaode2',NULL,1,'2025-08-09 00:45:17','2025-08-10 00:45:17',NULL,'STRIPE'),(25,'studio_1_1754746006',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-09 13:26:41','2025-08-10 13:26:41',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'kzcep-hw2e6-ceqbg-hukhy-azgth-4batf-b7m4d-zrl2v-ify23-agqtf-xqe',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@chaulaode',NULL,1,'2025-08-09 13:26:41','2025-08-10 13:26:41',NULL,'STRIPE'),(26,'studio_1_1754748785',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-09 14:13:03','2025-08-10 14:13:03',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'kzcep-hw2e6-ceqbg-hukhy-azgth-4batf-b7m4d-zrl2v-ify23-agqtf-xqe',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@chaulaode',NULL,1,'2025-08-09 14:13:03','2025-08-10 14:13:03',NULL,'STRIPE'),(27,'studio_1_1754840983',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-10 15:49:30','2025-08-11 15:49:30',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'hnymd-a264o-r3pns-3u62v-o2r4e-tnmic-qh77e-leh2u-x6u2y-nwjgr-3qe',NULL,NULL,'TESTNET','FUTURES','chaulaode1257@gmail.com','@chaulaode',NULL,1,'2025-08-10 15:49:30','2025-08-11 15:49:30',NULL,'STRIPE'),(28,'studio_1_1754841254',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-10 15:54:12','2025-08-11 15:54:12',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'hnymd-a264o-r3pns-3u62v-o2r4e-tnmic-qh77e-leh2u-x6u2y-nwjgr-3qe',NULL,NULL,'TESTNET','FUTURES','chaulaode1257@gmail.com','@chaulaode',NULL,1,'2025-08-10 15:54:12','2025-08-11 15:54:12',NULL,'STRIPE'),(29,'studio_1_1754841445',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-10 15:57:18','2025-08-11 15:57:18',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'hnymd-a264o-r3pns-3u62v-o2r4e-tnmic-qh77e-leh2u-x6u2y-nwjgr-3qe',NULL,NULL,'TESTNET','FUTURES','chaulaode1257@gmail.com','@chaulaode',NULL,1,'2025-08-10 15:57:18','2025-08-11 15:57:18',NULL,'STRIPE'),(30,'studio_1_1754876921',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 01:48:42','2025-08-12 01:48:42',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'nw247-ow7db-2svhx-uh6w7-cvsn4-lntvw-vexz3-rgxqp-z3236-2bg2i-kae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@chaulaode',NULL,1,'2025-08-11 01:48:42','2025-08-12 01:48:42',NULL,'STRIPE'),(31,'studio_1_1754877004',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 01:50:05','2025-08-12 01:50:05',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'nw247-ow7db-2svhx-uh6w7-cvsn4-lntvw-vexz3-rgxqp-z3236-2bg2i-kae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@chaulaode',NULL,1,'2025-08-11 01:50:05','2025-08-12 01:50:05',NULL,'STRIPE'),(32,'studio_1_1754877322',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 01:55:22','2025-08-12 01:55:22',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'nw247-ow7db-2svhx-uh6w7-cvsn4-lntvw-vexz3-rgxqp-z3236-2bg2i-kae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@chaulaode',NULL,1,'2025-08-11 01:55:22','2025-08-12 01:55:22',NULL,'STRIPE'),(33,'studio_1_1754899701',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 08:08:21','2025-08-12 08:08:21',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'c57tc-sdknt-ghi5r-k4q43-5fhgv-desnp-bktug-zvds3-kw6zf-s3kuk-tae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@chaulaode',NULL,1,'2025-08-11 08:08:21','2025-08-12 08:08:21',NULL,'STRIPE'),(34,'studio_1_1754900661',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 08:24:21','2025-08-12 08:24:21',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'c57tc-sdknt-ghi5r-k4q43-5fhgv-desnp-bktug-zvds3-kw6zf-s3kuk-tae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@chaulaode',NULL,1,'2025-08-11 08:24:21','2025-08-12 08:24:21',NULL,'STRIPE'),(35,'studio_1_1754901438',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 08:37:18','2025-08-12 08:37:18',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 08:37:18','2025-08-12 08:37:18',NULL,'STRIPE'),(36,'studio_1_1754904680',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 09:31:20','2025-09-10 09:31:20',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 09:31:20','2025-09-10 09:31:20',NULL,'STRIPE'),(37,'studio_1_1754904739',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 09:32:20','2025-09-10 09:32:20',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 09:32:20','2025-09-10 09:32:20',NULL,'STRIPE'),(38,'studio_1_1754905243',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 09:40:44','2025-09-10 09:40:44',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 09:40:44','2025-09-10 09:40:44',NULL,'STRIPE'),(39,'studio_1_1754905368',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 09:42:49','2025-09-10 09:42:49',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 09:42:49','2025-09-10 09:42:49',NULL,'STRIPE'),(40,'studio_1_1754905714',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 09:48:34','2025-08-12 09:48:34',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 09:48:34','2025-08-12 09:48:34',NULL,'STRIPE'),(41,'studio_1_1754905784',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 09:49:45','2025-09-10 09:49:45',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 09:49:45','2025-09-10 09:49:45',NULL,'STRIPE'),(42,'studio_1_1754907701',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 10:21:41','2025-08-12 10:21:41',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 10:21:41','2025-08-12 10:21:41',NULL,'STRIPE'),(43,'studio_1_1754907778',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 10:22:57','2025-08-12 10:22:57',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 10:22:57','2025-08-12 10:22:57',NULL,'STRIPE'),(44,'studio_1_1754907815',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 10:23:34','2025-09-10 10:23:34',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 10:23:34','2025-09-10 10:23:34',NULL,'STRIPE'),(45,'studio_1_1754909717',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 10:55:16','2025-09-10 10:55:16',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 10:55:16','2025-09-10 10:55:16',NULL,'STRIPE'),(46,'studio_1_1754909729',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 10:55:28','2025-09-10 10:55:28',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 10:55:28','2025-09-10 10:55:28',NULL,'STRIPE'),(47,'studio_1_1754909750',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 10:55:49','2025-09-10 10:55:49',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 10:55:49','2025-09-10 10:55:49',NULL,'STRIPE'),(48,'studio_1_1754909842',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 10:57:21','2025-09-10 10:57:21',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 10:57:21','2025-09-10 10:57:21',NULL,'STRIPE'),(49,'studio_1_1754910013',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 11:00:12','2025-09-10 11:00:12',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 11:00:12','2025-09-10 11:00:12',NULL,'STRIPE'),(50,'studio_1_1754910029',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-11 11:00:28','2025-09-10 11:00:28',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-11 11:00:28','2025-09-10 11:00:28',NULL,'STRIPE'),(51,'studio_1_1754984437',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 07:40:36','2025-08-13 07:40:36',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 07:40:36','2025-08-13 07:40:36',NULL,'STRIPE'),(52,'studio_1_1754986636',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 08:17:15','2025-08-13 08:17:15',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 08:17:15','2025-08-13 08:17:15',NULL,'STRIPE'),(53,'studio_4_1754986760',NULL,4,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 08:19:19','2025-08-13 08:19:19',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','SPOT','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 08:19:19','2025-08-13 08:19:19',NULL,'STRIPE'),(54,'studio_1_1755011465',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 15:11:04','2025-08-13 15:11:04',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 15:11:04','2025-08-13 15:11:04',NULL,'STRIPE'),(55,'studio_1_1755011744',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 15:15:43','2025-08-13 15:15:43',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 15:15:43','2025-08-13 15:15:43',NULL,'STRIPE'),(56,'studio_1_1755012017',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 15:20:17','2025-08-13 15:20:17',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 15:20:17','2025-08-13 15:20:17',NULL,'STRIPE'),(57,'studio_1_1755036343',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 22:05:42','2025-08-13 22:05:42',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 22:05:42','2025-08-13 22:05:42',NULL,'STRIPE'),(58,'studio_1_1755037370',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 22:22:50','2025-08-13 22:22:50',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 22:22:50','2025-08-13 22:22:50',NULL,'STRIPE'),(59,'studio_1_1755037437',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 22:23:56','2025-08-13 22:23:56',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 22:23:56','2025-08-13 22:23:56',NULL,'STRIPE'),(60,'studio_1_1755037844',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 22:30:43','2025-08-13 22:30:43',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 22:30:43','2025-08-13 22:30:43',NULL,'STRIPE'),(61,'studio_1_1755038242',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 22:37:22','2025-08-13 22:37:22',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 22:37:22','2025-08-13 22:37:22',NULL,'STRIPE'),(62,'studio_1_1755038505',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 22:41:44','2025-08-13 22:41:44',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 22:41:44','2025-08-13 22:41:44',NULL,'STRIPE'),(63,'studio_1_1755039114',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 22:51:53','2025-08-13 22:51:53',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 22:51:53','2025-08-13 22:51:53',NULL,'STRIPE'),(64,'studio_1_1755039141',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 22:52:20','2025-08-13 22:52:20',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 22:52:20','2025-08-13 22:52:20',NULL,'STRIPE'),(65,'studio_1_1755039715',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 23:01:55','2025-08-13 23:01:55',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 23:01:55','2025-08-13 23:01:55',NULL,'STRIPE'),(66,'studio_1_1755040821',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 23:20:20','2025-08-13 23:20:20',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 23:20:20','2025-08-13 23:20:20',NULL,'STRIPE'),(67,'studio_1_1755041075',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-12 23:24:34','2025-08-13 23:24:34',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-12 23:24:34','2025-08-13 23:24:34',NULL,'STRIPE'),(68,'studio_1_1755047371',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 01:09:30','2025-08-14 01:09:30',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 01:09:30','2025-08-14 01:09:30',NULL,'STRIPE'),(69,'studio_1_1755047882',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 01:18:01','2025-08-14 01:18:01',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 01:18:01','2025-08-14 01:18:01',NULL,'STRIPE'),(70,'studio_1_1755047912',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 01:18:31','2025-08-14 01:18:31',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 01:18:31','2025-08-14 01:18:31',NULL,'STRIPE'),(71,'studio_1_1755047969',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 01:19:28','2025-08-14 01:19:28',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 01:19:28','2025-08-14 01:19:28',NULL,'STRIPE'),(72,'studio_1_1755054051',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 03:00:50','2025-08-14 03:00:50',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 03:00:50','2025-08-14 03:00:50',NULL,'STRIPE'),(73,'studio_1_1755054078',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 03:01:17','2025-08-14 03:01:17',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 03:01:17','2025-08-14 03:01:17',NULL,'STRIPE'),(74,'studio_1_1755055586',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 03:26:25','2025-08-14 03:26:25',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 03:26:25','2025-08-14 03:26:25',NULL,'STRIPE'),(75,'studio_1_1755055600',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 03:26:39','2025-08-14 03:26:39',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 03:26:39','2025-08-14 03:26:39',NULL,'STRIPE'),(76,'studio_1_1755055613',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 03:26:52','2025-08-14 03:26:52',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 03:26:52','2025-08-14 03:26:52',NULL,'STRIPE'),(77,'studio_1_1755055634',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 03:27:14','2025-08-14 03:27:14',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 03:27:14','2025-08-14 03:27:14',NULL,'STRIPE'),(78,'studio_1_1755055876',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-13 03:31:15','2025-08-14 03:31:15',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-13 03:31:15','2025-08-14 03:31:15',NULL,'STRIPE'),(79,'studio_1_1755131532',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-14 00:32:12','2025-08-15 00:32:12',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'5n55t-7fead-eny3z-4374z-dn2gf-qo7h7-6wdsc-o5qwt-2bsrw-6w56b-6qe',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-14 00:32:12','2025-08-15 00:32:12',NULL,'STRIPE'),(80,'studio_1_1755131688',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-14 00:34:47','2025-08-15 00:34:47',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'5n55t-7fead-eny3z-4374z-dn2gf-qo7h7-6wdsc-o5qwt-2bsrw-6w56b-6qe',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-14 00:34:47','2025-08-15 00:34:47',NULL,'STRIPE'),(81,'studio_1_1755131948',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-14 00:39:07','2025-08-15 00:39:07',NULL,NULL,0,0,0.00000000,'MONTHLY',NULL,1,'5n55t-7fead-eny3z-4374z-dn2gf-qo7h7-6wdsc-o5qwt-2bsrw-6w56b-6qe',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-14 00:39:07','2025-08-15 00:39:07',NULL,'STRIPE'),(82,'studio_1_1755213163',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-14 23:12:42','2025-08-15 23:12:42',NULL,'2025-08-15 02:57:05',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-14 23:12:42','2025-08-15 23:12:42',NULL,'STRIPE'),(83,'studio_1_1755213186',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-14 23:13:06','2025-08-15 23:13:06',NULL,'2025-08-15 02:57:05',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-14 23:13:06','2025-08-15 23:13:06',NULL,'STRIPE'),(84,'studio_1_1755213658',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-14 23:20:57','2025-08-15 23:20:57',NULL,'2025-08-15 02:57:05',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-14 23:20:57','2025-08-15 23:20:57',NULL,'STRIPE'),(85,'studio_1_1755219823',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-15 01:03:31','2025-08-16 01:03:31',NULL,'2025-08-15 04:41:58',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-15 01:03:31','2025-08-16 01:03:31',NULL,'STRIPE'),(86,'studio_1_1755219834',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-15 01:03:53','2025-08-16 01:03:53',NULL,'2025-08-15 04:41:58',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-15 01:03:53','2025-08-16 01:03:53',NULL,'STRIPE'),(87,'studio_1_1755219856',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-15 01:04:15','2025-08-16 01:04:15',NULL,'2025-08-15 04:41:58',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-15 01:04:15','2025-08-16 01:04:15',NULL,'STRIPE'),(88,'studio_1_1755219871',NULL,1,NULL,'CANCELLED',1,0,NULL,'BINANCE','BTCUSDT','1h','{}','{\"buy_order_type\": \"PERCENTAGE\", \"buy_order_value\": 100.0, \"sell_order_type\": \"ALL\", \"sell_order_value\": 100.0}','{\"max_position_size\": 100.0, \"stop_loss_percent\": 2.0, \"take_profit_percent\": 4.0}','2025-08-15 01:04:30','2025-08-16 01:04:30',NULL,'2025-08-15 04:41:58',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae',NULL,NULL,'TESTNET','FUTURES','denguyenst@gmail.com','@aaaa',NULL,1,'2025-08-15 01:04:30','2025-08-16 01:04:30',NULL,'STRIPE'),(89,'paypal_paypal_0332ea7238c5_1755195305',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 01:15:05','2025-09-14 01:15:05',NULL,'2025-08-15 04:41:59',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(90,'paypal_paypal_0332ea7238c5_1755195305',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 01:15:05','2025-09-14 01:15:05',NULL,'2025-08-15 04:41:59',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(91,'paypal_paypal_c96854096655_1755195361',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 01:16:01','2025-09-14 01:16:01',NULL,'2025-08-15 04:41:59',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(92,'paypal_paypal_c96854096655_1755195361',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 01:16:01','2025-09-14 01:16:01',NULL,'2025-08-15 04:41:59',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(93,'paypal_paypal_ddf3b29c5fb9_1755195511',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 01:18:32','2025-09-14 01:18:32',NULL,'2025-08-15 02:57:06',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(94,'paypal_paypal_ddf3b29c5fb9_1755195511',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 01:18:32','2025-09-14 01:18:32',NULL,'2025-08-15 02:57:06',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(95,'paypal_paypal_bf1a701c4a32_1755204586',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 03:49:47','2025-09-14 03:49:47',NULL,'2025-08-15 04:50:11',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(96,'paypal_paypal_bf1a701c4a32_1755204586',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 03:49:47','2025-09-14 03:49:47',NULL,'2025-08-15 04:50:11',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(97,'paypal_paypal_31f7ce425cab_1755205257',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 04:00:58','2025-09-14 04:00:58',NULL,'2025-08-15 05:01:11',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE'),(98,'paypal_paypal_31f7ce425cab_1755205257',NULL,1,NULL,'CANCELLED',0,0,NULL,'BINANCE','BTCUSDT',NULL,NULL,NULL,NULL,'2025-08-15 04:00:58','2025-09-14 04:00:58',NULL,'2025-08-15 05:01:11',0,0,0.00000000,'MONTHLY',NULL,1,'wcup6-pbb5f-tewqx-tykmi-pz4sp-3zn2r-pfevf-34zwm-lqk2d-sy55u-rae','[\"1h\"]',NULL,'TESTNET','SPOT',NULL,NULL,NULL,1,NULL,NULL,NULL,'STRIPE');
/*!40000 ALTER TABLE `subscriptions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `trades`
--

DROP TABLE IF EXISTS `trades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `trades` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subscription_id` int NOT NULL,
  `side` varchar(10) NOT NULL,
  `status` enum('OPEN','CLOSED') DEFAULT 'OPEN',
  `entry_price` decimal(15,8) DEFAULT NULL,
  `exit_price` decimal(15,8) DEFAULT NULL,
  `quantity` decimal(15,8) DEFAULT NULL,
  `stop_loss_price` decimal(15,8) DEFAULT NULL,
  `take_profit_price` decimal(15,8) DEFAULT NULL,
  `entry_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `exit_time` datetime DEFAULT NULL,
  `pnl` decimal(15,8) DEFAULT NULL,
  `pnl_percentage` float DEFAULT NULL,
  `exchange_order_id` varchar(100) DEFAULT NULL,
  `exchange_trade_id` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_trades_subscription_id` (`subscription_id`),
  CONSTRAINT `trades_ibfk_1` FOREIGN KEY (`subscription_id`) REFERENCES `subscriptions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `trades`
--

LOCK TABLES `trades` WRITE;
/*!40000 ALTER TABLE `trades` DISABLE KEYS */;
/*!40000 ALTER TABLE `trades` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_principals`
--

DROP TABLE IF EXISTS `user_principals`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_principals` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `principal_id` varchar(255) NOT NULL,
  `status` enum('ACTIVE','INACTIVE') DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_user_principals_principal_id` (`principal_id`),
  KEY `ix_user_principals_id` (`id`),
  KEY `idx_principal_status` (`principal_id`,`status`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_principal_id` (`principal_id`),
  CONSTRAINT `user_principals_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_principals`
--

LOCK TABLES `user_principals` WRITE;
/*!40000 ALTER TABLE `user_principals` DISABLE KEYS */;
INSERT INTO `user_principals` VALUES (1,1,'ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bqe','ACTIVE','2025-08-04 23:21:59','2025-08-04 23:21:59'),(2,1,'rdmx6-jaaaa-aaaah-qcaiq-cai','ACTIVE','2025-08-04 23:21:59','2025-08-04 23:21:59'),(3,5,'ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnrz-bae','ACTIVE','2025-08-05 01:15:06','2025-08-05 01:15:06'),(4,5,'ok7jr-d6ktf-idahj-ucbcb-pg5tt-2ayc4-kjkjm-xm6qd-h4uxv-vbnra-bae','ACTIVE','2025-08-05 01:15:21','2025-08-05 01:15:21');
/*!40000 ALTER TABLE `user_principals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_settings`
--

DROP TABLE IF EXISTS `user_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_settings` (
  `id` int NOT NULL AUTO_INCREMENT,
  `principal_id` varchar(255) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `social_telegram` varchar(255) DEFAULT NULL,
  `social_discord` varchar(255) DEFAULT NULL,
  `social_twitter` varchar(255) DEFAULT NULL,
  `social_whatsapp` varchar(255) DEFAULT NULL,
  `default_channel` varchar(50) DEFAULT NULL,
  `display_dark_mode` tinyint(1) DEFAULT NULL,
  `display_currency` varchar(10) DEFAULT NULL,
  `display_language` varchar(10) DEFAULT NULL,
  `display_timezone` varchar(64) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_user_settings_principal` (`principal_id`),
  UNIQUE KEY `ix_user_settings_principal_id` (`principal_id`),
  KEY `ix_user_settings_id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_settings`
--

LOCK TABLES `user_settings` WRITE;
/*!40000 ALTER TABLE `user_settings` DISABLE KEYS */;
INSERT INTO `user_settings` VALUES (1,'bkwke-64bo2-yipx4-f4zbn-olkgc-tcu2b-pvlsr-wrekw-ahu22-43z25-oqe','denguyenst@gmail.comaaa','@chaulaode2','@denguyenst',NULL,NULL,'telegram',0,'ICP','en','UTC','2025-08-10 02:29:56','2025-08-10 06:54:55'),(2,'debug_principal','bulk@debug',NULL,NULL,NULL,NULL,'email',0,'ICP','en','UTC','2025-08-10 02:45:49','2025-08-10 02:45:49'),(3,'hnymd-a264o-r3pns-3u62v-o2r4e-tnmic-qh77e-leh2u-x6u2y-nwjgr-3qe','chaulaode1257@gmail.com','@chaulaode',NULL,NULL,NULL,'email',0,'ICP','en','UTC','2025-08-10 13:15:39','2025-08-10 14:51:58'),(4,'nw247-ow7db-2svhx-uh6w7-cvsn4-lntvw-vexz3-rgxqp-z3236-2bg2i-kae','denguyenst@gmail.com','@chaulaode',NULL,NULL,NULL,'email',0,'ICP','en','UTC','2025-08-11 01:19:25','2025-08-11 01:40:37'),(5,'c57tc-sdknt-ghi5r-k4q43-5fhgv-desnp-bktug-zvds3-kw6zf-s3kuk-tae','denguyenst@gmail.com','@chaulaode',NULL,NULL,NULL,'email',0,'ICP','en','UTC','2025-08-11 08:04:02','2025-08-11 08:04:02'),(6,'wsal7-6dg4r-3k3re-fggb5-suppr-3ovpw-23dkp-ongcc-sb3pq-jjfbs-eae','denguyenst@gmail.com','@aaaa',NULL,NULL,NULL,'email',0,'ICP','en','UTC','2025-08-11 08:37:06','2025-08-11 08:37:06');
/*!40000 ALTER TABLE `user_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `role` enum('USER','DEVELOPER','ADMIN') DEFAULT 'USER',
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `developer_name` varchar(255) DEFAULT NULL,
  `developer_bio` text,
  `developer_website` varchar(255) DEFAULT NULL,
  `api_key` varchar(255) DEFAULT NULL,
  `api_secret` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`),
  KEY `idx_users_email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'admin@botmarketplace.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gS.Oi2','ADMIN',1,'2025-08-01 23:35:18','2025-08-01 23:35:18','System Admin',NULL,NULL,NULL,NULL),(2,'system@botmarketplace.com','$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.gS.Oi2','ADMIN',1,'2025-08-01 23:35:18','2025-08-01 23:35:18','System Bot Creator',NULL,NULL,NULL,NULL),(3,'test@example.com','$2b$12$DN5/RoaGApVcN08dNPq1eeCrc5hX0BdZdyUhUmvPOxD6Rwa2oU1t6','USER',1,'2025-08-02 00:03:11','2025-08-02 00:03:11',NULL,NULL,NULL,NULL,NULL),(4,'test@marketplace.com','$2b$12$ZCfHwTl.COMI1gTCMCfnMe8pcPF508DIwWuw9DOYee31h1EaVfYhS','USER',1,'2025-08-03 03:59:47','2025-08-03 03:59:47',NULL,NULL,NULL,NULL,NULL),(5,'denguyenst@gmail.com','$2b$12$6APpeS1jFMAYp38pZ407nOw1CXYYeLeU7pI3xTb71ITA93cySn7n2','ADMIN',1,'2025-08-05 01:12:34','2025-08-07 23:07:00','chaulaode','chaulaode','cryptomancer.ai',NULL,NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Final view structure for view `paypal_payment_summary`
--

/*!50001 DROP VIEW IF EXISTS `paypal_payment_summary`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`botuser`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `paypal_payment_summary` AS select `pp`.`id` AS `id`,`pp`.`user_principal_id` AS `user_principal_id`,`b`.`name` AS `bot_name`,`pp`.`amount_usd` AS `amount_usd`,`pp`.`status` AS `status`,`pp`.`created_at` AS `created_at`,`pp`.`completed_at` AS `completed_at`,`pp`.`rental_id` AS `rental_id`,(case when ((`pp`.`status` = 'COMPLETED') and (`pp`.`rental_id` is not null)) then 'SUCCESS' when (`pp`.`status` = 'COMPLETED_PENDING_RENTAL') then 'NEEDS_MANUAL_REVIEW' when ((`pp`.`status` = 'FAILED') or (`pp`.`status` = 'CANCELLED')) then 'FAILED' else 'PENDING' end) AS `overall_status` from (`paypal_payments` `pp` join `bots` `b` on((`pp`.`bot_id` = `b`.`id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-15 20:40:59
