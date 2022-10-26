#Author: Sam Pullman
#Agency: Center for Computational Biomedicine (CCB)
#Project: HMC TIGER Shapefiles DB Project

import argparse
import sys
import pyodbc
import zipfile
import os
import requests
import zipfile
import io
import geopandas as gpd


def find_tiger(year, uid, pwd, ipaddress, geo):

    r = requests.get(f"https://www2.census.gov/geo/tiger/TIGER2020/ZCTA520/tl_2020_us_zcta520.zip", stream=True)

    z = zipfile.ZipFile(io.BytesIO(r.content))

    filepath = f"HostData/tl_{year}_us_{geo.lower()}_geom.shp"

    z.extractall(filepath)
    print()
    command = f'ogr2ogr -overwrite -progress -nln "dbo.tl_{year}_us_{geo.lower()}_geom" -f MSSQLSpatial "MSSQL:driver=ODBC Driver 17 for SQL Server;server={ipaddress};database=TIGERFiles;;uid={uid};pwd={pwd}" "HostData/tl_{year}_us_{geo.lower()}_geom.shp" -s_srs EPSG:4269 -t_srs EPSG:4326 -lco geom_name=GeometryLocation -lco UPLOAD_GEOM_FORMAT=wkt '
    os.system(command,)

    print("Updating GeometryLocation column")
    command = 'UPDATE [dbo].[tl_2020_us_zcta_geom] SET GeometryLocation = GeometryLocation.STUnion(GeometryLocation.STStartPoint());' 
    sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

    print("Creating ZCTA Geography table")
    command = 'CREATE TABLE [dbo].[tl_2020_us_zcta] (ogr_fid   INTEGER, GeographyLocation GEOGRAPHY, zcta5ce20 NVARCHAR(MAX), geoid20 NVARCHAR(MAX), classfp20 NVARCHAR(MAX), mtfcc20 NVARCHAR(MAX), funcstat20 NVARCHAR(MAX), aland20 NUMERIC, awater20 NUMERIC, intptlat20 NVARCHAR(MAX), intptlon20 NVARCHAR(MAX), ) ; '
    sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

    print("Inserting data ZCTA Geography table")
    command = 'INSERT INTO [dbo].[tl_2020_us_zcta] SELECT ogr_fid, GEOGRAPHY::STGeomFromText(GeometryLocation.STAsText(),4326), zcta5ce20, geoid20 , classfp20 , mtfcc20 , funcstat20 , aland20 , awater20 , intptlat20, intptlon20 FROM [dbo].[tl_2020_us_zcta_geom];'
    sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

    print("ISD_Spatial table creation")
    command = "DROP TABLE IF EXISTS [2021_USA].ISD_Spatial \n SELECT D.* \n INTO [2021_USA].ISD_Spatial \n FROM [2021_USA].DAILY_SUMMARY D; \n ALTER TABLE  [2021_USA].ISD_Spatial ADD GeographyLocationIsd Geography; \n UPDATE [2021_USA].ISD_Spatial SET GeographyLocationIsd = geography::STPointFromText('POINT(' + CAST([LONGITUDE] AS VARCHAR(20)) + ' ' + CAST([LATITUDE] AS VARCHAR(20)) + ')', 4326); \n ALTER TABLE [2021_USA].ISD_Spatial ALTER COLUMN Station NVARCHAR(256) NOT NULL; \n ALTER TABLE [2021_USA].ISD_Spatial ALTER COLUMN Date Date NOT NULL; \n ALTER TABLE [2021_USA].ISD_Spatial ADD CONSTRAINT pkStationDate2 PRIMARY KEY CLUSTERED (Station, Date); \n CREATE SPATIAL INDEX sidxGeographyLocation ON [2021_USA].ISD_Spatial (GeographyLocationIsd)"
    sql_server(command, 'ISD_HMC', ipaddress, uid, pwd)

    print("Alter ZCTA ogr_fid")
    command = 'ALTER TABLE dbo.tl_2020_us_zcta ALTER COLUMN ogr_fid INT NOT NULL;'
    sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

    print("Alter ZCTA primary key ogr_fid")
    command = 'ALTER TABLE dbo.tl_2020_us_zcta ADD CONSTRAINT pkogr_fid PRIMARY KEY CLUSTERED (ogr_fid);'
    sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

    print("Create spatial index zcta GeographyLocation")
    command = 'CREATE SPATIAL INDEX sidxGeographyLocation ON dbo.tl_2020_us_zcta (GeographyLocation)'
    sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

def create_db(ipaddress, uid, pwd):
    # If the AmericanCommunitySurvey db has already been created, drop it and re-create it blank
    drop_create_db = '''USE master;
                    ALTER DATABASE [TIGERFiles] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                    DROP DATABASE [TIGERFiles] ;
                    CREATE DATABASE [TIGERFiles] ;'''

    # Call the sql_server function to connect to the db and execute the query
    sql_server(drop_create_db, 'master', ipaddress, uid, pwd)

def sql_server(query, db, ipaddress, uid, pwd):
    conn = pyodbc.connect(f"DRIVER=ODBC Driver 17 for SQL Server;SERVER={ipaddress};DATABASE={db};UID={uid};PWD={pwd}", autocommit=True)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()

if __name__ == "__main__":
    # Construct the argument parser
    parser = argparse.ArgumentParser()

    # Add the arguments to the parser
    parser.add_argument('-y', '--year', type= str, required=True, action="store", help='The year (format "YYYY"|]) as a string')
    parser.add_argument('-u', '--uid', type= str, required=True, action="store", help='User ID for the DB server')
    parser.add_argument('-p', '--pwd', type= str, required=True, action="store", help='Password for the DB server')
    parser.add_argument('-i', '--ipaddress', type= str, required=True, action="store", help='The network address of the DB server')    
    parser.add_argument('-z', '--zcta', required=False, action="store_false", help='This option allows for the selection of the ZCTA geographical rollup.')

    # Print usage statement
    if len(sys.argv) < 2:
        parser.print_help()
        parser.print_usage()
        parser.exit()

    args = parser.parse_args()

    #Create the db
    # create_db(ipaddress=args.ipaddress, uid=args.uid, pwd=args.pwd)

    # Call the first function    
    geos = {"ZCTA":args.zcta}

    geos = [x for x in geos if geos[x]==False]

    if len(geos) == 0:
        geos = ["ZCTA"]

    for geo in geos:
        find_tiger(year=args.year, uid=args.uid, pwd=args.pwd, ipaddress=args.ipaddress, geo=geo)
