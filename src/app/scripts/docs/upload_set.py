import posixpath
import os
from flask_uploads import UploadSet as _UploadSet, TEXT
from flask_uploads import extension
from werkzeug.datastructures import FileStorage
from app.scripts.docs.get_md5 import get_md5


class UploadSet(_UploadSet):
    def detect_ext(self, basename):
        return self.extension_allowed(extension(basename))

    def save(self, storage, folder=None, name=None):
        if not isinstance(storage, FileStorage):
            raise TypeError("storage must be a werkzeug.FileStorage")

        if folder is None and name is not None and "/" in name:
            folder, name = os.path.split(name)

        basename = storage.filename
        if name:
            if name.endswith('.'):
                basename = name + extension(basename)
            else:
                basename = name

        # if not self.file_allowed(storage, basename):
        #     raise UploadNotAllowed()

        if folder:
            target_folder = os.path.join(self.config.destination, folder)
        else:
            target_folder = self.config.destination
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)

        target = os.path.join(target_folder, basename)
        if os.path.exists(target):
            c_dm5 = get_md5(storage.stream.read())
            with open(target, "rb") as f:
                d_dm5 = get_md5(f.read())
            if c_dm5 != d_dm5:
                basename = self.resolve_conflict(target_folder, basename)
                target = os.path.join(target_folder, basename)
        storage.stream.seek(0, 0)
        storage.save(target)
        if folder:
            return posixpath.join(folder, basename)
        else:
            return basename


text = UploadSet('text', TEXT)
