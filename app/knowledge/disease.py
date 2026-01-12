nutrients = [
    "Protein","Saturated fat","Monounsaturated fat","Omega-3","Omega-6",
    "Trans fat","Sugars","Tinh bột","Chất xơ","Vitamin A","Vitamin C",
    "Vitamin D","Vitamin E","Vitamin K","Vitamin B6","Vitamin B12",
    "Choline","Canxi","Sắt","Magie","Kẽm","Kali","Natri",
    "Phốt pho","Caffeine","Alcohol","Cholesterol"
]

disease_data = {
    "Suy thận": ["Kiêng","Hạn chế","Hạn chế","","","","","","","Bổ sung","","Bổ sung","","","Hạn chế","Hạn chế","","Kiêng","Hạn chế"],
    "Xơ gan, Viêm gan": ["Hạn chế","Hạn chế","Hạn chế","Bổ sung","","","","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","","Bổ sung","Bổ sung","Hạn chế","Hạn chế","","Kiêng","Kiêng"],
    "Gout": ["Kiêng","Hạn chế","Hạn chế"] + [""]*18 + ["Hạn chế","Kiêng","Kiêng"],
    "Sỏi thận": [""]*21 + ["Hạn chế"] + [""]*5,
    "Suy dinh dưỡng": ["Bổ sung"]*24 + ["Hạn chế","Hạn chế","Hạn chế"],
    "Bỏng nặng": ["Bổ sung"] + [""]*7 + ["Bổ sung",""] + ["Bổ sung","Bổ sung"] + [""]*8 + ["Hạn chế","Hạn chế",""],
    "Thiếu máu thiếu sắt": [""]*17 + ["Bổ sung"] + [""]*4 + ["Hạn chế","Hạn chế","Hạn chế"],
    "Bệnh tim mạch": ["Bổ sung","Hạn chế","Hạn chế"] + [""]*10 + ["Hạn chế"] + [""]*5 + ["Hạn chế"] + [""]*2 + ["Kiêng","Kiêng","Kiêng"],
    "Tiểu đường": ["Bổ sung"] + [""]*5 + ["Kiêng","Kiêng"] + [""]*14 + ["Kiêng","Kiêng","Hạn chế"],
    "Loãng xương": ["Bổ sung"] + [""]*21 + ["Hạn chế","Hạn chế","Hạn chế"],
    "Phụ nữ mang thai": ["Bổ sung","","Bổ sung","Bổ sung","Hạn chế","Hạn chế","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung","Bổ sung"] + [""]*2 + ["Kiêng","Kiêng","Hạn chế"],
    "Viêm loét, trào ngược dạ dày": [""]*24 + ["Kiêng","Kiêng",""],
    "Hội chứng ruột kích thích": [""]*7 + ["Hạn chế"] + [""]*15 + ["Kiêng","Kiêng","Hạn chế"],
    "Viêm khớp": ["Hạn chế","Hạn chế","Hạn chế","","","Hạn chế"] + [""]*16 + ["Kiêng","Kiêng","Hạn chế"],
    "Tăng huyết áp": ["","Hạn chế","Hạn chế","","Kiêng","Hạn chế"] + [""]*15 + ["Hạn chế","","Kiêng","Kiêng","Hạn chế"]
}