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

import logging

import requests


LOG = logging.getLogger(__name__)


class PrometheusAPIClientError(Exception):
    def __init__(self, response):
        self.resp = response

    def __str__(self) -> str:
        if self.resp.status_code != requests.codes.ok:
            if self.resp.status_code != 204:
                try:
                    decoded = self.resp.json()
                    if 'error' in decoded:
                        return f'[{self.resp.status_code}] {decoded["error"]}'
                except requests.JSONDecodeError:
                    # If an https endpoint is accessed as http,
                    # we get 400 status with plain text instead of
                    # json and decoding it raises exception.
                    return f'[{self.resp.status_code}] {self.resp.text}'
            return f'[{self.resp.status_code}] {self.resp.reason}'
        else:
            decoded = self.resp.json()
            return f'[{decoded.status}]'

    def __repr__(self) -> str:
        return self.__str__()


class PrometheusMetric(object):
    def __init__(self, input):
        self.timestamp = input['value'][0]
        self.labels = input['metric']
        self.value = input['value'][1]


class PrometheusAPIClient(object):
    def __init__(self, host, session=None, root_path=""):
        self._host = host
        if not self._host.endswith('/'):
            self._host += '/'
        if session is None:
            self._session = requests.Session()
        else:
            self._session = session
        self._session.verify = False
        self._root_path = root_path
        if root_path != "" and not self._root_path.endswith('/'):
            self._root_path += '/'

    def set_ca_cert(self, ca_cert):
        self._session.verify = ca_cert

    def set_client_cert(self, client_cert, client_key):
        self._session.cert = (client_cert, client_key)

    def set_basic_auth(self, auth_user, auth_password):
        self._session.auth = (auth_user, auth_password)

    def _get_url(self, endpoint):
        scheme = 'https' if self._session.verify else 'http'
        return f"{scheme}://{self._host}{self._root_path}api/v1/{endpoint}"

    def _get(self, endpoint, params=None):
        url = self._get_url(endpoint)
        resp = self._session.get(url, params=params,
                                 headers={'Accept': 'application/json',
                                          'Accept-Encoding': 'identity'})
        if resp.status_code != requests.codes.ok:
            raise PrometheusAPIClientError(resp)
        decoded = resp.json()
        if decoded['status'] != 'success':
            raise PrometheusAPIClientError(resp)

        return decoded

    def _post(self, endpoint, params=None):
        url = self._get_url(endpoint)
        resp = self._session.post(url, params=params,
                                  headers={'Accept': 'application/json'})
        if resp.status_code != requests.codes.ok:
            raise PrometheusAPIClientError(resp)
        decoded = resp.json()
        if 'status' in decoded and decoded['status'] != 'success':
            raise PrometheusAPIClientError(resp)
        return decoded

    def query(self, query):
        """Send custom queries to Prometheus.

        :param query: the query to send
        :type query: str
        """
        LOG.debug("Querying prometheus with query: %s", query)
        decoded = self._get("query", dict(query=query))

        if decoded['data']['resultType'] == 'vector':
            result = [PrometheusMetric(i) for i in decoded['data']['result']]
        else:
            result = [PrometheusMetric(decoded)]
        return result

    def series(self, matches):
        """Query the /series/ endpoint of prometheus.

        :param matches: List of matches to send as parameters
        :type matches: [str]
        """
        LOG.debug("Querying prometheus for series with matches: %s", matches)
        decoded = self._get("series", {"match[]": matches})

        return decoded['data']

    def labels(self):
        """Query the /labels/ endpoint of prometheus, returns list of labels.

        There isn't a way to tell prometheus to restrict
        which labels to return. It's not possible to enforce
        rbac with this for example.
        """
        LOG.debug("Querying prometheus for labels")
        decoded = self._get("labels")

        return decoded['data']

    def label_values(self, label):
        """Query prometheus for values of a specified label.

        :param label: Name of label for which to return values
        :type label: str
        """
        LOG.debug("Querying prometheus for the values of label: %s", label)
        decoded = self._get(f"label/{label}/values")

        return decoded['data']

    # ---------
    # admin api
    # ---------

    def delete(self, matches, start=None, end=None):
        """Delete some metrics from prometheus.

        :param matches: List of matches, that specify which metrics to delete
        :type matches [str]
        :param start: Timestamp from which to start deleting.
                      None for as early as possible.
        :type start: timestamp
        :param end: Timestamp until which to delete.
                    None for as late as possible.
        :type end: timestamp
        """
        # NOTE Prometheus doesn't seem to return anything except
        #      of 204 status code. There doesn't seem to be a
        #      way to know if anything got actually deleted.
        #      It does however return 500 code and error msg
        #      if the admin APIs are disabled.
        LOG.debug("Deleting metrics from prometheus matching: %s", matches)
        try:
            self._post("admin/tsdb/delete_series", {"match[]": matches,
                                                    "start": start,
                                                    "end": end})
        except PrometheusAPIClientError as exc:
            # The 204 is allowed here. 204 is "No Content",
            # which is expected on a successful call
            if exc.resp.status_code != 204:
                raise exc

    def clean_tombstones(self):
        """Ask prometheus to clean tombstones."""
        LOG.debug("Cleaning tombstones from prometheus")
        try:
            self._post("admin/tsdb/clean_tombstones")
        except PrometheusAPIClientError as exc:
            # The 204 is allowed here. 204 is "No Content",
            # which is expected on a successful call
            if exc.resp.status_code != 204:
                raise exc

    def snapshot(self):
        """Create a snapshot and return the file name containing the data."""
        LOG.debug("Taking prometheus data snapshot")
        ret = self._post("admin/tsdb/snapshot")
        return ret["data"]["name"]
