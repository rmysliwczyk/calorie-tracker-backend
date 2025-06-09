# Calorie Tracker - backend
This is a backend portion of my calorie tracker web app

## General overview:
This web application enables users to monitor their caloric intake by logging their daily meals. The main feature of the app is a database that users can update with their favorite food products. For each product, the database stores essential nutritional values per 100 grams, including calories, fats, carbohydrates, and proteins. Users can add their products and search for them using a responsive search function or by scanning product barcodes.

## Backend overview
This backend server uses JWT tokens for authentication of the users. For all available endpoints and docs about the API please visit the swagger docs page [here](https://ct.mysliwczykrafal.webredirect.org/api/docs).  
I'm hosting this service on my local network using Nginx as a reverse proxy and Docker as a flexible tool for continous deployment. Deployment happens whenever new code is pushed to main branch and is triggered via a webhook pointing to my Jenkins service.  
GitHub is then notified about success or failure during the build process. All of my .env contents are stored securely as secrets both on GitHub and in Jenkins.

## Tech stack/features - backend
- FastAPI
  - SQLModel - for ORM database integration
  - Alembic - for database migrations
- PostgreSQL - easily interchangable, but currently I'm running a dedicated server machine on my local network for hosting PostgreSQL
- Docker - for easy deployment
- Jenkins - for continuous deployment
- GitHub actions - for continuous integration

## How to Run the Application locally
Make sure you have Python 3, PIP, and the Python venv installed on your system. For Debian-based systems, you can ensure you have everything you need by entering the following command:
```
sudo apt install python3 python3-venv python3-pip 
``` 
Once you have cloned or downloaded the source code, navigate to the root folder of the calorie-tracker and run the following commands: 
```
bash python3 -m venv .
source bin/activate
pip install -r requirements.txt
fastapi dev
``` 
If you are using a different operating system, you will need to figure out how to install the modules specified in the `requirements.txt` file.
