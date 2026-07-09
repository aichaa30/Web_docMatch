import json
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Path to your JSON file
json_file_path = "/Users/aichagory/Downloads/download.json"

try:
    # Step 1: Load JSON data and count records
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    json_count = len(data.get("results", []))
    print(f" Total records in JSON file: {json_count}")

    # Step 2: Extract and filter the required fields
    filtered_data = []

    for entry in data.get("results", []):
        address_info = entry.get("addresses", [{}])[0]  # Extract address object safely

        filtered_entry = {
            "authorized_official_first_name": entry.get("basic", {}).get("authorized_official_first_name", ""),
            "authorized_official_last_name": entry.get("basic", {}).get("authorized_official_last_name", ""),
            "telephone_number": address_info.get("telephone_number", ""),
            "description": entry.get("taxonomies", [{}])[0].get("desc", ""),
            "address_1": address_info.get("address_1", ""),
            "city": address_info.get("city", ""),
            "state": address_info.get("state", ""),
            "postal_code": address_info.get("postal_code", "")
        }

        for key, value in filtered_entry.items():
            if isinstance(value, list):
                filtered_entry[key] = ", ".join(map(str, value))
            else:
                filtered_entry[key] = str(value)

        if all(filtered_entry[key] for key in filtered_entry):
            filtered_data.append(filtered_entry)

    # Step 3: Connect to PostgreSQL and insert data
    conn = psycopg2.connect(
        dbname="Docdb",
        user="postgres",
        password=os.getenv("LOCAL_DB_PASSWORD"),
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    for entry in filtered_data:
        print(f"Inserting: {entry}")
        cursor.execute("""
            INSERT INTO public."Doctor" 
            (authorized_official_first_name, authorized_official_last_name, telephone_number, description, address_1, city, state, postal_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            entry["authorized_official_first_name"],
            entry["authorized_official_last_name"],
            entry["telephone_number"],
            entry["description"],
            entry["address_1"],
            entry["city"],
            entry["state"],
            entry["postal_code"]
        ))

    conn.commit()

    cursor.execute('SELECT COUNT(*) FROM public."Doctor";')
    db_count = cursor.fetchone()[0]
    print(f"Total records in PostgreSQL table: {db_count}")

    if json_count == db_count:
        print(" All records successfully inserted! ")
    else:
        print(f" Mismatch detected: JSON file has {json_count}, but DB has {db_count}.")

    cursor.close()
    conn.close()

except FileNotFoundError:
    print(f" Error: The file {json_file_path} was not found.")
except json.JSONDecodeError:
    print(" Error: Failed to decode JSON. Check if the file is correctly formatted.")
except psycopg2.Error as e:
    print(f" Database error: {e}")