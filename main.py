import requests
import json
import psycopg2

# URL to fetch the JSON file
url = "https://npiregistry.cms.hhs.gov/api/?number=&enumeration_type=&taxonomy_description=&name_purpose=&first_name=&use_first_name_alias=&last_name=&organization_name=&address_purpose=&city=Syracuse&state=&postal_code=&country_code=&limit=200&skip=&pretty=on&version=2.1"

try:
    # Fetching the JSON data
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # Print JSON structure for debugging
    print(json.dumps(data, indent=4))

    # List to store the filtered data
    filtered_data = []

    # Iterating through the results and extracting desired parameters
    for entry in data.get("results", []):  # Ensure 'results' contains the relevant data
        filtered_entry = {
            "authorized_official_first_name": entry.get("basic", {}).get("authorized_official_first_name", "N/A"),
            "authorized_official_last_name": entry.get("basic", {}).get("authorized_official_last_name", "N/A"),
            "telephone_number": entry.get("addresses", [{}])[0].get("telephone_number", "N/A"),
            "description": entry.get("taxonomies", [{}])[0].get("desc", "N/A"),  # Renamed from "desc" to "description"
            "address_1": entry.get("addresses", [{}])[0].get("address_1", "N/A")
        }

        # Ensure all values are strings and remove any list values
        for key, value in filtered_entry.items():
            if isinstance(value, list):  # Convert lists to comma-separated strings
                filtered_entry[key] = ", ".join(map(str, value))
            else:
                filtered_entry[key] = str(value)

        # Check if all values are valid (i.e., not "N/A")
        if all(param != "N/A" for param in filtered_entry.values()):
            filtered_data.append(filtered_entry)

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(
        dbname="Docdb",
        user="postgres",
        password="aicha30200204",
        host="localhost",  # Replace with your partner's IP address OR hostname if needed
        port="5432"
    )
    cursor = conn.cursor()

    # Insert data into the existing table
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

    # Commit the transaction and close the connection
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
