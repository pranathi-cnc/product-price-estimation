# Product Price Estimation Experiment

## Overview

A small experiment that uses **Ollama + Gemma 4** to estimate rough reference prices for Bluetooth speakers from product descriptions.

The project compares Gemma's estimated prices with a simple **average-price baseline** and measures the prediction error using **Mean Absolute Error (MAE)**.

> These are rough estimates for review, not guaranteed market prices.

## Problem Statement

A reseller needs a rough reference price when reviewing new supplier listings.

The system:

* Cleans product descriptions.
* Splits 50 products into training, validation, and test datasets.
* Calculates an average-price baseline from the training data.
* Uses three training examples for few-shot prompting.
* Uses Gemma 4 to estimate prices.
* Calculates absolute error and MAE.
* Saves the final test results to CSV.

## Dataset

The dataset contains **50 Bluetooth speaker products** with:

* Product ID
* Product description
* Price in INR

The data is split into:

* **30 training products**
* **10 validation products**
* **10 test products**

## Project Structure

```text
product-price-estimation/
│
├── data/
│   ├── products.csv
│   ├── cleaned_products.csv
│   ├── train.csv
│   ├── validation.csv
│   └── test.csv
│
├── outputs/
│   └── test_results.csv
│
├── src/
│   └── app.py
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

## Workflow

```text
products.csv
      ↓
Clean descriptions
      ↓
cleaned_products.csv
      ↓
30 Training | 10 Validation | 10 Test
      ↓
Average Training Price
      ↓
Few-shot examples
      ↓
Gemma 4 price estimation
      ↓
Absolute Error
      ↓
MAE
      ↓
test_results.csv
```

## Baseline

The baseline prediction is the **average price of all 30 training products**.

For the current dataset:

```text
Average training price: ₹2889
```

This same value is used as the baseline prediction for validation and test products.

## Few-Shot Prompting

Three training examples are provided to Gemma as reference examples.

The current examples are:

```text
P006 → ₹1699
P016 → ₹2899
P026 → ₹4299
```

The test product's actual price is not provided to Gemma.

## Evaluation

For every prediction:

```text
Absolute Error = |Actual Price - Predicted Price|
```

MAE is calculated as:

```text
MAE = Sum of Absolute Errors / Number of Valid Predictions
```

A lower MAE means the predictions are closer to the actual prices.

## Output

The final report is saved as:

```text
outputs/test_results.csv
```

It contains:

* `product_id`
* `description`
* `actual_price`
* `baseline_prediction`
* `baseline_absolute_error`
* `gemma_prediction`
* `gemma_absolute_error`
* `invalid_output`

## Running the Project

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run:

```powershell
python src\app.py
```

The application automatically creates:

```text
data/cleaned_products.csv
data/train.csv
data/validation.csv
data/test.csv
outputs/test_results.csv
```

## Technology Stack

* Python
* Ollama
* Gemma 4
* Pydantic
* Pandas/CSV
* python-dotenv

## Model Configuration

`.env`:

```text
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:latest
```

## Human Review

The generated price is treated as an **estimate**, not a guaranteed market price.

The actual product price is used only after prediction to calculate the evaluation error.

## Important Result

The project reports both:

* Baseline MAE
* Gemma MAE

This allows us to objectively check whether Gemma performs better than the simple average-price baseline on the test data.
