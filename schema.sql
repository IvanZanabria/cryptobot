CREATE DATABASE IF NOT EXISTS cryptobot CHARACTER SET utf8mb4;
USE cryptobot;

-- Tabla de ordenes de compra
CREATE TABLE IF NOT EXISTS ordenes (
    id_orden VARCHAR(64) PRIMARY KEY,
    cripto VARCHAR(20) NOT NULL,
    productor VARCHAR(20) NOT NULL,
    operacion VARCHAR(20) NOT NULL,
    precio_ejecucion DECIMAL(12, 2) NOT NULL,
    precio_promedio DECIMAL(12, 2) NOT NULL,
    descuento VARCHAR(10) NOT NULL,
    inicio DATETIME NOT NULL,
    estado VARCHAR(20) NOT NULL
);

-- Tabla para el historial y gestion de alertas
CREATE TABLE IF NOT EXISTS alertas (
    id_alerta VARCHAR(64) PRIMARY KEY,
    tipo VARCHAR(40) NOT NULL,
    severidad VARCHAR(20) NOT NULL,
    cripto VARCHAR(20),
    productor VARCHAR(20),
    mensaje TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL,
    inicio DATETIME NOT NULL,
    resuelta_en DATETIME NULL
);

-- Tabla para el estado de los productores
CREATE TABLE IF NOT EXISTS productores (
    productor VARCHAR(20) PRIMARY KEY,
    estado VARCHAR(20) NOT NULL,
    ultimo_visto DATETIME NOT NULL
);

-- Tabla para el registro en tiempo real de los ticks (precios)
CREATE TABLE IF NOT EXISTS ticks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ts DATETIME NOT NULL,
    cripto VARCHAR(20) NOT NULL,
    precio DECIMAL(12, 2) NOT NULL,
    volumen DECIMAL(10, 2) NOT NULL,
    productor VARCHAR(20) NOT NULL
);
