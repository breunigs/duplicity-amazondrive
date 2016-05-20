# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2015 Stefan Breunig <stefan-duplicity@breunig.xyz>
# Copyright 2015 Malay Shah <malays@gmail.com>
# Based on the backend ncftpbackend.py
#
# This file is part of duplicity.
#
# Duplicity is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Duplicity is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with duplicity; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os.path
import urllib
import string
import json
import sys
import time
import io


import duplicity.backend
from duplicity import globals
from duplicity import log
from duplicity.errors import * #@UnusedWildImport
from duplicity import tempdir
from duplicity import util


class ACDBackend(duplicity.backend.Backend):
    OAUTH_TOKEN_PATH = os.path.expanduser('~/.duplicity_acd_oauthtoken.json')

    API_METADATA_URL = 'https://drive.amazonaws.com/drive/v1/'
    API_CONTENT_URL = 'https://content-na.drive.amazonaws.com/cdproxy/'

    OAUTH_AUTHORIZE_URL = 'https://www.amazon.com/ap/oa'
    OAUTH_TOKEN_URL = 'https://api.amazon.com/auth/o2/token'
    OAUTH_REDIRECT_URL = 'http://127.0.0.1:53682/'
    OAUTH_SCOPE = ['clouddrive:read_all', 'clouddrive:write']

    # TODO: borrowed from rclone
    CLIENT_ID = 'amzn1.application-oa2-client.6bf18d2d1f5b485c94c8988bb03ad0e7'
    CLIENT_SECRET = '9decbe76f25adab4d9dce361194512c192594038f494f738ed56d7427891db05'

    MULTIPART_BOUNDARY = 'DuplicityFormBoundaryd66364f7f8924f7e9d478e19cf4b871d114a1e00262542'

    def __init__(self, parsed_url):
        duplicity.backend.Backend.__init__(self, parsed_url)

        self.import_dependencies()

        self.logical_path = parsed_url.path.lstrip('/')

        if self.logical_path == "":
            raise BackendException((
                'You did not specify a path. '
                'Please specify a path, e.g. acd://duplicity_backups'))

        if globals.volsize > (10 * 1024 * 1024 * 1024):
            # TODO: research 10 GiB limit
            raise BackendException((
                'Your --volsize is bigger than 10 GiB, which is the maximum '
                'file size on ACD that does not require work arounds.'))
        self.initialize_oauth2_session()
        self.resolve_logical_path()

    def import_dependencies(self):
        # Import requests and requests-oauthlib
        try:
            # On debian (and derivatives), get these dependencies using:
            # apt-get install python-requests python-requests-oauthlib
            # On fedora (and derivatives), get these dependencies using:
            # yum install python-requests python-requests-oauthlib
            global requests
            global OAuth2Session
            import requests
            from requests_oauthlib import OAuth2Session
        except ImportError:
            raise BackendException((
                'OneDrive backend requires python-requests and '
                'python-requests-oauthlib to be installed. Please install '
                'them and try again.'))

    def initialize_oauth2_session(self):
        def token_updater(token):
            try:
                with open(self.OAUTH_TOKEN_PATH, 'w') as f:
                    json.dump(token, f)
            except Exception as e:
                log.Error(('Could not save the OAuth2 token to %s. '
                           'This means you may need to do the OAuth2 '
                           'authorization process again soon. '
                           'Original error: %s' % (
                               self.OAUTH_TOKEN_PATH, e)))

        token = None
        try:
            with open(self.OAUTH_TOKEN_PATH) as f:
                token = json.load(f)
        except IOError as e:
            log.Error(('Could not load OAuth2 token. '
                       'Trying to create a new one. (original error: %s)' % e))

        self.http_client = OAuth2Session(
            self.CLIENT_ID,
            scope=self.OAUTH_SCOPE,
            redirect_uri=self.OAUTH_REDIRECT_URL,
            token=token,
            auto_refresh_kwargs={
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET,
            },
            auto_refresh_url=self.OAUTH_TOKEN_URL,
            token_updater=token_updater)

        # TODO: needed?
        # We have to refresh token manually because it's not working "under the
        # covers"
        # if token is not None:
        #     self.http_client.refresh_token(self.OAUTH_TOKEN_URL)

        user_endpoint_response = self.http_client.get(self.API_METADATA_URL
            + 'account/endpoint')
        if user_endpoint_response.status_code != requests.codes.ok:
            token = None

        if token is None:
            if not sys.stdout.isatty() or not sys.stdin.isatty():
                log.FatalError(('The OAuth2 token could not be loaded from %s '
                                'and you are not running duplicity '
                                'interactively, so duplicity cannot possibly '
                                'access ACD.' % self.OAUTH_TOKEN_PATH))
            authorization_url, state = self.http_client.authorization_url(
                self.OAUTH_AUTHORIZE_URL)

            print ''
            print ('In order to authorize duplicity to access your ACD, '
                   'please open the following URL in a browser and copy '
                   'the URL of the blank page the dialog leads to: %s'
                    % authorization_url)
            print ''

            redirected_to = (raw_input('URL of the blank page: ')
                .replace('http://', 'https://', 1))

            token = self.http_client.fetch_token(
                self.OAUTH_TOKEN_URL,
                client_secret=self.CLIENT_SECRET,
                authorization_response=redirected_to)

            user_endpoint_response = self.http_client.get(self.API_METADATA_URL
                 + 'account/endpoint')
            user_endpoint_response.raise_for_status()

            token_updater(token)

        urls = user_endpoint_response.json()

        if 'metadataUrl' not in urls or 'contentUrl' not in urls:
            log.FatalError('Endpoint Response did not include expected '
                           'endpoints for this user. Is the token valid?')

        self.API_METADATA_URL = urls['metadataUrl']
        self.API_CONTENT_URL = urls['contentUrl']

    def resolve_logical_path(self):
        """Resolve the logical path into a node id. Non-existing folders will
        be created."""

        folders_response = self.http_client.get(self.API_METADATA_URL + 'nodes?filters=kind:FOLDER')
        folders = folders_response.json()['data']

        root_node = (f for f in folders if f.get('isRoot') == True).next()
        parent_node_id = root_node['id']

        for component in [x for x in self.logical_path.split('/') if x]:
            candidates = [f for f in folders if f.get('name') == component and
                parent_node_id in f['parents']]

            if len(candidates) >= 2:
                log.FatalError(('There are multiple folders with the same name '
                                'in the same parent. ParentID: %s FolderName: '
                                '%s' % (parent_node_id, component)))
            elif len(candidates) == 1:
                parent_node_id = candidates[0]['id']
            else:
                parent_node_id = self.mkdir(parent_node_id, component)

        self.logical_path_id = parent_node_id

    def mkdir(self, parent_node_id, folder_name):
        """Create folder below given node id. Returns new folder's id."""

        data = { 'name': folder_name, 'parents': [parent_node_id], 'kind' : 'FOLDER' }
        response = self.http_client.post(
            self.API_METADATA_URL + 'nodes',
            data=json.dumps(data))
        response.raise_for_status()
        return response.json()['id']

    def bytes_available(self):
        quota = self.http_client.get(self.API_METADATA_URL + 'account/quota')
        quota.json()['available']

    def multipart_stream(self, metadata, source_path):
        """Generator for chunked multipart/form-data file upload from streamed input"""

        boundary = self.MULTIPART_BOUNDARY

        yield str.encode('--%s\r\nContent-Disposition: form-data; '
                         'name="metadata"\r\n\r\n' % boundary +
                         '%s\r\n' % json.dumps(metadata) +
                         '--%s\r\n' % boundary)
        yield b'Content-Disposition: form-data; name="content"; filename="i_love_backups"\r\n'
        yield b'Content-Type: application/octet-stream\r\n\r\n'

        with source_path.open() as stream:
            while True:
                f = stream.read(io.DEFAULT_BUFFER_SIZE)
                if f:
                    yield f
                else:
                    break

        yield str.encode('\r\n--%s--\r\n' % boundary +
                         'multipart/form-data; boundary=%s' % boundary)

    def _put(self, source_path, remote_filename):
        metadata = { 'name': remote_filename, 'kind': 'FILE', 'parents': [self.logical_path_id] }
        headers = { 'Content-Type': 'multipart/form-data; boundary=%s'
                                                     % self.MULTIPART_BOUNDARY}

        start = time.time()

        # TODO: doesnt work :/
        # Attempt 1 failed. HTTPError: 400 Client Error: Bad Request for url: https://content-eu.drive.amazonaws.com/cdproxy/nodes?suppress=deduplication
        response = self.http_client.post(
            self.API_CONTENT_URL + 'nodes?suppress=deduplication',
            data=self.multipart_stream(metadata, source_path))
        response.raise_for_status()

        log.Debug("PUT file in %fs" % (time.time() - start))



    def _get(self, remote_filename, local_path):
        log.FatalError('_get not yet implemented')

    def _query(self, remote_filename):
        log.FatalError('_query not yet implemented')

    def _list(self):
        """List files in backup directory"""

        children_response = self.http_client.get(self.API_METADATA_URL + 'nodes/' + self.logical_path_id + '/children')
        children = children_response.json()['data']

        return [f['name'] for f in children if f['kind'] == 'FILE']


    def _delete(self, remote_filename):
        log.FatalError('delete not yet implemented')


duplicity.backend.register_backend("acd", ACDBackend)
