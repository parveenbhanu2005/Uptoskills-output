# Real-Time Credit Card Fraud & Anomaly Detection

## AI-Based Financial Transaction Safeguard System

An AI-based real-time financial transaction monitoring system designed to detect high-risk fraudulent transactions using anomaly detection, behavioral features, and graph neural networks.

---

## Objective

Detect high-risk fraudulent financial transactions in real time using sequence and behavioral models.

---

## Core Requirements

The system implements the following requirements:

1. Detect unusual transaction amounts, geographic velocity spikes, and unknown merchant interactions.
2. Track user spending history patterns across continuous temporal windows.
3. Analyze transaction risk scores using autoencoders and graph neural networks.
4. Generate instant transaction hold flags for fraud prevention teams.
5. Store flagged transaction feature vectors for investigation.
6. Maintain daily fraud loss prevention metrics.

---

## Expected Outputs

The system generates:

1. Real-time alert payload with fraud probability score.
2. Feature breakdown visualization showing risk indicators.
3. CSV report listing flagged transaction IDs, risk scores, and decision triggers.

---

## System Workflow

Transaction Stream

↓

Feature Engineering

↓

User Spending History

↓

Geographic Velocity Detection

↓

Unknown Merchant Detection

↓

Unusual Amount Detection

↓

Autoencoder Anomaly Detection

+

Graph Neural Network Risk Analysis

↓

Fraud Probability

↓

Transaction Hold Decision

↓

Fraud Alert

↓

JSON Alert + Feature Visualization + CSV Report

---

## Technologies Used

- Python
- PyTorch
- PyTorch Geometric
- Pandas
- NumPy
- Scikit-learn
- Matplotlib
- SQLite

---

## Machine Learning Models

### Autoencoder

The Autoencoder analyzes transaction feature vectors and calculates reconstruction error.

A higher reconstruction error indicates that a transaction differs from learned normal transaction patterns.

### Graph Neural Network

The GNN analyzes transaction relationships represented as a graph and produces a transaction risk score.

### Combined Fraud Probability

The system combines anomaly and GNN risk scores:

Fraud Probability =

0.6 × Autoencoder Anomaly Score

+

0.4 × GNN Risk Score

---

## Fraud Detection Features

The system analyzes:

- Transaction amount
- Average user spending
- Geographic transaction velocity
- Unknown merchant interaction
- Unusual transaction amount
- Geographic velocity spike

---

## Transaction Hold Mechanism

A transaction is held when the calculated fraud probability reaches the configured threshold.

Current threshold:

```text
0.75