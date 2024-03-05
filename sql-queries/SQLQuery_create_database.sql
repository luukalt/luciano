CREATE TABLE [dbo].[DATA](
[ID] [int] IDENTITY(1,1) NOT NULL,
[Scale] [nvarchar](100) NULL,
[Description] [nvarchar](100) NULL,
[WgtDate] [date] NULL,
[WgtTime] [time](7) NULL,
[WgtDateTime] [datetime] NULL,
[WgtNbr] [nvarchar](20) NULL,
[ValueGross] [decimal](18, 4) NULL,
[ValueTare] [decimal](18, 4) NULL,
[ValueNet] [decimal](18, 4) NULL,
[WgtUnit] [nvarchar](10) NULL,
[Cancel] [int] NULL,
[Type] [nvarchar](100) NULL,
[InStock] [int] NULL,
CONSTRAINT [PK_DATA] PRIMARY KEY CLUSTERED 
(
[ID] ASC
)WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF,
IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON)
ON [PRIMARY]
) ON [PRIMARY]