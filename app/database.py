from functools import lru_cache

from supabase import Client, create_client

from .config import settings


@lru_cache(maxsize=1)
def get_supabase() -> Client | None:
    """Return a Supabase client, or None when not configured.

    Lazy so the app can boot (and serve / and /health) even when the
    environment variables are missing.
    """
    if not settings.supabase_url or not settings.supabase_key:
        return None

    return create_client(
        settings.supabase_url,
        settings.supabase_key,
    )
