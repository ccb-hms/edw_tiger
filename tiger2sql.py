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

def find_tiger(years, uid, pwd, ipaddress, geo):
    #go get the shape files for the geos and years
    year1, year2 = year_split(years)

    # Loop through each year in the users defined range, get each TIGER file
    for year in range(year1, year2):    
        if geo == "ZCTA":
            r = requests.get(f"https://www2.census.gov/geo/tiger/TIGER{year}/{geo}5/tl_{year}_us_{geo.lower()}510.zip", stream=True)
        else:
            r = requests.get(f"https://www2.census.gov/geo/tiger/TIGER{year}/{geo}/tl_{year}_us_{geo.lower()}.zip", stream=True)

        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall(f"HostData/tl_{year}_us_{geo.lower()}.shp")

        #go send the unzipped stuff to sql
        try:
            command = f'ogr2ogr -f "MSSQLSpatial" "MSSQL:server={ipaddress};database=TIGERFILES;driver=ODBC Driver 17 for SQL Server;uid={uid};pwd={pwd}" "HostData/tl_{year}_us_{geo.lower()}.shp" -lco GEOMETRY_NAME=GEOM -lco GEOM_TYPE=GEOMETRY -a_srs "EPSG:4326" -overwrite -progress -skipfailures -lco UPLOAD_GEOM_FORMAT=wkb'
        
        except:
            logging.debug(f'There was a problem transferring the spacial file to sql server, please try again')
        
        
        #NOTE ON THIS COMMAND: the geometry type is defined as geometry as opposed to geography due to the way ogr2ogr handles the shape files. When defined as geography,
        #the file is rotated 90 degrees, requiring a manipulation afterwards to rotate it 90 degrees to it's original shape. To avoid this, I just left it as geom.
        # same reasoning for the a_srs type, when I use the type defined in the file it loads incorrectly, but 4326 works.
        
        os.system(command,)

def create_db(ipaddress, uid, pwd):
    # If the AmericanCommunitySurvey db has already been created, drop it and re-create it blank
    drop_create_db = '''USE master;
                    ALTER DATABASE [TIGERFILES] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
                    DROP DATABASE [TIGERFILES] ;
                    CREATE DATABASE [TIGERFILES] ;'''

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
        year2=int(years[1])

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
        find_tiger(years=args.year, uid=args.uid, pwd=args.pwd, ipaddress=args.ipaddress, geo=geo)

    # When the data pull is complete, write the logs to a csv file for easy reviewing
    with open('HostData/logging.log', 'r') as logfile, open('LOGFILE.csv', 'w') as csvfile:
        reader = csv.reader(logfile, delimiter='|')
        writer = csv.writer(csvfile, delimiter=',',)
        writer.writerow(['EventTime', 'Origin', 'Level', 'Message'])
        writer.writerows(reader)

