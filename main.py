import requests
import json
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# URL to fetch the JSON file
url = "https://npiregistry.cms.hhs.gov/api/?number=&enumeration_type=&taxonomy_description=&name_purpose=&first_name=&use_first_name_alias=&last_name=&organization_name=&address_purpose=&city=Syracuse&state=&postal_code=&country_code=&limit=200&skip=&pretty=on&version=2.1"

try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    print(json.dumps(data, indent=4))

    filtered_data = []

    for entry in data.get("results", []):
        filtered_entry = {
            "authorized_official_first_name": entry.get("basic", {}).get("authorized_official_first_name", "N/A"),
            "authorized_official_last_name": entry.get("basic", {}).get("authorized_official_last_name", "N/A"),
            "telephone_number": entry.get("addresses", [{}])[0].get("telephone_number", "N/A"),
            "description": entry.get("taxonomies", [{}])[0].get("desc", "N/A"),
            "address_1": entry.get("addresses", [{}])[0].get("address_1", "N/A")
        }

        for key, value in filtered_entry.items():
            if isinstance(value, list):
                filtered_entry[key] = ", ".join(map(str, value))
            else:
                filtered_entry[key] = str(value)

        if all(param != "N/A" for param in filtered_entry.values()):
            filtered_data.append(filtered_entry)

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname="Docdb",
        user="postgres",
        password=os.getenv("LOCAL_DB_PASSWORD"),
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()

    for entry in filtered_data:
        cursor.execute("""
            INSERT INTO public."Doctor" 
            (authorized_official_first_name, authorized_official_last_name, telephone_number, description, address_1)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            entry["authorized_official_first_name"],
            entry["authorized_official_last_name"],
            entry["telephone_number"],
            entry["description"],
            entry["address_1"]
        ))

    conn.commit()
    cursor.close()
    conn.close()

    print("Data has been successfully inserted into the database.")

except requests.exceptions.RequestException as e:
    print(f"An error occurred during the HTTP request: {e}")
except json.JSONDecodeError:
    print("Failed to decode JSON from the response.")
except psycopg2.Error as e:
    print(f"An error occurred with the database: {e}")