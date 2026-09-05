"""Email tasdiqlash tokenlari — jadval: `verification_tokens`.

Ustunlar:
    id, user_id (FK), token_hash (unique, sha256 — ochiq token saqlanmaydi),
    type (email_verify | password_reset), expires_at, used_at, created_at
"""

# TODO: class VerificationTokenType(str, enum.Enum): ...
# TODO: class VerificationToken(Base): ...
