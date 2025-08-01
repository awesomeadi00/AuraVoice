![Workflow Status](https://github.com/software-students-fall2023/4-containerized-app-exercise-wacotacotruck/actions/workflows/lint.yml/badge.svg?branch=main&kill_cache=1)
![Workflow Status](https://github.com/software-students-fall2023/4-containerized-app-exercise-wacotacotruck/actions/workflows/frontend.yml/badge.svg?branch=main&kill_cache=1)
![Workflow Status](https://github.com/software-students-fall2023/4-containerized-app-exercise-wacotacotruck/actions/workflows/backend.yml/badge.svg?branch=main&kill_cache=1)
![Workflow Status](https://github.com/software-students-fall2023/4-containerized-app-exercise-wacotacotruck/actions/workflows/ci-cd.yml/badge.svg?branch=main&kill_cache=1)

# VocalMIDI

Build a containerized app that uses machine learning. See [instructions](./instructions.md) for details.

## [Live Demo](http://159.65.44.240:5001/)
If using Google Chrome, follow these steps to address microphone access issues in the live demo:

1. **Open Chrome Flags**:
   - Type `chrome://flags/#unsafely-treat-insecure-origin-as-secure` in the address bar and press Enter.

2. **Enable Insecure Origins**:
   - Add `http://159.65.44.240:5001/` in the "Insecure origins treated as secure" section.
   - Change dropdown to 'Enabled'.

3. **Relaunch Chrome**:
   - Click 'Relaunch' to apply changes.

## Team Members: 
- [Aditya Pandhare](https://github.com/awesomeadi00)
- [Anzhelika Nastashchuk](https://github.com/annsts)
- [Baani Pasrija](https://github.com/zeepxnflrp)
- [Zander Chen](https://github.com/ccczy-czy)

## Description:

VocalMIDI is a web application that utilizes the power of machine learning to convert your voice into midi. With just a few clicks all you have to do is hum, sing or speak into your microphone and it will automatically convert your voice into a musical composition to which you can use in your own Digital Audio Workstations, Songs, or whatever application you'd like! You can browse through other users midi files and search through whatever sounds great to your ears!

## Setup: 

### Prerequisites: 

Before you start the steps below, make sure you have the following downloaded on your system: 

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

**Download AWS Command Line Interface:**

 1. Go to [AWS website](https://aws.amazon.com/cli/) and download AWS Command Line Interface based on your operating system.
 2. Go to terminal and type the following line: `aws configure`
 3. Follow the prompt and provide values:
 ```
 AWS Access Key ID: <Value for variable AWS_ACCESS_KEY_ID in provided .env file>
 AWS Secret Access Key: <Value for variable AWS_SECRET_ACCESS_KEY in provided .env file>
 Default region name: us-east-1
 Default output format: json
 ```

### Running the Application:

1. Clone the repository:
```
git clone https://github.com/software-students-fall2023/4-containerized-app-exercise-wacotacotruck.git
```

2. Navigate to the project directory: 
```
cd 4-containerized-app-exercise-wacotacotruck
```

3. Create .env files inside the `machine_learning_client/` folder and `web_app/` folder each (Variables should be provided to you):
```
.env for machine_learning_client/ folder:

AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
S3_BUCKET_NAME


.env for web_app/ folder:

MONGO_DBNAME
MONGO_URI
FLASK_APP
GITHUB_SECRET
GITHUB_REPO
APP_SECRET_KEY
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
S3_BUCKET_NAME
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
