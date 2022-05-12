<div id="top"></div>


<!-- PROJECT LOGO -->
<br />
<div align="center">

  <h3 align="center">ACS API</h3>

  <p align="center">
    A Docker containerized process for downloading Census TIGER line/shapefiles to sql server.
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
* [Geopandas](https://geopandas.org/en/stable/) 

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

3. Build the docker image
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
        -v ~/dev/shapefiles:/HostData \
        mcr.microsoft.com/mssql/server:2019-latest
    ```
    Here we're using the -v option, through which a new directory is created within Docker’s storage directory on the host machine, and Docker manages that directory’s contents. This way we are able to designate the dev/shapefiles directory as 'HostData' so whenever /HostData is referenced, Docker will use dev/shapefiles on the host machine. You can change this to whichever directory you're using.

    the -e option sets your environmental variables, which here establishes the password you'll need in step 6.

5. run the docker gdal container
   ```sh
    docker \
       run \
        --rm \
        --name gdal-test \
        -v ~/dev/shapefiles:/HostData \
        -i -t gdal-test
    ```
    
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


7. Errors are written to _**logging.log**_ in the directory you bind-mounted in steps 4 and 5 with the -v option. If you prefer a csv formatted view of the logs, it's written to _**LOGFILE.csv**_ in the same aforementioned directory. 

8. When the process has finished, you can view the DB with your favorite database tool by logging into the SQL server. To understand how to preserve the container with the DB, [view the docs.](https://docs.docker.com/engine/reference/commandline/commit/)

9. kill the docker containers _🚩🚩🚩IMPORTANT NOTE🚩🚩🚩: You will lose the loaded DB once the containers are killed. To preserve your work, you will need to <instructions here>. Do not kill the containers until you are 100% done working in the DB_.
  ```sh
  docker kill gdal-test
  docker kill workbench 
  ```
  
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


