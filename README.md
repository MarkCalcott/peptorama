# Peptorama: Structure creation and exploratory data analysis of non-ribosomal peptides

## Overview

Peptorama is an application for creating peptide structures and exploratory data
analysis. It is a browser-based web app with a Python backend for data processing.

Peptorama is available from https://peptorama.com/

## Installation

### Requirements

- [Git](https://git-scm.com/)
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or Anaconda
- [Node.js](https://nodejs.org/) (Optional for development)

### Quickest install

This install uses a prebuilt frontend and is the quickest to set up.

```bash
git clone https://github.com/MarkCalcott/peptorama.git
cd peptorama
conda env create -f backend/environment.yaml
```

From the `backend` folder:

```bash
conda activate peptorama
uvicorn peptorama.main:app
```

Then open http://localhost:8000 in your browser. Example data can be found in
the data folder.

### Development install

For users who want to modify the frontend. First perform the quick install and then...

Build the frontend:

```bash
cd frontend
npm ci
npm run build
```

Run the app in two terminals as below.

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

Then open http://localhost:5173 in your browser.

## Testing

Run tests for the backend

```bash
cd backend
conda activate peptorama
pytest
pytest --cov=peptorama
```

Run tests for frontend

```bash
cd frontend
npx vitest
```
