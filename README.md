
# AuraVoice

AuraVoice is a web application that utilizes the power of machine learning to convert your voice into midi. With just a few clicks all you have to do is hum, sing or speak into your microphone and it will automatically convert your voice into a musical composition to which you can use in your own digital audio workstations, songs, or any application you'd like! 

AuraVoice is also a social media platform in which you can share your creations and also browse through other users MIDI files! AuraVoice is able to do this through the [CREPE Pitch Tracker CNN Deep Neural Network Model](https://github.com/marl/crepe). Feel free to check out their repository for more details!  

## Team Members: 
- [Aditya Pandhare](https://github.com/awesomeadi00)
- [Anzhelika Nastashchuk](https://github.com/annsts)
- [Baani Pasrija](https://github.com/zeepxnflrp)
- [Zander Chen](https://github.com/ccczy-czy)


## Setup from scratch: 

### Docker Installation 

Before you start the steps below, make sure you have the following downloaded on your system: 

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### AWS Configuration Setup

 1. Go to [AWS website](https://aws.amazon.com/cli/) and download AWS Command Line Interface based on your operating system.
 2. Go to terminal and type the following line: `aws configure`
 3. Follow the prompt and provide values:
 ```
 AWS Access Key ID: <AWS_ACCESS_KEY_ID in provided .env file>

 AWS Secret Access Key: <AWS_SECRET_ACCESS_KEY in provided .env file>
 
 Default region name: us-east-1
 
 Default output format: json
 ```

Furthermore if you are starting this project from scratch, you can visit the [AWS Console](https://aws.amazon.com/free/?trk=3b81af00-66e9-4dfa-8d40-13976c5ec632&sc_channel=ps&ef_id=Cj0KCQjwtMHEBhC-ARIsABua5iSj6tpYHEFKOtPW8c94SQyLZDVaqc2A-oj4io059T6aJ08Wr008fLoaArKiEALw_wcB:G:s&s_kwcid=AL!4422!3!733904860063!e!!g!!aws%20console!22269309085!176152675838&gad_campaignid=22269309085&gbraid=0AAAAADjHtp9QrWUlNJI3b6UfDIOW86Hcf&gclid=Cj0KCQjwtMHEBhC-ARIsABua5iSj6tpYHEFKOtPW8c94SQyLZDVaqc2A-oj4io059T6aJ08Wr008fLoaArKiEALw_wcB) with your account and visit the S3 service and create a Bucket. 

You can also get your AWS Access Key ID and AWS Secret Access Key through the following steps:  
- From AWS Console 
- Click on your account on the top left
- Security Credentials 
- Create Access Key

## Running the Application:

1. Clone the repository:
```
git clone https://github.com/awesomeadi00/AuraVoice.git
```

2. Navigate to the project directory: 
```
cd AuraVoice
```

3. Create .env files inside the `machine_learning_client/` folder and `web_app/` folder each (Variables should be provided to you):
```
.env for machine_learning_client/ folder:

AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
S3_BUCKET_NAME
```

```
.env for web_app/ folder:

# MongoDB Configuration (Local Container - auto-configured)
MONGO_URI=mongodb://admin:password123@mongodb:27017/auravoice?authSource=admin
MONGO_DBNAME=auravoice

# Flask Configuration
FLASK_APP=app.py
APP_SECRET_KEY=your-secret-key-here

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
S3_BUCKET_NAME=your-s3-bucket-name
```

4. Build docker images and run the containers:
```
docker compose up --build -d
```

5. Open the application in your browser:
```
http://localhost:5001
```

6. To stop the containers, run the command: 
```
docker-compose stop
```