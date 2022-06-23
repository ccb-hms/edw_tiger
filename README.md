<div id="top"></div>


<!-- PROJECT LOGO -->
<br />
<div align="center">

  <h3 align="center">TIGER2SQL</h3>

  <p align="center">
    A Docker containerized approach to download the Census Bureau's TIGER line/shapefiles to sql server.
    <br />
    <br />
    <a href="https://github.com/ccb-hms/tiger2sql/issues">Report Bug</a>
    ·
    <a href="https://github.com/ccb-hms/tiger2sql/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>


<!-- ABOUT THE PROJECT -->
## About The Project

This project was created as a way to efficiently download TIGER line/shapefiles from the US Census site. 

The TIGER/Line Shapefiles are extracts of selected geographic and cartographic information from the Census Bureau's Master Address File (MAF)/Topologically Integrated Geographic Encoding and Referencing (TIGER) Database (MTDB). The shapefiles include information for the fifty states, the District of Columbia, Puerto Rico, and the Island areas (American Samoa, the Commonwealth of the Northern Mariana Islands, Guam, and the United States Virgin Islands). The shapefiles include polygon boundaries of geographic areas and features, linear features including roads and hydrography, and point features. These shapefiles do not contain any sensitive data or confidential data protected by Title 13 of the U.S.C.

The TIGER/Line Shapefiles contain a standard geographic identifier (GEOID) for each entity that links to the GEOID in the data from censuses and surveys. The TIGER/Line Shapefiles do not include demographic data from surveys and censuses (e.g., Decennial Census, Economic Census, American Community Survey, and the Population Estimates Program). Other, non-census, data often have this standard geographic identifier as well. Data from many of the Census Bureau’s surveys and censuses, including the geographic codes needed to join to the TIGER/Line Shapefiles, are available at the Census Bureau’s public data dissemination website (https://data.census.gov/).


<p align="right">(<a href="#top">back to top</a>)</p>


### Built With

This project is built using the following frameworks/libraries.

* [Docker](https://Docker.com/)
* [Python](https://python.org/)
* [OGR2OGR]([https://gdal.org/programs/ogr2ogr.html#ogr2ogr])

**Note on the ogr2ogr package:**  the geometry type is defined as geometry as opposed to geography due to the way ogr2ogr handles the shape files. When defined as geography the file is rotated 90 degrees requiring a manipulation afterwards to rotate it back 90 degrees to it's original shape. To avoid this, I just left it as geometry type. The same reasoning applies for the a_srs parameter, when I use the type defined in the file it loads incorrectly, but 4326 works.

<p align="right">(<a href="#top">back to top</a>)</p>


<!-- GETTING STARTED -->
## Getting Started

### Installation

1. Clone the repo into the directory of your choosing.
   ```sh
   git clone https://github.com/ccb-hms/tiger2sql.git
   ```

2. Navigate your terminal to the base directory of the newly cloned git repo.
   ```sh
   cd <dir>
   ```

3. Build the docker image by running the following command in the same directory as step 1 and 2.
   ```sh
   docker build --tag gdal-test .
   ```

4. Run the SQL Server container (for more information about Microsoft's SQL server container, view the [registry](https://hub.docker.com/_/microsoft-mssql-server))
   ```sh
    docker \
        run \
        --rm \
        --name workbench \
        -d \
        -p 1433:1433 \
        -e 'ACCEPT_EULA=Y' \
        -e 'SA_PASSWORD=asd123^&*' \
        -v ~/dev/tiger2sql:/HostData \
        -v sqldata1:/var/opt/mssql \
        mcr.microsoft.com/mssql/server:2019-latest
    ```
    
    This appears to work correctly with the Azure SQL Edge container by simply substituting `mcr.microsoft.com/azure-sql-edge:latest` for the image name.

    This command will bind mount two directories in the container: `/HostData` and `/var/opt/mssql`. `/var/opt/mssql` is the default location that SQL Server uses to store 
    database files.  By mounting a directory on your host (`/HostData`) as a data volume in your container, your database files will be persisted for future use even after the container is deleted.  See [here](https://docs.microsoft.com/en-us/sql/linux/sql-server-linux-docker-container-configure?view=sql-server-ver16&pivots=cs1-bash) for more details.

    the -e option sets environment variables inside the container that are used to configure SQL Server.

5. run the docker gdal container
   ```sh
    docker \
       run \
        --rm \
        --name gdal-test \
        -v ~/dev/tiger2sql:/HostData \
        -i -t gdal-test
    ```

    This command mounts `/HostData` as a data volume in your container, such that your database files will be persisted for future use even after the container is deleted. You *MUST* use the same location for `/HostData` as in step 4. 
    
 6. An iteractive shell within the gdal container will open. Run the following command:
    ```sh
    python3 -u < HostData/tiger2sql.py - -y/--year [year] -u/--uid [uid] -p/pwd [pwd] -i/--ipaddress [ipaddress] -z/--zcta [zcta] -st/--state [state] -c/--county [county]
    ```

    **Available parameters are:**
    
    * **-y, --year: _str_** The year you'd like to download data for in the format "YYYY" or a range of years "YYYY-YYYY". TIGER files are available from 2009-2020.
    
    * **-u, --uid: _str_** The username of the SQL server you're accessing. In the example we're using the default 'sa' uid, but be sure to change this if you are using different login credentials. 

    * **-p, --pwd: _str_** The password you defined in step 4, with the -e option.

    * **-ip, --ipaddress: _str_** The ip address that the container is using. You can find this by running the following commands in your terminal:
        ```sh
        docker network list
        ```
        to find the name of your gdal network (usually it is 'bridge') then use:
        ```sh
        docker network inspect bridge
        ```
        to find the ip address.

    * **-z, --zcta: optional** Include this option to download all TIGER files by ZCTA, or Zip Code Tabulated Areas. Can be combined with the -st/--state and -c/--county options to download for multiple rollups. Default behavior downloads for zcta, state, and counties.

    * **-st, --state: optional** Include this option to download all TIGER files by State. Can be combined with the -z/--zcta and -c/--county options to download for multiple rollups. Default behavior downloads for zcta, state, and counties.

    * **-c, --county: optional** Include this option to download all TIGER files by County. Can be combined with the -st/--state and -z/--zcta options to download for multiple rollups. Default behavior downloads for zcta, state, and counties.

    Example invocation:
    ```
    python3 -u < HostData/tiger2sql.py - --year "2017-2018" --uid "sa" --pwd "asd123^&*" --ipaddress "172.17.0.2" --zcta
    ```

    This example returns zip code tabulation area (zcta) level Tiger data from 2017-2018. The breakdown of each option is below:

    * `--year 2017-2018` : Collects data from 2017-2018
    * `--uid sa` : Default system admin uid for mssql
    * `--pwd` asd123^&* : This password was set up in step 4 (-e "SA_PASSWORD=asd123^&*" )
    * `--ipaddress` 172.17.0.2 : This is the ip address the workbench container is using
    * `--zcta` : Only the "zcta" geographical rollup will be collected. 


7. Errors are written to _**logging.log**_ in the directory you bind-mounted in steps 4 and 5 with the -v option. If you prefer a csv formatted view of the logs, it's written to _**LOGFILE.csv**_ in the same aforementioned directory. 

8. When the process has finished, kill the docker containers using
      ```sh
      docker kill workbench
      docker kill gdal-test
      ```
    then run the following docker command to re-initialize the db in a fresh container.
      ```docker run \
      --name 'sql19' \
      -e 'ACCEPT_EULA=Y' -e 'MSSQL_SA_PASSWORD='Str0ngp@ssworD \
      -p 1433:1433 \
      -v sqldata1:/var/opt/mssql \
      -d mcr.microsoft.com/mssql/server:2019-latest
      ```
      
9. You can view the DB with your favorite database tool by logging into SQL server. I like Azure Data Studio, but any remote-accessible db tool will work.

  
<p align="right">(<a href="#top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## Contributing

See the [open issues](https://github.com/ccb-hms/tiger2sql/issues) for a full list of proposed features (and known issues).

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the HMS CCB License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Sam Pullman - samantha_pullman@hms.harvard.edu

<p align="right">(<a href="#top">back to top</a>)</p>


