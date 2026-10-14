"""Manage pharmacy stock, patient allergies, and prescriptions."""

import json
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect(":memory:")
stock = {}
prescriptions = []


def setup_database():
    """Create the patient database and insert sample records."""
    with conn:
        conn.execute(
            "CREATE TABLE patients (id TEXT, name TEXT, allergy TEXT)"
        )
        conn.executemany(
            "INSERT INTO patients VALUES (?, ?, ?)",
            [
                ("P1", "Kavya", "penicillin"),
                ("P2", "Arjun", "none"),
                ("P3", "Meena", "ibuprofen"),
            ],
        )


def find_patient(name):
    """Find a patient by name using a parameterized SQL query."""
    cur = conn.cursor()
    query = "SELECT id, allergy FROM patients WHERE name = ?"
    return cur.execute(query, (name,)).fetchall()


def add_stock(drug, units, expiry, batch_log=None):
    """Add drug units to stock and optionally record the batch."""
    if not isinstance(units, int) or isinstance(units, bool) or units <= 0:
        raise ValueError("Units must be a positive integer.")

    datetime.strptime(expiry, "%Y-%m-%d")

    if batch_log is None:
        batch_log = []

    current_units = stock.get(drug, {}).get("units", 0)
    stock[drug] = {
        "units": current_units + units,
        "expiry": expiry,
    }
    batch_log.append((drug, units))
    return len(batch_log)


def dispense(patient_name, drug, units):
    """Dispense medicine only when the patient and stock are valid."""
    if not isinstance(units, int) or isinstance(units, bool) or units <= 0:
        print("Invalid quantity.")
        return False

    patients = find_patient(patient_name)
    if not patients:
        print("Patient not found:", patient_name)
        return False

    patient_id, allergy = patients[0]

    if allergy.lower() != "none" and allergy.lower() in drug.lower():
        print("Allergy warning for", patient_name)
        return False

    if drug not in stock:
        print("Drug not found in stock:", drug)
        return False

    if stock[drug]["units"] < units:
        print("Insufficient stock for", drug)
        return False

    stock[drug]["units"] -= units
    prescriptions.append(
        {
            "patient": patient_id,
            "drug": drug,
            "units": units,
            "time": datetime.now().isoformat(),
        }
    )
    return True


def expiring_soon(days=30):
    """Return drugs expiring within the specified number of days."""
    if not isinstance(days, int) or isinstance(days, bool) or days < 0:
        raise ValueError("Days must be a non-negative integer.")

    today = datetime.now().date()
    cutoff = today + timedelta(days=days)
    soon = []

    for drug, details in stock.items():
        expiry = datetime.strptime(
            details["expiry"], "%Y-%m-%d"
        ).date()
        if today <= expiry <= cutoff:
            soon.append(drug)

    return soon


def export_prescriptions(file="prescriptions.json"):
    """Export prescriptions to a JSON file."""
    with open(file, "w", encoding="utf-8") as output_file:
        json.dump(prescriptions, output_file, indent=4)


def load_stock(file="stock.json"):
    """Load stock from JSON, keeping existing stock if loading fails."""
    try:
        with open(file, "r", encoding="utf-8") as input_file:
            loaded_stock = json.load(input_file)

        if not isinstance(loaded_stock, dict):
            raise ValueError("Stock data must be a JSON object.")

        for drug, details in loaded_stock.items():
            if not isinstance(details, dict):
                raise ValueError(f"Invalid stock entry for {drug}.")
            if not isinstance(details.get("units"), int):
                raise ValueError(f"Invalid units for {drug}.")
            if details["units"] < 0:
                raise ValueError(f"Negative stock for {drug}.")
            datetime.strptime(details["expiry"], "%Y-%m-%d")

        stock.clear()
        stock.update(loaded_stock)

    except FileNotFoundError:
        print("Stock file not found; starting with empty stock.")
    except FileNotFoundError:
        print("Stock file not found; starting with empty stock.")
    except (
        OSError,
        json.JSONDecodeError,
        ValueError,
        TypeError,
        KeyError,
    ) as error:
        print("Unable to load stock:", error)


def print_stock():
    """Display all drugs, quantities, and expiry dates."""
    print("Pharmacy Stock")
    for drug, details in stock.items():
        print(
            f"{drug} -> {details['units']} units, "
            f"expires {details['expiry']}"
        )


def main():
    """Run the pharmacy stock demonstration."""
    setup_database()
    load_stock()

    add_stock("Paracetamol", 100, "2027-03-01")
    add_stock("Amoxicillin", 20, "2025-12-31")
    add_stock("Penicillin", 50, "2027-01-15")
    add_stock("Ibuprofen", 15, "2026-11-30")

    print(
        "Arjun gets Amoxicillin:",
        dispense("Arjun", "Amoxicillin", 30),
    )
    print(
        "Kavya gets Penicillin:",
        dispense("Kavya", "Penicillin", 10),
    )
    print(
        "Meena gets ibuprofen:",
        dispense("Meena", "Ibuprofen", 2),
    )
    print(
        "Unknown patient:",
        dispense("Ghost", "Paracetamol", 5),
    )

    name = input("Patient name to look up (Enter for Arjun): ") or "Arjun"
    print("Lookup result:", find_patient(name))
    print("Expiring within 30 days:", expiring_soon())
    export_prescriptions()
    print_stock()


if __name__ == "__main__":
    main()
