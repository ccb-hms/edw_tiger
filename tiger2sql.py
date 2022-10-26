#Author: Sam Pullman
#Agency: Center for Computational Biomedicine (CCB)
#Project: Exposome Data Warehouse - TIGER shapefiles migration from Census.gov to mssql server.

import argparse
import sys
import logging
import logging.config
import pyodbc
import zipfile
import os
import requests
import zipfile
import io
import csv
import geopandas as gpd
import matplotlib
import glob
import shutil

def find_tiger(years, uid, pwd, ipaddress, geo, cleanup):
    #go get the shape files for the geos and years
    year1, year2 = year_split(years)

    # Loop through each year in the users defined range, get each TIGER file
    for year in range(year1, year2):    
        if geo == "ZCTA":
            r = requests.get(f"https://www2.census.gov/geo/tiger/TIGER{year}/{geo}5{str(year)[-2:]}/tl_{year}_us_{geo.lower()}5{str(year)[-2:]}.zip", stream=True)
        else:
            r = requests.get(f"https://www2.census.gov/geo/tiger/TIGER{year}/{geo}/tl_{year}_us_{geo.lower()}.zip", stream=True)

        z = zipfile.ZipFile(io.BytesIO(r.content))

        filepath = f"HostData/tl_{year}_us_{geo.lower()}.shp"

        z.extractall(filepath)

        #go send the unzipped stuff to sql
        try:
            command = f'ogr2ogr -overwrite -progress -nln "dbo.tl_{year}_us_{geo.lower()}_geom" -f MSSQLSpatial "MSSQL:driver=ODBC Driver 17 for SQL Server;server={ipaddress};database=TIGERFiles;;uid={uid};pwd={pwd}" "HostData/tl_{year}_us_{geo.lower()}_geom.shp" -s_srs EPSG:4269 -t_srs EPSG:4326 -lco geom_name=GeometryLocation -lco UPLOAD_GEOM_FORMAT=wkt '

        except:
            logging.debug(f'There was a problem transferring the spacial file to sql server, please try again')
        
        #NOTE ON THIS COMMAND: the geometry type is defined as geometry as opposed to geography despite the features being geographical due to the way ogr2ogr handles 
        #the shape files. The TIGER shapefiles use SRID 4269, NAD83 geodetic datum, which corresponds to geometry type data. We will transform the data into a Geography type
        #once it is in mssql.
        
        os.system(command,)
        
        print("Updating GeometryLocation column")
        command = f'UPDATE [dbo].[tl_{year}_us_{geo.lower()}_geom] SET GeometryLocation = GeometryLocation.STUnion(GeometryLocation.STStartPoint());' 
        sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

        print(f"Creating {geo} Geography table")
        command = f'CREATE TABLE [dbo].[tl_{year}_us_{geo.lower()}] (ogr_fid   INTEGER, GeographyLocation GEOGRAPHY, zcta5ce20 NVARCHAR(MAX), geoid20 NVARCHAR(MAX), classfp20 NVARCHAR(MAX), mtfcc20 NVARCHAR(MAX), funcstat20 NVARCHAR(MAX), aland20 NUMERIC, awater20 NUMERIC, intptlat20 NVARCHAR(MAX), intptlon20 NVARCHAR(MAX), ) ; '
        sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

        print(f"Inserting data {geo} Geography table")
        command = f'INSERT INTO [dbo].[tl_{year}_us_{geo.lower()}] SELECT ogr_fid, GEOGRAPHY::STGeomFromText(GeometryLocation.STAsText(),4326), zcta5ce20, geoid20 , classfp20 , mtfcc20 , funcstat20 , aland20 , awater20 , intptlat20, intptlon20 FROM [dbo].[tl_2020_us_zcta_geom];'
        sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

        print(f"Alter {geo} ogr_fid")
        command = f'ALTER TABLE [dbo].[tl_{year}_us_{geo.lower()}] ALTER COLUMN ogr_fid INT NOT NULL;'
        sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

        print(f"Alter {geo} primary key ogr_fid")
        command = f'ALTER TABLE [dbo].[tl_{year}_us_{geo.lower()}] ADD CONSTRAINT pkogr_fid PRIMARY KEY CLUSTERED (ogr_fid);'
        sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

        print(f"Create spatial index {geo} GeographyLocation")
        command = f'CREATE SPATIAL INDEX sidxGeographyLocation ON [dbo].[tl_{year}_us_{geo.lower()}] (GeographyLocation)'
        sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)

        print("DROP original TIGER geometry table")
        command = f"DROP TABLE IF EXISTS [dbo].[tl_{year}_us_{geo.lower()}_geom]"
        sql_server(command, 'TIGERFiles', ipaddress, uid, pwd)
        
        if not cleanup:
            shutil.rmtree(filepath)     
        else:
            pass 

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


def year_split(years):
    # If the user enters a range, assign variables to the beginning and end of the range
    if "-" in years:
        years = years.replace(" ","").split("-")
        year1 = int(years[0])
        year2=int(years[1])+1

    # If the user enters a single year, assign year2 to be +1 year from the desired year, so the range function won't error out
    else:
        year1 = int(years)
        year2 = int(years)+1

    return(year1, year2)


if __name__ == "__main__":
    # Construct the argument parser
    parser = argparse.ArgumentParser()

    # Add the arguments to the parser
    parser.add_argument('-y', '--year', type= str, required=True, action="store", help='The year (format "YYYY"|]) or years (format "YYYY-YYYY") to download data for. This should be a str.')
    parser.add_argument('-u', '--uid', type= str, required=True, action="store", help='User ID for the DB server')
    parser.add_argument('-p', '--pwd', type= str, required=True, action="store", help='Password for the DB server')
    parser.add_argument('-i', '--ipaddress', type= str, required=True, action="store", help='The network address of the DB server')    
    parser.add_argument('-z', '--zcta', required=False, action="store_false", help='This option allows for the selection of the ZCTA geographical rollup.')
    parser.add_argument('-st', '--state', required=False, action="store_false", help='This option allows for the selection of the State geographical rollup.')
    parser.add_argument('-c', '--county', required=False, action="store_false", help='This option allows for the selection of the County geographical rollup.')
    parser.add_argument('-cl', '--cleanup', required=False, action="store_false", help='This option allows for the cleanup of the host directory, to save disk space.')

    # Print usage statement
    if len(sys.argv) < 2:
        parser.print_help()
        parser.print_usage()
        parser.exit()
    
    args = parser.parse_args()

    # Set up logging configs
    logging.basicConfig(filename='HostData/logging.log',level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')

    # First line of the logs
    logging.info(f'Starting data pull for {args.year}')
    
    #Create the db
    create_db(ipaddress=args.ipaddress, uid=args.uid, pwd=args.pwd)
    
    # Call the first function    
    geos = {"ZCTA":args.zcta, "STATE":args.state, "COUNTY":args.county}

    geos = [x for x in geos if geos[x]==False]

    if len(geos) == 0:
        geos = ["ZCTA", "STATE", "COUNTY"]

    for geo in geos:
        find_tiger(years=args.year, uid=args.uid, pwd=args.pwd, ipaddress=args.ipaddress, geo=geo, cleanup=args.cleanup)

    # When the data pull is complete, write the logs to a csv file for easy reviewing
    with open('HostData/logging.log', 'r') as logfile, open('LOGFILE.csv', 'w') as csvfile:
        reader = csv.reader(logfile, delimiter='|')
        writer = csv.writer(csvfile, delimiter=',',)
        writer.writerow(['EventTime', 'Origin', 'Level', 'Message'])
        writer.writerows(reader)

