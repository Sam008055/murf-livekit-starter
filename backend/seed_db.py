import src.db as db

def seed():
    phone = "+919035128088"
    print(f"Seeding profile for {phone}...")
    result = db.update_farmer_profile(
        phone,
        name='Ravi Kumar',
        facts_update={'crop': 'wheat', 'district': 'Karnal'}
    )
    print("Seeded successfully:", result)

if __name__ == "__main__":
    seed()
