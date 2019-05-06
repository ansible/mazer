import io
import uuid


class MultiPartForm(object):
    """
    Accumulate the data to be used when posting a form.
    Borrowed from https://blog.thesparktree.com/the-unfortunately-long-story-dealing-with
    """

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = '--------------------------%s' % uuid.uuid4().hex
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, fileHandle, mimetype):
        """Add a file to be uploaded."""
        body = fileHandle.read()
        self.files.append((fieldname, filename, mimetype, body))
        return

    def get_binary(self):
        """Return a binary buffer containing the form data, including attached files."""
        part_boundary = '--' + self.boundary

        binary = io.BytesIO()
        needsCLRF = False
        # Add the form fields
        for name, value in self.form_fields:
            if needsCLRF:
                binary.write(str.encode('\r\n', 'utf-8'))
            needsCLRF = True

            block = [part_boundary,
                     'Content-Disposition: form-data; name="%s"' % name,
                     '',
                     value
                     ]
            binary.write(str.encode('\r\n'.join(block), 'utf-8'))

        # Add the files to upload
        for field_name, filename, content_type, body in self.files:
            if needsCLRF:
                binary.write(str.encode('\r\n', 'utf-8'))
            needsCLRF = True

            block = [part_boundary,
                     str('Content-Disposition: file; name="%s"; filename="%s"' %
                         (field_name, filename)),
                     'Content-Type: %s' % content_type,
                     ''
                     ]
            binary.write(str.encode('\r\n'.join(block), 'utf-8'))
            binary.write(str.encode('\r\n', 'utf-8'))
            binary.write(body)

        # add closing boundary marker,
        binary.write(str.encode('\r\n--' + self.boundary + '--\r\n', 'utf-8'))
        return binary
