import csv

def save_csv_report(results: list[dict], filename: str = "change_password_report.csv"):
    fieldnames = [
        "IP",
        "MODEL",
        "VENDOR",
        "PING",
        "AUTH_LOGIN",
        "PASSWORD_CHANGED",
        "NEW_ADMIN_LOGIN",
        "STATUS",
    ]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(results)
