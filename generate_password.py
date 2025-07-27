import bcrypt

# Generate a new password hash for 'admin'
password = 'admin'
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

print(f"Password: {password}")
print(f"Hash: {password_hash.decode()}")
print(f"Verification: {bcrypt.checkpw(password.encode(), password_hash)}")
