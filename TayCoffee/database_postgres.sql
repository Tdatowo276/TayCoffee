/*
  PostgreSQL schema for TÀY COFFEE - Local Management System
  Optimized for LAN deployment.
*/

/* =========================================================
   Drop objects (safe re-run)
   ========================================================= */
DROP VIEW IF EXISTS vw_DailyRevenue;

DROP TABLE IF EXISTS OrderCombos CASCADE;
DROP TABLE IF EXISTS OrderDetails CASCADE;
DROP TABLE IF EXISTS Payments CASCADE;
DROP TABLE IF EXISTS Orders CASCADE;
DROP TABLE IF EXISTS Recipes CASCADE;
DROP TABLE IF EXISTS Ingredients CASCADE;
DROP TABLE IF EXISTS ComboItems CASCADE;
DROP TABLE IF EXISTS Combos CASCADE;
DROP TABLE IF EXISTS ProductReviews CASCADE;
DROP TABLE IF EXISTS WishlistItems CASCADE;
DROP TABLE IF EXISTS Wishlists CASCADE;
DROP TABLE IF EXISTS Promotions CASCADE;
DROP TABLE IF EXISTS Products CASCADE;
DROP TABLE IF EXISTS Categories CASCADE;
DROP TABLE IF EXISTS Tables CASCADE;
DROP TABLE IF EXISTS Shifts CASCADE;
DROP TABLE IF EXISTS UserAddresses CASCADE;
DROP TABLE IF EXISTS Users CASCADE;
DROP TABLE IF EXISTS Roles CASCADE;

/* =========================================================
   Identity / User / Roles
   ========================================================= */
CREATE TABLE Roles (
    RoleID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    RoleName VARCHAR(30) NOT NULL UNIQUE
);

CREATE TABLE Users (
    UserID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    FullName VARCHAR(120) NOT NULL,
    Email VARCHAR(150) NOT NULL UNIQUE,
    Phone VARCHAR(15) NULL,
    PasswordHash VARCHAR(255) NOT NULL, -- SHA-256
    RoleID INT NOT NULL REFERENCES Roles(RoleID),
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    CreatedAt TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE Shifts (
    ShiftID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    EmployeeID INT NOT NULL REFERENCES Users(UserID),
    StartTime TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    EndTime TIMESTAMPTZ NULL,
    Status VARCHAR(20) DEFAULT 'active' -- active, completed
);

/* =========================================================
   Restaurant Layout (Tables)
   ========================================================= */
CREATE TABLE Tables (
    TableID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    TableNumber VARCHAR(10) NOT NULL UNIQUE,
    Capacity INT DEFAULT 4,
    Status VARCHAR(20) NOT NULL DEFAULT 'Empty' CHECK (Status IN ('Empty', 'Occupied', 'Reserved'))
);

/* =========================================================
   Catalog & Menu
   ========================================================= */
CREATE TABLE Categories (
    CategoryID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CategoryName VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Products (
    ProductID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CategoryID INT NOT NULL REFERENCES Categories(CategoryID),
    ProductName VARCHAR(120) NOT NULL,
    Description VARCHAR(600) NULL,
    Price NUMERIC(18,2) NOT NULL CHECK (Price >= 0),
    StockQuantity INT NOT NULL DEFAULT 100 CHECK (StockQuantity >= 0), -- For pre-packaged items
    ImageURL VARCHAR(500) NULL, -- Can store emoji or URL
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    CreatedAt TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

/* =========================================================
   Inventory & Recipes (Automated Deduction)
   ========================================================= */
CREATE TABLE Ingredients (
    IngredientID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    IngredientName VARCHAR(120) NOT NULL UNIQUE,
    Unit VARCHAR(20) NOT NULL, -- g, ml, piece
    StockAmount NUMERIC(18,2) NOT NULL DEFAULT 0,
    MinStockThreshold NUMERIC(18,2) DEFAULT 100
);

CREATE TABLE Recipes (
    RecipeID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ProductID INT NOT NULL REFERENCES Products(ProductID),
    IngredientID INT NOT NULL REFERENCES Ingredients(IngredientID),
    QuantityNeeded NUMERIC(18,2) NOT NULL CHECK (QuantityNeeded > 0)
);

/* =========================================================
   Sales & Payments
   ========================================================= */
CREATE TABLE Promotions (
    PromotionID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    Code VARCHAR(30) NOT NULL UNIQUE,
    DiscountType VARCHAR(20) NOT NULL CHECK (DiscountType IN ('percent','flat','delivery')),
    DiscountValue NUMERIC(18,2) NOT NULL CHECK (DiscountValue >= 0),
    MinOrderAmount NUMERIC(18,2) NOT NULL DEFAULT 0,
    IsActive BOOLEAN NOT NULL DEFAULT TRUE,
    StartDate TIMESTAMPTZ NULL,
    EndDate TIMESTAMPTZ NULL
);

CREATE TABLE Orders (
    OrderID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    CustomerID INT NULL REFERENCES Users(UserID),
    TableID INT NULL REFERENCES Tables(TableID),
    EmployeeID INT NULL REFERENCES Users(UserID),
    PromotionID INT NULL REFERENCES Promotions(PromotionID),
    OrderDate TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    SubTotal NUMERIC(18,2) NOT NULL CHECK (SubTotal >= 0),
    Discount NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (Discount >= 0),
    TotalAmount NUMERIC(18,2) GENERATED ALWAYS AS (SubTotal - Discount) STORED,
    OrderStatus VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (OrderStatus IN ('pending','processing','preparing','served','completed','cancelled')),
    Notes VARCHAR(255) NULL
);

CREATE TABLE OrderDetails (
    OrderDetailID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    OrderID INT NOT NULL REFERENCES Orders(OrderID),
    ProductID INT NOT NULL REFERENCES Products(ProductID),
    Quantity INT NOT NULL CHECK (Quantity > 0),
    UnitPrice NUMERIC(18,2) NOT NULL CHECK (UnitPrice >= 0),
    OrderNote VARCHAR(255) NULL -- Details like "less sugar", "extra ice"
);

CREATE TABLE Payments (
    PaymentID INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    OrderID INT NOT NULL REFERENCES Orders(OrderID),
    Amount NUMERIC(18,2) NOT NULL CHECK (Amount >= 0),
    Method VARCHAR(20) NOT NULL CHECK (Method IN ('Cash','Card','BankTransfer','QR')),
    Status VARCHAR(20) NOT NULL DEFAULT 'unpaid' CHECK (Status IN ('unpaid','paid','failed','refunded')),
    PaidAt TIMESTAMPTZ NULL
);

/* =========================================================
   Seed Data
   ========================================================= */

-- Roles
INSERT INTO Roles (RoleName) VALUES ('Admin'), ('Cashier'), ('Staff');

-- Users (Password is 'admin123' hashed with SHA-256 for demo)
-- Hashed 'admin123': 240be518ebb2146c006a9a83c77d9884730415d8f2038756bf0500d075a34a4c
INSERT INTO Users (FullName, Email, Phone, PasswordHash, RoleID) VALUES
('Quản lý Tày', 'admin@taycoffee.vn', '0901234567', '240be518ebb2146c006a9a83c77d9884730415d8f2038756bf0500d075a34a4c', 1),
('Thu ngân 1', 'cashier@taycoffee.vn', '0987654321', '240be518ebb2146c006a9a83c77d9884730415d8f2038756bf0500d075a34a4c', 2);

-- Categories
INSERT INTO Categories (CategoryName) VALUES ('Cà phê'), ('Trà'), ('Bánh ngọt'), ('Khác');

-- Products
INSERT INTO Products (CategoryID, ProductName, Description, Price, ImageURL) VALUES
(1, 'Cà phê Muối', 'Signature salty cream coffee.', 35000, '☕'),
(1, 'Bạc xỉu', 'Classic Vietnamese white coffee.', 29000, '🥤'),
(2, 'Trà Đào Cam Sả', 'Refreshing peach tea with lemongrass.', 45000, '🍑'),
(3, 'Bánh Croissant', 'Buttery flaky pastry.', 25000, '🥐');

-- Ingredients
INSERT INTO Ingredients (IngredientName, Unit, StockAmount) VALUES
('Hạt cà phê Robusta', 'g', 5000),
('Sữa đặc', 'ml', 2000),
('Muối kem', 'g', 1000),
('Trà đào túi lọc', 'piece', 100),
('Bột mì', 'g', 5000);

-- Recipes
INSERT INTO Recipes (ProductID, IngredientID, QuantityNeeded) VALUES
(1, 1, 20), -- Cà phê Muối: 20g cà phê
(1, 2, 30), -- Cà phê Muối: 30ml sữa đặc
(1, 3, 10), -- Cà phê Muối: 10g muối kem
(2, 1, 20), -- Bạc xỉu: 20g cà phê
(2, 2, 50); -- Bạc xỉu: 50ml sữa đặc

-- Tables
INSERT INTO Tables (TableNumber, Capacity, Status) VALUES
('Bàn 01', 2, 'Empty'),
('Bàn 02', 2, 'Empty'),
('Bàn 03', 4, 'Empty'),
('Bàn 04', 4, 'Occupied'),
('Bàn 05', 6, 'Empty');

-- Promotions
INSERT INTO Promotions (Code, DiscountType, DiscountValue, MinOrderAmount) VALUES
('TAYNEW', 'percent', 15, 50000),
('COFFEE5', 'flat', 5000, 30000);

-- Orders Demo
INSERT INTO Orders (TableID, EmployeeID, SubTotal, Discount, OrderStatus) VALUES
(4, 2, 64000, 0, 'processing');

INSERT INTO OrderDetails (OrderID, ProductID, Quantity, UnitPrice, OrderNote) VALUES
(1, 1, 1, 35000, 'Ít đường'),
(1, 2, 1, 29000, 'Nhiều đá');
