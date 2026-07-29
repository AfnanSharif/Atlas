<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=FC466B,3F5EFB&height=200&section=header&text=Atlas&fontSize=70&fontColor=ffffff&animation=twinkling" width="100%" />

<img src="https://img.icons8.com/?id=KRrT886bjuhL&format=png&size=100" width="90" />

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&weight=600&size=22&duration=2500&pause=1000&color=FC466B&center=true&vCenter=true&width=700&height=50&lines=Offline-first%20personalized%20travel%20itinerary%20generation;Python%20+%20Streamlit" alt="Typing SVG" />

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](#)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](#)
[![Transformers](https://img.shields.io/badge/Transformers-FFD21E?style=for-the-badge)](#)

</div>

---

## 📖 Overview

**Atlas** — Offline-first personalized travel itinerary generation.

Core logic lives in `src/travel_itinerary/`. Configuration is centralized in `config/settings.yaml`
and secrets/API keys are loaded from a local `.env` (see `.env.example`).

## 🏗️ Project Layout

```
Atlas/
├── app.py               # Streamlit entry point
├── src/travel_itinerary/
│   └── ...              # Core package — offline-first personalized travel itinerary generation
├── config/settings.yaml # App configuration
├── tests/                # Unit tests
├── scripts/setup.sh      # venv + install helper (macOS/Linux)
├── requirements.txt
```


## ⚡ Setup & Run

### 🪟 Windows (PowerShell / CMD)
```cmd
git clone https://github.com/AfnanSharif/Atlas.git
cd Atlas

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
:: edit .env to add any API keys — the app runs fully offline without them

streamlit run app.py
```

### 🍎 macOS / 🐧 Linux
```bash
git clone https://github.com/AfnanSharif/Atlas.git
cd Atlas

./scripts/setup.sh                 # creates .venv and installs requirements.txt
source .venv/bin/activate

cp .env.example .env
# edit .env to add any API keys — the app runs fully offline without them

streamlit run app.py
```

Open **http://localhost:8501**.

```bash
make test    # run the test suite
make lint    # lint the codebase
```

---

<div align="center">

**Created by [AfnanSharif](https://github.com/AfnanSharif)** · ⭐ star this repo if it helped you

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=FC466B,3F5EFB&height=80&section=footer" width="100%" />

</div>
