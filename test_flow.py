import requests

BASE_URL = 'http://127.0.0.1:5000/api'

def check(condition, message):
    if condition:
        print(f"[OK] {message}")
    else:
        print(f"[FAIL] {message}")

print("--- Testing CodeWiz Flow ---")

import random
rand_num = random.randint(1000, 9999)

# 1. Register Walk-in Patient
res = requests.post(f"{BASE_URL}/patient", json={
    "phone": f"555-{rand_num}",
    "name": "Jane Doe",
    "age": 28,
    "gender": "Female"
})
check(res.status_code == 201, "Registered Walk-in Patient")
p1_id = res.json()['id']

# 2. Walk-in Appointment (Minor symptom -> General Doctor)
res = requests.post(f"{BASE_URL}/appointment", json={
    "patient_id": p1_id,
    "symptoms": "Cough, Fever",
    "type": "Walk-in"
})
check(res.status_code == 201, "Created Walk-in Appointment")
appt1 = res.json()['appointment']
check(appt1['priority'] == 'Normal', "Assigned Normal Priority for Minor Symptoms")

rand_num2 = random.randint(1000, 9999)

# 3. Register Online Patient
res = requests.post(f"{BASE_URL}/patient", json={
    "phone": f"555-{rand_num2}",
    "name": "John Smith",
    "age": 45,
    "gender": "Male"
})
check(res.status_code == 201, "Registered Online Patient")
p2_id = res.json()['id']

# 4. Online Appointment (Severe symptom -> Specialist)
res = requests.post(f"{BASE_URL}/appointment", json={
    "patient_id": p2_id,
    "symptoms": "Severe Pain in chest",
    "type": "Online"
})
check(res.status_code == 201, "Created Online Appointment")
appt2 = res.json()['appointment']
check(appt2['priority'] == 'Urgent', "Assigned Urgent Priority for Severe Symptoms")

# 5. Check Queue
res = requests.get(f"{BASE_URL}/queue")
queue = res.json()['queue']
check(len(queue) == 2, f"Queue length is {len(queue)} (expected 2)")

# 6. Issue Prescription (Doctor Dashboard)
res = requests.post(f"{BASE_URL}/prescription", json={
    "appointment_id": appt1['id'],
    "medicines": "Paracetamol 500mg, Cough Syrup"
})
check(res.status_code == 201, "Issued Prescription for Walk-in Patient")
presc = res.json()

# 7. Check Queue again
res = requests.get(f"{BASE_URL}/queue")
queue = res.json()['queue']
# only 1 should be left since first is marked Completed by prescription creation
check(len(queue) == 1, "Queue updated after prescription")

# 8. Order Medicine (Patient Portal)
res = requests.post(f"{BASE_URL}/medicine/order", json={
    "prescription_id": presc['id']
})
check(res.status_code == 200, "Ordered Medicine")
check(res.json()['order_status'] == 'Ordered', 'Order Status is Ordered')

print("--- Testing Complete ---")
