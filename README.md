Temp file

## Installation

The simplest installation uses node.js, npm and conda

```
git clone https://github.com/<your-username>/peptorama.git
cd peptorama

:: Backend
conda env create -f backend/environment.yaml
conda activate peptorama
cd backend
pytest

:: Frontend
cd ..\frontend
npm ci
npm run build
```

## Run the app

Once installed, first run the below commands to start a local server and use peptorama and then view the app at: http://localhost:8000/

```
cd ..\backend
conda activate peptorama
uvicorn peptorama.main:app
```

## Run in development mode

To develop the app, run the app in two terminals as below.

### Terminal 1
```
conda activate peptorama
cd backend
uvicorn peptorama.main:app --reload
```

### Terminal 2
```
cd frontend
npm run dev
```

