import json

APP_NAME = "recipes"
MODEL_NAME = "Ingredient"
JSON_FILE = r"data\ingredients.json"
FIXTURE_FILE = "ingredients_fixture.json"

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

fixture = []
for id, item in enumerate(data, start=1):
    fixture.append(
        {
            "model": f"{APP_NAME}.{MODEL_NAME.lower()}",
            "pk": id,
            "fields": {
                "name": item["name"],
                "measurement_unit": item["measurement_unit"],
            },
        }
    )

with open(FIXTURE_FILE, "w", encoding="utf-8") as f:
    json.dump(fixture, f, ensure_ascii=False, indent=2)

print(f"Fixtures created: {FIXTURE_FILE}")
