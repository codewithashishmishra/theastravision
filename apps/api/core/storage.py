from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage

from core.gcm_crypto import ALGORITHM, is_gcm_blob, unwrap_blob_at_rest, wrap_blob_at_rest


class ScreenshotDecryptError(Exception):
    """Raised when stored screenshot cannot be decrypted for HR viewing."""


class MissingSessionKeyError(ScreenshotDecryptError):
    pass


def _assert_jpeg(data: bytes) -> bytes:
    if len(data) < 3 or data[0:3] != b"\xff\xd8\xff":
        raise ScreenshotDecryptError("Decrypted data is not a valid JPEG image")
    return data


class TrackerStorageService:
    """Store GCM-encrypted tracker blobs; at-rest wrap uses server master key."""

    @staticmethod
    def _base_path(tenant_id, employee_id, session_id):
        return f"tracker/{tenant_id}/{employee_id}/{session_id}"

    @classmethod
    def get_storage(cls):
        if getattr(settings, "ALLOW_S3", False):
            return default_storage
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        return FileSystemStorage(location=str(media_root))

    @classmethod
    def save_gcm_screenshot(cls, tenant_id, employee_id, session_id, gcm_blob: bytes, checksum):
        """Persist client GCM blob with optional master-key wrap at rest."""
        aad = f"store:{session_id}:{checksum}".encode("utf-8")
        if is_gcm_blob(gcm_blob):
            at_rest = wrap_blob_at_rest(gcm_blob, aad)
        else:
            at_rest = gcm_blob
        rel_path = f"{cls._base_path(tenant_id, employee_id, session_id)}/{checksum}.{ALGORITHM}.bin"
        storage = cls.get_storage()
        return storage.save(rel_path, ContentFile(at_rest))

    @classmethod
    def read_screenshot_plaintext(cls, storage_key: str, session, checksum: str, monitor: int) -> bytes:
        from core.gcm_crypto import unwrap_data_key

        storage = cls.get_storage()
        with storage.open(storage_key, "rb") as f:
            header = f.read(32)
        if is_gcm_blob(header) and not session.encryption_key_wrapped:
            raise MissingSessionKeyError(
                "Session encryption key is missing; cannot decrypt GCM screenshot"
            )
        if not session.encryption_key_wrapped:
            return _assert_jpeg(cls._read_legacy(storage_key))
        data_key = unwrap_data_key(session.encryption_key_wrapped)
        return _assert_jpeg(
            cls.read_screenshot_plaintext_with_key(
                storage_key, data_key, str(session.id), checksum, monitor
            )
        )

    @classmethod
    def read_screenshot_plaintext_with_key(
        cls, storage_key: str, data_key: bytes, session_id: str, checksum: str, monitor: int
    ) -> bytes:
        from core.gcm_crypto import decrypt_blob, screenshot_aad, unwrap_blob_at_rest

        storage = cls.get_storage()
        with storage.open(storage_key, "rb") as f:
            at_rest = f.read()
        aad_store = f"store:{session_id}:{checksum}".encode("utf-8")
        try:
            gcm_blob = unwrap_blob_at_rest(at_rest, aad_store)
        except Exception:
            gcm_blob = at_rest
        aad_shot = screenshot_aad(session_id, checksum, monitor)
        try:
            return decrypt_blob(data_key, gcm_blob, aad_shot)
        except Exception as exc:
            raise ScreenshotDecryptError("GCM decryption failed") from exc

    @classmethod
    def _read_legacy(cls, storage_key: str) -> bytes:
        """Fernet-encrypted screenshots from before GCM migration."""
        import base64

        from cryptography.fernet import Fernet
        from django.conf import settings

        storage = cls.get_storage()
        with storage.open(storage_key, "rb") as f:
            blob = f.read()
        key = getattr(settings, "TRACKER_ENCRYPTION_KEY", "") or settings.SECRET_KEY
        if isinstance(key, str):
            key = key.encode()
        fernet_key = base64.urlsafe_b64encode(__import__("hashlib").sha256(key).digest())
        return Fernet(fernet_key).decrypt(blob)

    @classmethod
    def delete_file(cls, storage_key):
        storage = cls.get_storage()
        if storage.exists(storage_key):
            storage.delete(storage_key)
