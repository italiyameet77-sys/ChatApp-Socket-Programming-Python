import bcrypt


FORMAT = "utf-8"
password = "1234"
hashed = bcrypt.hashpw(password.encode(FORMAT), bcrypt.gensalt())
print("Hashed password:", hashed)