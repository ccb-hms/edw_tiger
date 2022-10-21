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

    command = f'ogr2ogr -f "MSSQLSpatial" "MSSQL:server={ipaddress};database=TIGERFiles;driver=ODBC Driver 17 for SQL Server;uid={uid};pwd={pwd}" "HostData/tl_{year}_us_{geo.lower()}_geom.shp" -lco GEOMETRY_NAME=Geo -lco GEOM_TYPE=GEOGRAPHY -s_srs "EPSG:4269" -t_srs "EPSG:4326" -overwrite -progress -lco UPLOAD_GEOM_FORMAT=wkb'

    os.system(command,)


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
    create_db(ipaddress=args.ipaddress, uid=args.uid, pwd=args.pwd)
    
    # Call the first function    
    geos = {"ZCTA":args.zcta}

    geos = [x for x in geos if geos[x]==False]

    if len(geos) == 0:
        geos = ["ZCTA"]

    for geo in geos:
        find_tiger(year=args.year, uid=args.uid, pwd=args.pwd, ipaddress=args.ipaddress, geo=geo)

