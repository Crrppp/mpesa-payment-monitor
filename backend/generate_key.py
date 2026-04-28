from cryptography.fernet import Fernet

key = Fernet.generate_key()
print("\n" + "="*50)
print("🔐 YOUR FERNET KEY (Copy this to .env file):")
print("="*50)
print(f"FERNET_KEY={key.decode()}")
print("="*50)
print("\nAdd this to your .env file in the project root.")