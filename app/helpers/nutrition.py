from app.knowledge.disease import disease_data, nutrients

def get_restrictions(disease: str):
    result = {"Kiêng": [], "Hạn chế": [], "Bổ sung": []}
    if disease not in disease_data:
        return result

    values = disease_data[disease]

    for nutrient, action in zip(nutrients, values):
        if action in result:
            result[action].append(nutrient)

    return result
