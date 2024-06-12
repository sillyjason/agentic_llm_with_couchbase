import json

# Read data from the file
with open('dataset/orders.json', 'r') as file:
    data = json.load(file)

# Remove "refund_amount" and "refund_category" fields from each object
for obj in data:
    obj.pop("refund_status", None)
    obj.pop("refund_ticket_id", None)

# Write the modified data back to the file
with open('dataset/orders.json', 'w') as file:
    json.dump(data, file)