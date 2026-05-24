from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage, default_storage


class InterviewStorageService:
    @classmethod
    def get_storage(cls):
        if getattr(settings, 'ALLOW_S3', False):
            return default_storage
        media_root = Path(settings.MEDIA_ROOT)
        media_root.mkdir(parents=True, exist_ok=True)
        return FileSystemStorage(location=str(media_root))

    @classmethod
    def save_bytes(cls, rel_path: str, data: bytes) -> str:
        storage = cls.get_storage()
        return storage.save(rel_path, ContentFile(data))

    @classmethod
    def save_upload(cls, rel_path: str, uploaded_file) -> str:
        storage = cls.get_storage()
        return storage.save(rel_path, uploaded_file)

    @classmethod
    def open_path(cls, rel_path: str):
        storage = cls.get_storage()
        return storage.open(rel_path, 'rb')
