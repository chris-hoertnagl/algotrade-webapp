# algotrade
An algorithmic trading web app.  
The app is using binance, so you need a binance account in order to use it.  
The app is using docker, so it can be deployed at any system that runs docker.

This project is intended as a small PoC for building a WebApp that allows to 
create no-Code trading algorithms and is not being updated anymore.

NOTE - you first need to add your Binance API-KEY to the config_binance.py file before this will work.
  
##How to setup the project for developement:
Open a Terminal and choose a folder where you want to create your virtual environment.

Then execute the following commands to setup the environment:  
change to your target directory for the environment  
pip install --upgrade pip  
pip install virtualenv  
python -m virtualenv algoenv  
algoenv\Scripts\activate

pip install -r requirements.txt  
 
install docker (for windows: https://docs.docker.com/docker-for-windows/install/)

In a Terminal:  
docker-compose build  
docker-compose up

The application will be running at 127.0.0.1:8000 (localhost)
