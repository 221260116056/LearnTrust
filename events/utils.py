import hashlib
import secrets
from django.conf import settings
from .models import ImmutableLog


def create_log(user, module, event_type, metadata):
    """
    Create an immutable log entry with generated token hash.
    """
    # Generate unique token hash using user_id, module_id, event_type, random nonce, and SECRET_KEY
    nonce = secrets.token_hex(16)
    hash_input = f"{user.id}{module.id if module else ''}{event_type}{nonce}{settings.SECRET_KEY}"
    token_hash = hashlib.sha256(hash_input.encode()).hexdigest()
    
    # Create log entry (save method will generate current_hash)
    log = ImmutableLog.objects.create(
        user=user,
        module=module,
        event_type=event_type,
        metadata=metadata,
        token_hash=token_hash
    )
    
    return log
