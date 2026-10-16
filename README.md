Temp file

## Installation

### Requirements

- [Git](https://git-scm.com/)
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda
- [Node.js](https://nodejs.org/) (LTS)

### Install

```bash
git clone https://github.com/MarkCalcott/peptorama.git
cd peptorama
conda env create -f backend/environment.yaml
```

Build the frontend:

```bash
cd frontend
npm ci
npm run build
```

## Run the app

From the `backend` folder:

```bash
conda activate peptorama
uvicorn peptorama.main:app
```

Then open http://localhost:8000 in your browser.

## Run in development mode

Run the app in two terminals as below.

### Run the tests

```bash
cd backend
conda activate peptorama
pytest
pytest --cov=peptorama
```

### Terminal 1
```bash
cd backend
conda activate peptorama
uvicorn peptorama.main:app --reload
```

### Terminal 2
```bash
cd frontend
npm run dev
```

