# 🛡️ Hybrid ML-Based Real-Time E-Commerce Fraud Detection System

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.3-000000?style=flat&logo=flask&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-F7931E?style=flat&logo=scikit-learn&logoColor=white)
![Accuracy](https://img.shields.io/badge/Accuracy-98.8%25-brightgreen?style=flat)
![AUC-ROC](https://img.shields.io/badge/AUC--ROC-0.98-blue?style=flat)
![Published](https://img.shields.io/badge/Published-IJEDR%20Vol.14%20Issue%202-orange?style=flat)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

A full-stack, ML-powered fraud detection system for e-commerce transactions. Uses a **weighted ensemble of Random Forest + Gradient Boosting** combined with rule-based logic to classify transactions in real time, with an admin dashboard, role-based auth, and CSV batch processing.

> 📄 **Published:** "AI-Powered Hybrid Machine Learning Based Real-Time E-Commerce Fraud Detection System" — IJEDR Volume 14, Issue 2, April 2026 | Paper ID: IJEDR2602373  
> 👩‍💻 **Authors:** Joy Angelin J, Lakshmi Poorani S | Guide: Mrs. N. Rajapriya M.E, (Ph.D)

---

## 📊 Model Performance

| Metric | Score |
|---|---|
| **Accuracy** | **98.8%** |
| **Precision** | **97.5%** |
| **Recall** | **96.2%** |
| **F1-Score** | **96.9%** |
| **AUC-ROC** | **0.98** |

---

## 📸 Screenshots

| Dashboard | Fraud Prediction | Model Info |
|---|---|---|
| Total txns, fraud count, risk score | Real-time per-transaction scoring | RF metrics + feature importance |

> *101 transactions processed — 99 fraud detected, avg risk score 96.7%*

---

## ✨ Features

**5 Core Modules:**

**1. Dashboard** — Live stats: total transactions, fraud count, legitimate count, average risk score. Recent transaction table with fraud/legitimate labels.

**2. Fraud Prediction** — Enter transaction details (amount, hour, location, device, payment method) and get an instant fraud probability score with hybrid ML + rule-based decision.

**3. Analytics** — CSV batch upload for bulk fraud analysis. Processes multiple transaction records in one shot, returns per-row fraud classification.

**4. Model Information** — Random Forest classifier overview, key features, and live performance metrics panel.

**5. Alert & Monitoring** — Fraudulent transactions are highlighted in real time. Admin can view all flagged transactions across users.

**Additional:**
- Role-based auth: Admin, regular User
- Admin dashboard: approve/manage users, view all transactions
- Pending state for new user accounts until admin approval
- SQLite persistence for users and transaction history
- CSV upload with format validation

---

## 🧠 ML Architecture

### Hybrid Detection Engine

```
Transaction Input
       ↓
Feature Extraction (7 features)
       ↓
StandardScaler normalization
       ↓
┌──────────────────────────────────┐
│  Random Forest (100 trees)       │ → RF score
│  Gradient Boosting (100 trees)   │ → GB score
└──────────────────────────────────┘
       ↓
Weighted Ensemble (RF + GB average)
       ↓
Rule-Based Boost Layer
  • Amount > threshold → boost score
  • International location + VPN device → boost
  • New account + high amount → boost
       ↓
Final Fraud Score (0–100%) + Label
```

### Features Used

| Feature | Description | Encoding |
|---|---|---|
| `amount` | Transaction amount (₹) | Continuous |
| `hour` | Hour of day (0–23) | 0–23 |
| `location` | Transaction origin | 1=Home, 2=Nearby, 3=International |
| `device` | Device type | 1=Known, 2=Unknown, 3=VPN |
| `is_new` | Account age < 30 days | 0/1 |
| `num_items` | Items in transaction | Integer |
| `payment` | Payment method | 1=Card, 2=NetBanking, 3=UPI, 4=Crypto |

### Training Data
- 8,000 legitimate transactions + 2,000 fraudulent transactions (synthetic, statistically modeled)
- Fraud patterns: high amounts, international location, VPN devices, new accounts, crypto payments
- Train/test split: 80/20 with stratification

---

## 🗂️ Project Structure

```
fraud-detection/
├── app.py              # Flask app — all routes, auth, prediction, batch processing
├── model.py            # Model training script (generates model.pkl)
├── create_admin.py     # One-time admin user seeder
├── requirements.txt
├── model.pkl           # Trained ensemble (auto-generated, git-ignored)
├── fraud.db            # SQLite DB (auto-created, git-ignored)
├── uploads/            # Temp folder for CSV batch uploads
└── templates/
    ├── base.html           # Shared nav layout
    ├── index.html          # Landing / login page
    ├── login.html
    ├── register.html
    ├── dashboard.html      # User stats + recent transactions
    ├── predict.html        # Real-time fraud prediction form
    ├── analytics.html      # CSV batch upload
    ├── model_info.html     # Model metrics + feature list
    ├── admin_dashboard.html # Admin: user management
    └── pending.html        # Awaiting admin approval
```

---

## ⚙️ Setup & Run

```bash
# 1. Clone
git clone https://github.com/lakshmipoorani-05/fraud-detection.git
cd fraud-detection

# 2. Install dependencies
pip install -r requirements.txt

# 3. Train the model (generates model.pkl)
python model.py

# 4. Create admin user
python create_admin.py

# 5. Run
python app.py
```

Open → **http://localhost:5000**

---

## 📁 CSV Batch Upload Format

Upload a `.csv` file with these exact columns:

```
amount,hour,location,device,payment,is_new,num_items
5000,14,1,2,0,1,3
29767,21,3,3,1,1,15
```

The system processes each row through the full hybrid detection pipeline and returns fraud scores for all records.

---

## 🗄️ Database Schema

```
users        — id, username, email, password (hashed), role, status, organization
transactions — id, user_id, amount, hour, location, device, payment, is_new_account,
               num_items, ml_score, rule_boost, final_score, result, timestamp
batch_uploads — id, user_id, filename, total_transactions, fraud_count, status
```

---

## 🛣️ Route Map

| Route | Method | Description |
|---|---|---|
| `/` | GET | Landing page |
| `/register` | GET/POST | User registration |
| `/login` | GET/POST | User login |
| `/dashboard` | GET | User dashboard + stats |
| `/predict` | GET/POST | Real-time fraud prediction |
| `/analytics` | GET/POST | CSV batch upload & analysis |
| `/model-info` | GET | Model performance metrics |
| `/admin` | GET | Admin user management |
| `/api/transactions` | GET | JSON feed of recent transactions |

---

## 📰 Publication

**"AI-Powered Hybrid Machine Learning Based Real-Time E-Commerce Fraud Detection System"**  
International Journal of Engineering Development and Research (IJEDR)  
ISSN: 2321-9939 | Volume 14, Issue 2 | April 2026 | Impact Factor: 9.37  
Paper ID: IJEDR2602373 | Registration ID: 306276

---

## 🛣️ Roadmap

- [x] Hybrid Random Forest + Gradient Boosting ensemble
- [x] Rule-based boost layer for high-risk patterns
- [x] Role-based auth (Admin / User) with approval gate
- [x] CSV batch processing
- [x] Admin dashboard with user management
- [x] Transaction history persistence
- [x] Published research paper
- [ ] Real-time streaming via WebSockets
- [ ] SHAP explainability for per-prediction reasoning
- [ ] Email alerts on high-risk transactions
- [ ] Docker containerization
- [ ] Deploy on Render / Railway

---

## 👩‍💻 Authors

**Lakshmi Poorani S** & **Joy Angelin J**  
B.E. CSE — Francis Xavier Engineering College, Tirunelveli  
Guide: Mrs. N. Rajapriya M.E, (Ph.D), Asst. Professor, Dept. of CSE

[GitHub](https://github.com/lakshmipoorani-05) · [LinkedIn](https://linkedin.com/in/lakshmipoorani)

---

## 📄 License

MIT License — use freely, credit appreciated.
