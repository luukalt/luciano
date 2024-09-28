CREATE TABLE [dbo].[POTJES] (
    [ID] [int] IDENTITY(1,1) NOT NULL,
	[Barcode] [nvarchar](100) NULL,
    [Omschrijving] [nvarchar](100) NULL,
    [Aantal] [int] NULL,
    CONSTRAINT [PK_GEBAK] PRIMARY KEY CLUSTERED 
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
INSERT INTO [dbo].[POTJES] 
    (Barcode, Omschrijving, Aantal)
VALUES (1, 'Item 1', 10),
       (2, 'Item 2', 15);