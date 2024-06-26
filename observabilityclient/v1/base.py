#   Copyright 2022 Red Hat, Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.
#

from osc_lib.command import command

from observabilityclient.i18n import _


class ObservabilityBaseCommand(command.Command):
    """Base class for metric commands."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        # TODO(jwysogla): Should this be restricted somehow?
        parser.add_argument(
            '--disable-rbac',
            action='store_true',
            help=_("Disable rbac injection")
        )
        return parser


class Manager(object):
    """Base class for the python api."""

    DEFAULT_HEADERS = {
        "Accept": "application/json",
    }

    def __init__(self, client):
        self.client = client
        self.prom = client.prometheus_client

    def _set_default_headers(self, kwargs):
        headers = kwargs.get('headers', {})
        for k, v in self.DEFAULT_HEADERS.items():
            if k not in headers:
                headers[k] = v
        kwargs['headers'] = headers
        return kwargs

    def _get(self, *args, **kwargs):
        self._set_default_headers(kwargs)
        return self.client.api.get(*args, **kwargs)

    def _post(self, *args, **kwargs):
        self._set_default_headers(kwargs)
        return self.client.api.post(*args, **kwargs)

    def _put(self, *args, **kwargs):
        self._set_default_headers(kwargs)
        return self.client.api.put(*args, **kwargs)

    def _patch(self, *args, **kwargs):
        self._set_default_headers(kwargs)
        return self.client.api.patch(*args, **kwargs)

    def _delete(self, *args, **kwargs):
        self._set_default_headers(kwargs)
        return self.client.api.delete(*args, **kwargs)
