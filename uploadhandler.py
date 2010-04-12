#
# Copyright 2008 ebartels
# Copyright 2008 Fairview Computing
# Copyright 2010 John Keyes
#
# Derived from: 
#  * http://www.djangosnippets.org/snippets/678
#  * http://www.fairviewcomputing.com/blog/2008/10/21/ajax-upload-progress-bars-jquery-django-nginx/
#

from django.core.files.uploadhandler import TemporaryFileUploadHandler
from django.core.cache import cache
from django.conf import settings

import logging

class UploadProgressCachedHandler(TemporaryFileUploadHandler):
    """
    Tracks progress for file uploads.
    The http post request must contain a query parameter, 'X-Progress-ID',
    which should contain a unique string to identify the upload to be tracked.
    """

    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.progress_id = None
        self.cache_key = None
        self.logger = logging.getLogger("uploadhandler.UploadProgressCachedHandler")

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        self.content_length = content_length
        if 'X-Progress-ID' in self.request.GET:
            self.progress_id = self.request.GET['X-Progress-ID']
        if self.progress_id:
            self.cache_key = "%s_%s" % (self.request.META['REMOTE_ADDR'], self.progress_id )
            cache.set(self.cache_key, {
                'state': 'uploading',
                'size': self.content_length,
                'received': 0
            })
            if settings.DEBUG:
                self.logger.debug('Initialized cache with %s %s' % (self.cache_key, cache.get(self.cache_key)))
        else:
            self.logger.warn("No progress ID.")

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        if settings.DEBUG:
            self.logger.debug("Field_name %s file_name %s" % (field_name, file_name))

    def receive_data_chunk(self, raw_data, start):
        if self.cache_key:
            data = cache.get(self.cache_key)
            if data:
                data['received'] += self.chunk_size
                cache.set(self.cache_key, data)
                if settings.DEBUG:
                    self.logger.debug('Updated cache with %s %s' % (self.cache_key, data))
        return raw_data

    def file_complete(self, file_size):
        pass

    def upload_complete(self):
        if settings.DEBUG:
            self.logger.debug('Upload complete for %s' % self.cache_key)
        if self.cache_key:
            data = cache.get(self.cache_key)
            if data:
                # upload is 'done'.
                data['state'] = 'done'
                cache.set(self.cache_key, data)
                if settings.DEBUG:
                    self.logger.debug('Updated cache with %s %s' % (self.cache_key, data))
