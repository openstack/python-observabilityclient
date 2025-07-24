#   Copyright 2023 Red Hat, Inc.
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

import keystoneauth1.session

from observabilityclient import rbac
from observabilityclient.utils.metric_utils import get_prometheus_client
from observabilityclient.v1 import python_api


class Client(object):
    """Client for the observabilityclient api."""

    def __init__(self, session=None, adapter_options=None,
                 session_options=None, disable_rbac=False):
        """Initialize a new client for the Observabilityclient v1 API."""
        session_options = session_options or {}
        adapter_options = adapter_options or {}

        adapter_options.setdefault('service_type', "metric-storage")

        if session is None:
            session = keystoneauth1.session.Session(**session_options)
        else:
            if session_options:
                raise ValueError("session and session_options are exclusive")

        self.session = session

        self.prometheus_client = get_prometheus_client(
            session, adapter_options
        )
        self.query = python_api.QueryManager(self)
        self.rbac = rbac.PromQLRbac(
            self.prometheus_client,
            self.session.get_project_id()
        )
