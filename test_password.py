import bcrypt

# Test different passwords
test_passwords = ['admin', 'password', '123456', 'test']

# The hash from config.py
password_hash = b'$2b$12$ZCgWXzUdmVX.PnIfj4oeJOkX69Tu1rVZ51zGYe3kSloANnwMaTlBW'

print("Testing passwords against hash...")
for password in test_passwords:
    if bcrypt.checkpw(password.encode(), password_hash):
        print(f"✅ Password found: '{password}'")
        break
else:
    print("❌ No password matched")
    print("Available passwords tested:", test_passwords)
