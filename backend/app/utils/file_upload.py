"""
File Upload Utility

Handles secure file uploads for product images and user avatars.
"""
import os
import uuid
import hashlib
from typing import Optional
from datetime import datetime

from flask import current_app
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class FileUploadError(Exception):
    """Raised when a file upload fails validation or processing."""
    pass


class FileUploadService:
    """
    Handles file uploads with validation, secure naming, and storage.

    Validates file extensions, MIME types, and file sizes before saving.
    Generates unique filenames to prevent collisions and path traversal.
    """

    # Mapping of upload types to their allowed extensions and max sizes
    UPLOAD_CONFIGS = {
        "product_image": {
            "extensions": {"png", "jpg", "jpeg", "webp", "gif"},
            "max_size_mb": 10,
            "subdirectory": "products",
        },
        "avatar": {
            "extensions": {"png", "jpg", "jpeg", "webp"},
            "max_size_mb": 5,
            "subdirectory": "avatars",
        },
        "warranty_document": {
            "extensions": {"pdf", "png", "jpg", "jpeg"},
            "max_size_mb": 15,
            "subdirectory": "warranties",
        },
    }

    # MIME type to extension mapping for validation
    MIME_MAP = {
        "image/jpeg": {"jpg", "jpeg"},
        "image/png": {"png"},
        "image/webp": {"webp"},
        "image/gif": {"gif"},
        "application/pdf": {"pdf"},
    }

    @staticmethod
    def validate_file(
        file: FileStorage,
        upload_type: str = "product_image",
    ) -> str:
        """
        Validate an uploaded file.

        Args:
            file: The uploaded file from the request.
            upload_type: One of the keys in UPLOAD_CONFIGS.

        Returns:
            The validated (lowercased) file extension.

        Raises:
            FileUploadError: If validation fails.
        """
        if not file or not file.filename:
            raise FileUploadError("No file provided.")

        config = FileUploadService.UPLOAD_CONFIGS.get(upload_type)
        if not config:
            raise FileUploadError(f"Unknown upload type: {upload_type}")

        # Check extension
        filename = secure_filename(file.filename)
        if "." not in filename:
            raise FileUploadError("File has no extension.")

        ext = filename.rsplit(".", 1)[1].lower()
        if ext not in config["extensions"]:
            allowed = ", ".join(sorted(config["extensions"]))
            raise FileUploadError(
                f"File type '.{ext}' is not allowed. Allowed types: {allowed}"
            )

        # Check MIME type consistency
        if file.content_type:
            allowed_exts = FileUploadService.MIME_MAP.get(file.content_type)
            if allowed_exts and ext not in allowed_exts:
                raise FileUploadError(
                    f"File extension '.{ext}' does not match content type '{file.content_type}'."
                )

        # Check file size (read content to get size, then seek back)
        file.seek(0, os.SEEK_END)
        size_bytes = file.tell()
        file.seek(0)

        max_bytes = config["max_size_mb"] * 1024 * 1024
        if size_bytes > max_bytes:
            raise FileUploadError(
                f"File size ({size_bytes / 1024 / 1024:.1f} MB) exceeds "
                f"maximum allowed ({config['max_size_mb']} MB)."
            )

        if size_bytes == 0:
            raise FileUploadError("Uploaded file is empty.")

        return ext

    @staticmethod
    def generate_filename(original_filename: str, prefix: Optional[str] = None) -> str:
        """
        Generate a unique, safe filename.

        Combines a UUID with a hash of the original filename to prevent
        collisions while keeping some traceability.

        Args:
            original_filename: The original uploaded filename.
            prefix: Optional prefix (e.g., product ID).

        Returns:
            A unique filename like "prod-42_a1b2c3d4_5e6f7890.jpg".
        """
        ext = original_filename.rsplit(".", 1)[-1].lower() if "." in original_filename else "bin"
        name_hash = hashlib.md5(original_filename.encode()).hexdigest()[:8]
        unique_id = uuid.uuid4().hex[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d")

        parts = []
        if prefix:
            parts.append(str(prefix))
        parts.append(f"{timestamp}_{name_hash}_{unique_id}")

        return f"{'_'.join(parts)}.{ext}"

    @staticmethod
    def save_file(
        file: FileStorage,
        upload_type: str = "product_image",
        prefix: Optional[str] = None,
    ) -> dict:
        """
        Validate and save an uploaded file to disk.

        Args:
            file: The uploaded file.
            upload_type: Type of upload (determines directory and rules).
            prefix: Optional filename prefix.

        Returns:
            Dictionary with 'filename', 'filepath', 'url', 'size_bytes'.

        Raises:
            FileUploadError: If the file fails validation or cannot be saved.
        """
        ext = FileUploadService.validate_file(file, upload_type)

        config = FileUploadService.UPLOAD_CONFIGS[upload_type]
        upload_root = current_app.config.get(
            "UPLOAD_FOLDER",
            os.path.join(current_app.root_path, "..", "uploads"),
        )
        upload_dir = os.path.join(upload_root, config["subdirectory"])
        os.makedirs(upload_dir, exist_ok=True)

        filename = FileUploadService.generate_filename(file.filename, prefix)
        filepath = os.path.join(upload_dir, filename)

        file.seek(0)
        file.save(filepath)

        # Get saved file size
        size_bytes = os.path.getsize(filepath)

        # Build a relative URL path
        url = f"/uploads/{config['subdirectory']}/{filename}"

        return {
            "filename": filename,
            "filepath": filepath,
            "url": url,
            "size_bytes": size_bytes,
            "content_type": file.content_type,
        }

    @staticmethod
    def delete_file(filepath: str) -> bool:
        """
        Delete an uploaded file from disk.

        Args:
            filepath: Full path to the file.

        Returns:
            True if deleted, False if file did not exist.
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except OSError as e:
            current_app.logger.error(f"Failed to delete file {filepath}: {e}")
            return False
