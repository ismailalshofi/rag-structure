# rag-structure

Retrieval-Augmented Generation (RAG) Implementation

## Setup

1) Download and install MiniConda from [here](https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html)

2) Create new conda env for the project:

```bash
$ conda create -n rag-structure python=3.13
```

3) Activate the created env:

```bash
$ conda activate rag-structure
```

## Installation

### Install requirements:

```bash
$ pip install -r requirements.txt
```

### Setup environment variables:

```bash
$ cp .env.example .env
```

Add your environment variables to '.env' like local variables or API keys

## Run the FastAPI server:

```bash
$ uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Postman collection: [/app/assets/rag-structure.postman_collection.json](/app//assets/rag-structure.postman_collection.json)
