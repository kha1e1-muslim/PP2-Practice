from datetime import datetime, timedelta

today = datetime.now()
new_date = today - timedelta(days=5)

print("Current date:", today)
print("5 days ago:", new_date)