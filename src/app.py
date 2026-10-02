# import csv
# import os
# import re
# from pathlib import Path

# import ollama
# from dotenv import load_dotenv
# from pydantic import BaseModel, ValidationError, field_validator

# load_dotenv()

# OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
# OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:latest")

# DATA_FILE = Path("data/products.csv")
# OUTPUT_DIR = Path("outputs")

# client = ollama.Client(host=OLLAMA_URL)

# class PricePrediction(BaseModel):
#     price: float

#     @field_validator("price")
#     @classmethod
#     def validate_price(cls, value):
#         if value < 0:
#             raise ValueError("Price cannot be negative.")
#         return value


# def load_products():
#     with open(DATA_FILE, "r", encoding="utf-8") as file:
#         return list(csv.DictReader(file))

# def clean_description(description):
#     description = re.sub(
#         r"(price|cost|mrp|rs\.?|inr)\s*[:\-]?\s*₹?\s*\d+",
#         "",
#         description,
#         flags=re.IGNORECASE,
#     )

#     description = re.sub(r"\s+", " ", description)

#     return description.strip()


# def clean_products(products):
#     cleaned = []

#     for product in products:
#         cleaned.append(
#             {
#                 "product_id": product["product_id"],
#                 "description": clean_description(product["description"]),
#                 "price": float(product["price"]),
#             }
#         )

#     return cleaned
# def split_products(products):
#     train = products[:30]
#     validation = products[30:40]
#     test = products[40:50]

#     return train, validation, test

# def calculate_baseline(train):
#     total = sum(product["price"] for product in train)

#     return total / len(train)

# def select_few_shot_examples(train):
#     return [
#         train[5],
#         train[15],
#         train[25],
#     ]

# def create_prompt(product, examples):
#     examples_text = ""

#     for index, example in enumerate(examples, start=1):
#         examples_text += f"""
# Example {index}:
# Description: {example["description"]}
# Price: {example["price"]}
# """

#     prompt = f"""
# You are estimating the rough reference price of a Bluetooth speaker.

# Use the product descriptions and prices in the examples as reference points.

# {examples_text}

# Now estimate the price for this product:

# Description:
# {product["description"]}

# Return ONLY a JSON object in this format:

# {{"price": 2500}}

# Rules:
# - Return only the JSON object.
# - Price must be a positive number.
# - Do not include currency symbols.
# - Do not include explanations.
# """

#     return prompt

# def predict_price(product, examples):
#     prompt = create_prompt(product, examples)

#     response = client.generate(
#         model=OLLAMA_MODEL,
#         prompt=prompt,
#     )

#     raw_response = response["response"].strip()

#     try:
#         prediction = PricePrediction.model_validate_json(raw_response)

#         return prediction.price, None

#     except (ValidationError, ValueError):
#         match = re.search(
#             r'"price"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
#             raw_response,
#         )

#         if match:
#             try:
#                 price = float(match.group(1))
#                 prediction = PricePrediction(price=price)
#                 return prediction.price, None
#             except ValueError:
#                 pass

#         return None, raw_response

# def evaluate_validation(validation, baseline, examples):
#     baseline_errors = []
#     gemma_errors = []

#     print("\nVALIDATION RESULTS")
#     print("=" * 70)

#     for product in validation:

#         baseline_prediction = baseline

#         gemma_prediction, error = predict_price(
#             product,
#             examples,
#         )

#         baseline_error = abs(
#             product["price"] - baseline_prediction
#         )

#         baseline_errors.append(baseline_error)

#         if gemma_prediction is not None:
#             gemma_error = abs(
#                 product["price"] - gemma_prediction
#             )
#             gemma_errors.append(gemma_error)
#         else:
#             gemma_error = None

#         print(f"\nProduct: {product['product_id']}")
#         print(f"Actual: ₹{product['price']:.2f}")
#         print(f"Baseline: ₹{baseline_prediction:.2f}")

#         if gemma_prediction is not None:
#             print(f"Gemma: ₹{gemma_prediction:.2f}")
#             print(f"Gemma Error: ₹{gemma_error:.2f}")
#         else:
#             print("Gemma: INVALID")

#     baseline_mae = sum(baseline_errors) / len(baseline_errors)

#     if gemma_errors:
#         gemma_mae = sum(gemma_errors) / len(gemma_errors)
#     else:
#         gemma_mae = float("inf")

#     print("\nValidation Average Absolute Error")
#     print(f"Baseline: ₹{baseline_mae:.2f}")
#     print(f"Gemma:    ₹{gemma_mae:.2f}")

#     return gemma_mae

# def run_test(test, baseline, examples):
#     results = []

#     for product in test:

#         baseline_prediction = baseline

#         gemma_prediction, invalid_output = predict_price(
#             product,
#             examples,
#         )

#         baseline_error = abs(
#             product["price"] - baseline_prediction
#         )

#         if gemma_prediction is not None:
#             gemma_error = abs(
#                 product["price"] - gemma_prediction
#             )
#         else:
#             gemma_error = None

#         results.append(
#             {
#                 "product_id": product["product_id"],
#                 "description": product["description"],
#                 "actual_price": product["price"],
#                 "baseline_prediction": baseline_prediction,
#                 "baseline_absolute_error": baseline_error,
#                 "gemma_prediction": gemma_prediction,
#                 "gemma_absolute_error": gemma_error,
#                 "invalid_output": invalid_output or "",
#             }
#         )

#     return results

# def save_results(results):
#     OUTPUT_DIR.mkdir(exist_ok=True)

#     output_file = OUTPUT_DIR / "test_results.csv"

#     with open(
#         output_file,
#         "w",
#         newline="",
#         encoding="utf-8",
#     ) as file:

#         writer = csv.DictWriter(
#             file,
#             fieldnames=results[0].keys(),
#         )

#         writer.writeheader()
#         writer.writerows(results)

#     return output_file


# # --------------------------------------------------
# # Main
# # --------------------------------------------------

# def main():

#     print("Loading products...")

#     products = load_products()

#     print(f"Total products: {len(products)}")

#     products = clean_products(products)

#     train, validation, test = split_products(products)

#     print(f"Training products:   {len(train)}")
#     print(f"Validation products: {len(validation)}")
#     print(f"Test products:       {len(test)}")

#     baseline = calculate_baseline(train)

#     print(f"\nAverage training price: ₹{baseline:.2f}")

#     examples = select_few_shot_examples(train)

#     print("\nFew-shot examples:")
#     for example in examples:
#         print(
#             f"- {example['product_id']}: "
#             f"₹{example['price']:.2f}"
#         )

#     # Validation
#     evaluate_validation(
#         validation,
#         baseline,
#         examples,
#     )

#     # Final test
#     print("\n" + "=" * 70)
#     print("FINAL TEST")
#     print("=" * 70)

#     results = run_test(
#         test,
#         baseline,
#         examples,
#     )

#     output_file = save_results(results)

#     # Calculate final metrics
#     baseline_errors = [
#         result["baseline_absolute_error"]
#         for result in results
#     ]

#     gemma_errors = [
#         result["gemma_absolute_error"]
#         for result in results
#         if result["gemma_absolute_error"] is not None
#     ]

#     baseline_mae = sum(baseline_errors) / len(baseline_errors)

#     if gemma_errors:
#         gemma_mae = sum(gemma_errors) / len(gemma_errors)
#     else:
#         gemma_mae = None

#     invalid_count = sum(
#         1
#         for result in results
#         if result["gemma_prediction"] is None
#     )

#     print(f"\nBaseline MAE: ₹{baseline_mae:.2f}")

#     if gemma_mae is not None:
#         print(f"Gemma MAE:    ₹{gemma_mae:.2f}")
#     else:
#         print("Gemma MAE:    No valid predictions")

#     print(f"Invalid Gemma predictions: {invalid_count}")

#     print(f"\nResults saved to: {output_file}")


# if __name__ == "__main__":
#     main()



import csv
import os
import re
from pathlib import Path

import ollama
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, field_validator


load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:latest")

DATA_FILE = Path("data/products.csv")
OUTPUT_DIR = Path("outputs")
DATA_DIR = Path("data")

client = ollama.Client(host=OLLAMA_URL)


class PricePrediction(BaseModel):

    price: float

    @field_validator("price")
    @classmethod
    def validate_price(cls, value):
        if value < 0:
            raise ValueError("Price cannot be negative.")
        return value


def load_products():

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def clean_description(description):

    description = re.sub(
        r"(price|cost|mrp|rs\.?|inr)\s*[:\-]?\s*₹?\s*\d+",
        "",
        description,
        flags=re.IGNORECASE,
    )

    description = re.sub(r"\s+", " ", description)

    return description.strip()


def clean_products(products):

    cleaned = []

    for product in products:

        cleaned.append(
            {
                "product_id": product["product_id"],
                "description": clean_description(
                    product["description"]
                ),
                "price": float(product["price"]),
            }
        )

    return cleaned


def split_products(products):

    train = products[:30]

    validation = products[30:40]

    test = products[40:50]

    return train, validation, test


# --------------------------------------------------
# Save cleaned data and three separate datasets
# --------------------------------------------------

def save_datasets(cleaned, train, validation, test):

    DATA_DIR.mkdir(exist_ok=True)

    fieldnames = [
        "product_id",
        "description",
        "price",
    ]

    # Cleaned complete dataset
    with open(
        DATA_DIR / "cleaned_products.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(cleaned)

    # Training dataset
    with open(
        DATA_DIR / "train.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(train)

    # Validation dataset
    with open(
        DATA_DIR / "validation.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(validation)

    # Test dataset
    with open(
        DATA_DIR / "test.csv",
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(test)

    print("\nDatasets saved:")
    print("data/cleaned_products.csv")
    print("data/train.csv")
    print("data/validation.csv")
    print("data/test.csv")


def calculate_baseline(train):

    total = sum(
        product["price"]
        for product in train
    )

    return total / len(train)


def select_few_shot_examples(train):

    return [
        train[5],
        train[15],
        train[25],
    ]


def create_prompt(product, examples):

    examples_text = ""

    for index, example in enumerate(
        examples,
        start=1,
    ):

        examples_text += f"""
Example {index}:

Description: {example["description"]}

Price: {example["price"]}

"""

    prompt = f"""
You are estimating the rough reference price of a Bluetooth speaker.

Use the product descriptions and prices in the examples as reference points.

{examples_text}

Now estimate the price for this product:

Description:

{product["description"]}

Return ONLY a JSON object in this format:

{{"price": 2500}}

Rules:

- Return only the JSON object.
- Price must be a positive number.
- Do not include currency symbols.
- Do not include explanations.
"""

    return prompt


def predict_price(product, examples):

    prompt = create_prompt(
        product,
        examples,
    )

    response = client.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
    )

    raw_response = response["response"].strip()

    try:

        prediction = PricePrediction.model_validate_json(
            raw_response
        )

        return prediction.price, None

    except (
        ValidationError,
        ValueError,
    ):

        match = re.search(
            r'"price"\s*:\s*([0-9]+(?:\.[0-9]+)?)',
            raw_response,
        )

        if match:

            try:

                price = float(
                    match.group(1)
                )

                prediction = PricePrediction(
                    price=price
                )

                return prediction.price, None

            except ValueError:

                pass

        return None, raw_response


def evaluate_validation(
    validation,
    baseline,
    examples,
):

    baseline_errors = []

    gemma_errors = []

    print("\nVALIDATION RESULTS")

    print("=" * 70)

    for product in validation:

        baseline_prediction = baseline

        gemma_prediction, error = predict_price(
            product,
            examples,
        )

        baseline_error = abs(
            product["price"]
            - baseline_prediction
        )

        baseline_errors.append(
            baseline_error
        )

        if gemma_prediction is not None:

            gemma_error = abs(
                product["price"]
                - gemma_prediction
            )

            gemma_errors.append(
                gemma_error
            )

        else:

            gemma_error = None

        print(
            f"\nProduct: {product['product_id']}"
        )

        print(
            f"Actual: ₹{product['price']:.2f}"
        )

        print(
            f"Baseline: ₹{baseline_prediction:.2f}"
        )

        if gemma_prediction is not None:

            print(
                f"Gemma: ₹{gemma_prediction:.2f}"
            )

            print(
                f"Gemma Error: ₹{gemma_error:.2f}"
            )

        else:

            print("Gemma: INVALID")

    baseline_mae = (
        sum(baseline_errors)
        / len(baseline_errors)
    )

    if gemma_errors:

        gemma_mae = (
            sum(gemma_errors)
            / len(gemma_errors)
        )

    else:

        gemma_mae = float("inf")

    print(
        "\nValidation Average Absolute Error"
    )

    print(
        f"Baseline: ₹{baseline_mae:.2f}"
    )

    print(
        f"Gemma:    ₹{gemma_mae:.2f}"
    )

    return gemma_mae


def run_test(
    test,
    baseline,
    examples,
):

    results = []

    for product in test:

        baseline_prediction = baseline

        gemma_prediction, invalid_output = (
            predict_price(
                product,
                examples,
            )
        )

        baseline_error = abs(
            product["price"]
            - baseline_prediction
        )

        if gemma_prediction is not None:

            gemma_error = abs(
                product["price"]
                - gemma_prediction
            )

        else:

            gemma_error = None

        results.append(
            {
                "product_id": product["product_id"],
                "description": product["description"],
                "actual_price": product["price"],
                "baseline_prediction": baseline_prediction,
                "baseline_absolute_error": baseline_error,
                "gemma_prediction": gemma_prediction,
                "gemma_absolute_error": gemma_error,
                "invalid_output": invalid_output or "",
            }
        )

    return results


def save_results(results):

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    output_file = (
        OUTPUT_DIR
        / "test_results.csv"
    )

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys(),
        )

        writer.writeheader()

        writer.writerows(results)

    return output_file


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():

    print("Loading products...")

    products = load_products()

    print(
        f"Total products: {len(products)}"
    )

    products = clean_products(
        products
    )

    train, validation, test = (
        split_products(products)
    )

    # Save all required datasets
    save_datasets(
        products,
        train,
        validation,
        test,
    )

    print(
        f"Training products:   {len(train)}"
    )

    print(
        f"Validation products: {len(validation)}"
    )

    print(
        f"Test products:       {len(test)}"
    )

    baseline = calculate_baseline(
        train
    )

    print(
        f"\nAverage training price: "
        f"₹{baseline:.2f}"
    )

    examples = select_few_shot_examples(
        train
    )

    print("\nFew-shot examples:")

    for example in examples:

        print(
            f"- {example['product_id']}: "
            f"₹{example['price']:.2f}"
        )

    # Validation
    evaluate_validation(
        validation,
        baseline,
        examples,
    )

    # Final test
    print(
        "\n" + "=" * 70
    )

    print("FINAL TEST")

    print("=" * 70)

    results = run_test(
        test,
        baseline,
        examples,
    )

    output_file = save_results(
        results
    )

    # Calculate final metrics
    baseline_errors = [
        result[
            "baseline_absolute_error"
        ]
        for result in results
    ]

    gemma_errors = [
        result[
            "gemma_absolute_error"
        ]
        for result in results
        if result[
            "gemma_absolute_error"
        ] is not None
    ]

    baseline_mae = (
        sum(baseline_errors)
        / len(baseline_errors)
    )

    if gemma_errors:

        gemma_mae = (
            sum(gemma_errors)
            / len(gemma_errors)
        )

    else:

        gemma_mae = None

    invalid_count = sum(
        1
        for result in results
        if result[
            "gemma_prediction"
        ] is None
    )

    print(
        f"\nBaseline MAE: "
        f"₹{baseline_mae:.2f}"
    )

    if gemma_mae is not None:

        print(
            f"Gemma MAE:    "
            f"₹{gemma_mae:.2f}"
        )

    else:

        print(
            "Gemma MAE:    "
            "No valid predictions"
        )

    print(
        f"Invalid Gemma predictions: "
        f"{invalid_count}"
    )

    print(
        f"\nResults saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":
    main()
