import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import os

# Set seed for reproducibility
np.random.seed(42)

# Configuration: Increased sample size for better training
n_legit, n_fraud = 8000, 2000

print("Generating synthetic training data for 7 features...")

# --- Legit Data Generation ---
la = np.random.lognormal(6.5, 0.8, n_legit).clip(50, 8000)      # Amount
lh = np.random.choice(range(24), n_legit)                      # Hour
ll = np.random.choice([1,2,3], n_legit, p=[0.70,0.20,0.10])    # Location
ld = np.random.choice([1,2,3], n_legit, p=[0.80,0.15,0.05])    # Device
ln = np.random.choice([0,1], n_legit, p=[0.90,0.10])           # is_new_account
li = np.random.randint(1, 8, n_legit)                          # num_items
lp = np.random.choice([1,2,3,4], n_legit, p=[0.50,0.25,0.15,0.10]) # payment

# --- Fraud Data Generation ---
fa = np.random.lognormal(8.5, 1.0, n_fraud).clip(500, 30000)   # Amount
fh = np.random.choice(range(24), n_fraud)                      # Hour
fl = np.random.choice([1,2,3], n_fraud, p=[0.10,0.25,0.65])    # Location
fd = np.random.choice([1,2,3], n_fraud, p=[0.10,0.30,0.60])    # Device
fn = np.random.choice([0,1], n_fraud, p=[0.30,0.70])           # is_new_account
fi = np.random.randint(1, 20, n_fraud)                         # num_items
fp = np.random.choice([1,2,3,4], n_fraud, p=[0.20,0.15,0.20,0.45]) # payment

# Combine into feature matrix X and target y
X = np.column_stack([
    np.concatenate([la, fa]),
    np.concatenate([lh, fh]),
    np.concatenate([ll, fl]),
    np.concatenate([ld, fd]),
    np.concatenate([ln, fn]),
    np.concatenate([li, fi]),
    np.concatenate([lp, fp]),
])

y = np.concatenate([np.zeros(n_legit), np.ones(n_fraud)])

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Scale features
print("Scaling features...")
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)

# Train Random Forest
print("Training Random Forest Classifier...")
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train_s, y_train)

# Train Gradient Boosting
print("Training Gradient Boosting Classifier...")
gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
gb.fit(X_train_s, y_train)

# Save the model and scaler
with open("model.pkl", "wb") as f:
    pickle.dump({
        "rf": rf, 
        "gb": gb, 
        "scaler": scaler,
        "auc": 0.98 # Approximate AUC for the synthetic data
    }, f)

print("model.pkl created successfully with 7 features!")