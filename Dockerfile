FROM osgeo/gdal:ubuntu-full-latest-amd64
#------------------------------------------------------------------------------
# Install system tools and libraries via apt
#------------------------------------------------------------------------------
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install \
        -y \
        curl \
        wget \ 
        make \
        pkg-config \
        gnupg \
        krb5-user \
        libkrb5-dev \
        unixodbc \
        unixodbc-dev \      
        libssl-dev \
        pip \
        python3 \
    && rm -rf /var/lib/apt/lists/*
#------------------------------------------------------------------------------
# Install and configure database connectivity components
#------------------------------------------------------------------------------
# install MS SQL Server ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && echo "deb [arch=amd64] https://packages.microsoft.com/ubuntu/20.04/prod bionic main" | tee /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install msodbcsql17
# install FreeTDS driver
RUN wget ftp://ftp.freetds.org/pub/freetds/stable/freetds-1.1.40.tar.gz
RUN tar zxvf freetds-1.1.40.tar.gz
RUN cd freetds-1.1.40 && ./configure --enable-krb5 && make && make install
RUN rm -r /freetds*
# tell unixodbc where to find the FreeTDS driver shared object
RUN echo '\n\
[FreeTDS]\n\
Driver = /usr/local/lib/libtdsodbc.so \n\
' >> /etc/odbcinst.ini

# install additional python libraries
RUN pip3 install pyodbc==4.0.32
RUN pip3 install scrapy
RUN pip3 install pandas==1.4.2
RUN pip3 install openpyxl==3.0.9
RUN pip3 install lxml==4.8.0
RUN pip3 install requests==2.27.1
RUN pip3 install geopandas
RUN pip3 install matplotlib
