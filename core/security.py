from passlib.context import CryptContext

# Create a password context with the default hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def hash_password(password: str) -> str:
    """
    Hash a password using the default hashing algorithm.
    """
    return pwd_context.hash(password)