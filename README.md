# 🛒 Real-Time E-Commerce Intelligence Engine

## Overview
This project is a full-stack data engineering application that simulates, processes, and visualizes a high-frequency stream of e-commerce transactions. 

Unlike static datasets, this system generates live traffic using an asynchronous event loop, processes it via a **FastAPI** microservice, persists data in **MongoDB**, and provides actionable insights through a real-time **Streamlit** dashboard.

## 🏗 Architecture
* **Ingestion Layer:** Custom Python simulator generating orders, inventory flux, and random "messy" data events (stockouts, regional disparities).
* **Backend API:** Asynchronous **FastAPI** service handling data persistence and business logic.
* **Database:** **MongoDB** (via Motor) for non-blocking write operations and flexible schema storage.
* **Frontend:** **Streamlit** dashboard polling the API for live metrics, using **Plotly** for interactive visualization.

## 🚀 Key Features
* **Live Simulation Engine:** mimic real-world sales patterns with adjustable velocity.
* **Async/Await Pipeline:** Non-blocking database operations ensuring high throughput.
* **Inventory Intelligence:** Automated low-stock alerts and "Restock" triggers.
* **Interactive Analytics:** Real-time charts for sales velocity and category distribution.

## 🛠 Tech Stack
* **Language:** Python 3.10+
* **Frameworks:** FastAPI, Streamlit
* **Database:** MongoDB
* **Libraries:** Pandas, Plotly, Pydantic, Motor, Uvicorn

## 💻 How to Run Locally

### Prerequisites
* Python 3.8+
* MongoDB installed and running locally


```bash
git clone [https://github.com/YOUR_USERNAME/e_commerce_project.git](https://github.com/YOUR_USERNAME/e_commerce_project.git)
cd e_commerce_project
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt

python -m uvicorn main:app --reload
streamlit run dashboard.py
