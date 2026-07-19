USE ShahreKetabDB;
GO

/* این جدول برای گزارش بدهی شهر کتاب به ناشران لازم است. */
IF OBJECT_ID(N'dbo.PublisherPurchase', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.PublisherPurchase
    (
        PurchaseID INT IDENTITY(1,1) NOT NULL,
        PublisherID INT NOT NULL,
        StoreCode INT NOT NULL,
        PurchaseDate DATE NOT NULL,
        TotalAmount DECIMAL(18,2) NOT NULL,
        PaidAmount DECIMAL(18,2) NOT NULL
            CONSTRAINT DF_PublisherPurchase_Paid DEFAULT (0),

        CONSTRAINT PK_PublisherPurchase PRIMARY KEY (PurchaseID),
        CONSTRAINT CK_PublisherPurchase_Total CHECK (TotalAmount > 0),
        CONSTRAINT CK_PublisherPurchase_Paid
            CHECK (PaidAmount >= 0 AND PaidAmount <= TotalAmount),
        CONSTRAINT FK_PublisherPurchase_Publisher
            FOREIGN KEY (PublisherID) REFERENCES dbo.Publisher(PublisherID),
        CONSTRAINT FK_PublisherPurchase_Store
            FOREIGN KEY (StoreCode) REFERENCES dbo.Store(StoreCode)
    );
END;
GO

/* ایندکس‌های پیشنهادی برای سریع‌ترشدن گزارش‌ها */
IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_Sale_Store_Date'
      AND object_id = OBJECT_ID(N'dbo.Sale')
)
    CREATE INDEX IX_Sale_Store_Date
        ON dbo.Sale(StoreCode, InvoiceDate);
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_Sale_Customer'
      AND object_id = OBJECT_ID(N'dbo.Sale')
)
    CREATE INDEX IX_Sale_Customer
        ON dbo.Sale(CustomerCode);
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_Sale_Employee'
      AND object_id = OBJECT_ID(N'dbo.Sale')
)
    CREATE INDEX IX_Sale_Employee
        ON dbo.Sale(EmployeeNationalCode);
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_SaleItem_ISBN'
      AND object_id = OBJECT_ID(N'dbo.SaleItem')
)
    CREATE INDEX IX_SaleItem_ISBN
        ON dbo.SaleItem(ISBN);
GO

IF NOT EXISTS
(
    SELECT 1 FROM sys.indexes
    WHERE name = N'IX_Inventory_ISBN'
      AND object_id = OBJECT_ID(N'dbo.Inventory')
)
    CREATE INDEX IX_Inventory_ISBN
        ON dbo.Inventory(ISBN);
GO
