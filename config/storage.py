import os
import cloudinary.uploader
from cloudinary_storage.storage import RawMediaCloudinaryStorage


class PrivateMediaCloudinaryStorage(RawMediaCloudinaryStorage):
    """
    Custom storage class that forces all media files to be uploaded to Cloudinary
    with type="authenticated" so they are not publicly accessible via predictable URLs.
    """
    def _upload(self, name, content):
        options = {'type': 'authenticated', 'resource_type': 'raw'}
        
        # Passing the file-like object directly instead of raw bytes
        response = cloudinary.uploader.upload(
            content,
            public_id=name,
            **options
        )
        return response.get('public_id') or response.get('version')

