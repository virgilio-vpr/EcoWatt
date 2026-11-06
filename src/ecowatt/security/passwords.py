from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Argon2id RFC 9106 low-memory: calibrar no host antes de produção.
hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


def verify(encoded: str, password: str) -> bool:
    try:
        return hasher.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False
