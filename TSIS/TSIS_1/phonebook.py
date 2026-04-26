"""
TSIS 1 — Extended PhoneBook
Builds on Practice 7 (CRUD, CSV) and Practice 8 (procedures, pagination).
New features: groups, multiple phones, email, birthday,
JSON import/export, advanced search/filter/sort.
"""

import csv
import json
from datetime import datetime
from connect import open_db_session


# ================================================================
# HELPERS
# ================================================================

def _render_contact(contact_obj):
    """Pretty-print a contact dict."""
    phone_list = contact_obj.get("phones", [])
    phone_text = ", ".join(
        f"{phone_item['phone']} ({phone_item['type']})" for phone_item in phone_list
    ) if phone_list else "—"
    print(f"  ID        : {contact_obj.get('id', '?')}")
    print(f"  Name      : {contact_obj.get('first_name', '')}")
    print(f"  Email     : {contact_obj.get('email') or '—'}")
    print(f"  Birthday  : {contact_obj.get('birthday') or '—'}")
    print(f"  Group     : {contact_obj.get('group_name') or '—'}")
    print(f"  Phones    : {phone_text}")
    print()


def _fetch_phones_for(db_session, owner_contact_id):
    """Return list of {phone, type} for a contact."""
    cur = db_session.cursor()
    cur.execute(
        "SELECT phone, type FROM phones WHERE contact_id = %s",
        (owner_contact_id,),
    )
    phone_records = cur.fetchall()
    cur.close()
    return [{"phone": rec[0], "type": rec[1]} for rec in phone_records]


def _resolve_group_id(db_session, group_label):
    """Return group id, inserting if needed."""
    cur = db_session.cursor()
    cur.execute("SELECT id FROM groups WHERE name = %s", (group_label,))
    matched = cur.fetchone()
    if matched:
        cur.close()
        return matched[0]
    cur.execute(
        "INSERT INTO groups (name) VALUES (%s) RETURNING id",
        (group_label,),
    )
    new_group_id = cur.fetchone()[0]
    db_session.commit()
    cur.close()
    return new_group_id


def _record_to_dict(record_row, cur):
    """Turn a cursor row into a dict using column names."""
    column_titles = [meta[0] for meta in cur.description]
    return dict(zip(column_titles, record_row))


# ================================================================
# 3.3 — IMPORT / EXPORT / OTHERS
# ================================================================

def export_to_json():
    output_filename = "contacts.json"
    db_session = open_db_session()
    cur = db_session.cursor()
    cur.execute(
        "SELECT c.id, c.first_name, c.email, c.birthday::TEXT, g.name "
        "FROM contacts c LEFT JOIN groups g ON g.id = c.group_id"
    )

    exported_records = []
    for row in cur.fetchall():
        exported_records.append({
            "id":         row[0],
            "first_name": row[1],
            "email":      row[2],
            "birthday":   row[3],
            "group":      row[4],
            "phones":     _fetch_phones_for(db_session, row[0]),
        })

    with open(output_filename, "w", encoding="utf-8") as out_file:
        json.dump(exported_records, out_file, indent=2, ensure_ascii=False)
    print(f"✅ Экспортировано в {output_filename}")
    db_session.close()


# ================================================================
# 3.2 — FILTER BY GROUP
# ================================================================

def filter_by_group():
    db_session = open_db_session()
    cur = db_session.cursor()
    cur.execute("SELECT id, name FROM groups ORDER BY name")
    available_groups = cur.fetchall()

    print("  Доступные группы:")
    for group_row in available_groups:
        print(f"    [{group_row[0]}] {group_row[1]}")
    chosen_group_id = input("  Введите ID группы: ").strip()

    cur.execute("""
        SELECT c.id, c.first_name, c.email, c.birthday, g.name AS group_name
        FROM contacts c LEFT JOIN groups g ON g.id = c.group_id
        WHERE c.group_id = %s ORDER BY c.first_name
    """, (chosen_group_id,))
    matched_rows = cur.fetchall()

    if not matched_rows:
        print("  Контакты не найдены.")
        return

    for row in matched_rows:
        contact_obj = {
            "id":         row[0],
            "first_name": row[1],
            "email":      row[2],
            "birthday":   row[3],
            "group_name": row[4],
        }
        side_session = open_db_session()
        contact_obj["phones"] = _fetch_phones_for(side_session, row[0])
        side_session.close()
        _render_contact(contact_obj)
    db_session.close()


# ================================================================
# 3.1 — ADD / UPDATE CONTACT (console)
# ================================================================

def insert_from_console():
    new_name     = input("  Имя          : ").strip()
    new_email    = input("  Email        : ").strip() or None
    new_birthday = input("  Дата рожд. (YYYY-MM-DD, Enter — пропустить): ").strip() or None
    new_group    = input("  Группа (Family/Work/Friend/Other): ").strip() or "Other"

    db_session = open_db_session()
    try:
        target_group_id = _resolve_group_id(db_session, new_group)
        cur = db_session.cursor()
        cur.execute(
            "INSERT INTO contacts (first_name, email, birthday, group_id) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (new_name, new_email, new_birthday, target_group_id),
        )
        new_contact_id = cur.fetchone()[0]

        # Add phones
        while True:
            phone_value = input("  Телефон (Enter — завершить): ").strip()
            if not phone_value:
                break
            phone_kind = input("  Тип (home/work/mobile): ").strip()
            if phone_kind not in ("home", "work", "mobile"):
                phone_kind = "mobile"
            cur.execute(
                "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                (new_contact_id, phone_value, phone_kind),
            )

        db_session.commit()
        print("✅ Контакт добавлен!")
    finally:
        db_session.close()


# ================================================================
# MENU
# ================================================================

def menu():
    while True:
        print("\n--- PhoneBook TSIS 1 ---")
        print("1. Добавить контакт | 2. Фильтр по группе | 3. Экспорт JSON | 0. Выход")
        user_choice = input("Выбор: ")
        if   user_choice == "1": insert_from_console()
        elif user_choice == "2": filter_by_group()
        elif user_choice == "3": export_to_json()
        elif user_choice == "0": break


if __name__ == "__main__":
    menu()
