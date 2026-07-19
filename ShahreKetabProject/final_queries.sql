USE ShahreKetabDB;
GO

/* 1) مشخصات فروشگاه‌های یک شهر */
DECLARE @CityName NVARCHAR(50) = N'اصفهان';
SELECT s.StoreCode, c.CityName, c.ProvinceName, s.Phone, s.Address
FROM dbo.Store AS s
JOIN dbo.City AS c ON c.CityCode = s.CityCode
WHERE c.CityName = @CityName;
GO

/* 2) فروشگاه‌هایی که کتاب نویسنده مشخص را ندارند */
DECLARE @AuthorName NVARCHAR(100) = N'پیشرو';
SELECT s.StoreCode, c.CityName, s.Phone, s.Address
FROM dbo.Store AS s
JOIN dbo.City AS c ON c.CityCode = s.CityCode
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.Inventory AS i
    JOIN dbo.BookAuthor AS ba ON ba.ISBN = i.ISBN
    JOIN dbo.Author AS a ON a.AuthorID = ba.AuthorID
    WHERE i.StoreCode = s.StoreCode
      AND i.AvailableQuantity > 0
      AND a.AuthorName = @AuthorName
);
GO

/* 3) جمع فروش یک فروشگاه در بازه زمانی */
DECLARE @StoreCode INT = 4545;
DECLARE @StartDate DATE = '2009-01-01';
DECLARE @EndDate DATE = '2011-01-01';
SELECT
    s.StoreCode,
    COUNT(DISTINCT s.InvoiceNumber) AS InvoiceCount,
    SUM(si.Quantity) AS SoldQuantity,
    SUM(si.Quantity * si.UnitPrice) AS TotalSales
FROM dbo.Sale AS s
JOIN dbo.SaleItem AS si ON si.InvoiceNumber = s.InvoiceNumber
WHERE s.StoreCode = @StoreCode
  AND s.InvoiceDate BETWEEN @StartDate AND @EndDate
GROUP BY s.StoreCode;
GO

/* 4) کارمندان یک فروشگاه */
DECLARE @EmployeeStoreCode INT = 2545;
SELECT NationalCode, FullName, Phone, Address, Gender, StoreCode
FROM dbo.Employee
WHERE StoreCode = @EmployeeStoreCode;
GO

/* 5) فروش‌های یک کارمند */
DECLARE @EmployeeNationalCode CHAR(10) = '0047853651';
SELECT
    s.InvoiceNumber,
    s.InvoiceDate,
    e.FullName AS EmployeeName,
    c.FullName AS CustomerName,
    s.StoreCode,
    b.Title,
    si.Quantity,
    si.UnitPrice,
    si.Quantity * si.UnitPrice AS LineTotal
FROM dbo.Sale AS s
JOIN dbo.Employee AS e ON e.NationalCode = s.EmployeeNationalCode
JOIN dbo.Customer AS c ON c.CustomerCode = s.CustomerCode
JOIN dbo.SaleItem AS si ON si.InvoiceNumber = s.InvoiceNumber
JOIN dbo.Book AS b ON b.ISBN = si.ISBN
WHERE s.EmployeeNationalCode = @EmployeeNationalCode;
GO

/* 6) کتاب‌های نویسنده یا موضوع */
DECLARE @SearchText NVARCHAR(100) = N'ثروت';
SELECT DISTINCT b.ISBN, b.Title, b.Subject, p.PublisherName, b.Price
FROM dbo.Book AS b
JOIN dbo.Publisher AS p ON p.PublisherID = b.PublisherID
LEFT JOIN dbo.BookAuthor AS ba ON ba.ISBN = b.ISBN
LEFT JOIN dbo.Author AS a ON a.AuthorID = ba.AuthorID
WHERE b.Subject LIKE N'%' + @SearchText + N'%'
   OR a.AuthorName LIKE N'%' + @SearchText + N'%';
GO

/* 7) مشتریان بدهکار */
DECLARE @MinimumDebt DECIMAL(18,2) = 10000;
SELECT CustomerCode, FullName, Phone, Address, DebtAmount
FROM dbo.Customer
WHERE DebtAmount > @MinimumDebt
ORDER BY DebtAmount DESC;
GO

/* 8) خریدهای یک مشتری */
DECLARE @CustomerCode INT = 123456;
SELECT
    c.FullName,
    s.InvoiceNumber,
    s.InvoiceDate,
    st.StoreCode,
    st.Address,
    b.ISBN,
    b.Title,
    si.Quantity,
    si.UnitPrice,
    si.Quantity * si.UnitPrice AS LineTotal
FROM dbo.Customer AS c
JOIN dbo.Sale AS s ON s.CustomerCode = c.CustomerCode
JOIN dbo.Store AS st ON st.StoreCode = s.StoreCode
JOIN dbo.SaleItem AS si ON si.InvoiceNumber = s.InvoiceNumber
JOIN dbo.Book AS b ON b.ISBN = si.ISBN
WHERE c.CustomerCode = @CustomerCode;
GO

/* 9) کتاب‌های فروخته‌نشده در بازه زمانی */
DECLARE @NotSoldStart DATE = '2009-10-01';
DECLARE @NotSoldEnd DATE = '2010-01-10';
SELECT b.ISBN, b.Title, b.Subject, p.PublisherName, b.Price
FROM dbo.Book AS b
JOIN dbo.Publisher AS p ON p.PublisherID = b.PublisherID
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.SaleItem AS si
    JOIN dbo.Sale AS s ON s.InvoiceNumber = si.InvoiceNumber
    WHERE si.ISBN = b.ISBN
      AND s.InvoiceDate BETWEEN @NotSoldStart AND @NotSoldEnd
);
GO

/* 10) فروشگاه‌های با موجودی کمتر از حد مجاز برای یک کتاب */
DECLARE @ISBN VARCHAR(20) = '7845-45';
SELECT
    st.StoreCode,
    c.CityName,
    st.Address,
    b.Title,
    i.AvailableQuantity,
    i.MinimumQuantity,
    i.MinimumQuantity - i.AvailableQuantity AS Shortage
FROM dbo.Inventory AS i
JOIN dbo.Store AS st ON st.StoreCode = i.StoreCode
JOIN dbo.City AS c ON c.CityCode = st.CityCode
JOIN dbo.Book AS b ON b.ISBN = i.ISBN
WHERE i.ISBN = @ISBN
  AND i.AvailableQuantity < i.MinimumQuantity;
GO

/* 11) بدهی به ناشر */
DECLARE @PublisherName NVARCHAR(100) = N'آیالر';
SELECT
    p.PublisherName,
    SUM(pp.TotalAmount) AS TotalPurchase,
    SUM(pp.PaidAmount) AS TotalPaid,
    SUM(pp.TotalAmount - pp.PaidAmount) AS Debt
FROM dbo.PublisherPurchase AS pp
JOIN dbo.Publisher AS p ON p.PublisherID = pp.PublisherID
WHERE p.PublisherName = @PublisherName
GROUP BY p.PublisherName;
GO
