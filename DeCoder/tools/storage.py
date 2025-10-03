import json
import string
from typing import List

DATA_FILE = "Data.json"

def load_data() -> dict:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def next_code(code: str) -> str:
    letters = string.ascii_uppercase
    code_list = list(code)
    i = len(code_list) - 1
    while i >= 0:
        idx = letters.index(code_list[i])
        if idx < len(letters) - 1:
            code_list[i] = letters[idx + 1]
            break
        else:
            code_list[i] = 'A'
            i -= 1
    return ''.join(code_list)

def assign_codes(users: dict):
    existing_codes = {user.get("code") for user in users.values() if user.get("code")}
    code = 'AAAAA'
    for user_id, user in users.items():
        if not user.get("code"):
            while code in existing_codes:
                code = next_code(code)
            user['code'] = code
            existing_codes.add(code)
            code = next_code(code)

def get_user_ids_by_codes(codes: List[str]) -> List[str]:
    return [uid for uid, udata in users_data.items() if udata.get("code") in codes]

users_data = load_data()
