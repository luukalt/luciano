CREATE TABLE [dbo].[DIVERSEN] (
    [ID] [int] IDENTITY(1,1) NOT NULL,
	[Barcode] [nvarchar](100) NULL,
    [Omschrijving] [nvarchar](100) NULL,
    [Aantal] [int] NULL,
    CONSTRAINT [PK_DIVERSEN] PRIMARY KEY CLUSTERED 
    (
        [ID] ASC
    ) WITH (
        PAD_INDEX  = OFF,
        STATISTICS_NORECOMPUTE  = OFF,
        IGNORE_DUP_KEY = OFF,
        ALLOW_ROW_LOCKS  = ON,
        ALLOW_PAGE_LOCKS  = ON
    ) ON [PRIMARY]
) ON [PRIMARY];

-- Insert dummy data
INSERT INTO [dbo].[DIVERSEN] 
    (Barcode, Omschrijving, Aantal)
VALUES (1, 'Item 1', 10),
       (2, 'Item 2', 15),
       (3, 'Item 3', 20),
       (4, 'Item 4', 8),
       (5, 'Item 5', 12),
       (6, 'Item 6', 18),
       (7, 'Item 7', 25),
       (8, 'Item 8', 30);
