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

from unittest import mock

import testtools

from observabilityclient import prometheus_client
from observabilityclient import rbac
from observabilityclient.tests.unit.test_prometheus_client import (
    MetricListMatcher
)
from observabilityclient.v1 import python_api


class QueryManagerTest(testtools.TestCase):
    def setUp(self):
        super(QueryManagerTest, self).setUp()
        self.client = mock.Mock()
        prom_client = prometheus_client.PrometheusAPIClient("somehost")
        self.client.prometheus_client = prom_client

        self.rbac = mock.Mock(wraps=rbac.PromQLRbac(prom_client, mock.Mock()))
        self.rbac.labels = {'project': 'project_id'}

        self.manager = python_api.QueryManager(self.client)

        self.client.rbac = self.rbac
        self.client.query = self.manager

    def test_list(self):
        returned_data = {'data': ['metric1', 'test42', 'abc2']}
        expected = ['abc2', 'metric1', 'test42']

        with mock.patch.object(prometheus_client.PrometheusAPIClient, '_get',
                               return_value=returned_data):
            ret1 = self.manager.list()
            self.assertEqual(expected, ret1)

            ret2 = self.manager.list(disable_rbac=True)
            self.assertEqual(expected, ret2)

    def test_show(self):
        query = 'some_metric'
        returned_by_prom = {
            'data': {
                'resultType': 'non-vector'
            },
            'value': [1234567, 42],
            'metric': {
                'label': 'label_value'
            }
        }
        expected = [prometheus_client.PrometheusMetric(returned_by_prom)]
        expected_matcher = MetricListMatcher(expected)

        with mock.patch.object(prometheus_client.PrometheusAPIClient, '_get',
                               return_value=returned_by_prom):
            ret2 = self.manager.show(query, disable_rbac=True)
            self.rbac.append_rbac_labels.assert_not_called()

        with mock.patch.object(prometheus_client.PrometheusAPIClient, '_get',
                               return_value=returned_by_prom):
            ret1 = self.manager.show(query)
            self.rbac.append_rbac_labels.assert_not_called()

        self.assertThat(ret1, expected_matcher)
        self.assertThat(ret2, expected_matcher)

    def test_query(self):
        queried_metric_name = 'some_metric'
        query = queried_metric_name
        returned_by_prom = {
            'data': {
                'resultType': 'non-vector'
            },
            'value': [1234567, 42],
            'metric': {
                'label': 'label_value'
            }
        }
        expected = [prometheus_client.PrometheusMetric(returned_by_prom)]
        expected_matcher = MetricListMatcher(expected)
        with mock.patch.object(prometheus_client.PrometheusAPIClient, '_get',
                               return_value=returned_by_prom), \
                mock.patch.object(python_api.QueryManager, 'list',
                                  return_value=queried_metric_name):

            ret1 = self.manager.query(query, disable_rbac=True)
            self.rbac.modify_query.assert_not_called()

            ret2 = self.manager.query(query)
            self.rbac.modify_query.assert_not_called()

        self.assertThat(ret1, expected_matcher)
        self.assertThat(ret2, expected_matcher)

    def test_delete(self):
        matches = "some_metric"
        start = 0
        end = 100
        with mock.patch.object(prometheus_client.PrometheusAPIClient,
                               'delete') as m:
            self.manager.delete(matches, start, end)
        m.assert_called_with(matches, start, end)

    def test_clean_tombstones(self):
        with mock.patch.object(prometheus_client.PrometheusAPIClient,
                               'clean_tombstones') as m:
            self.manager.clean_tombstones()
        m.assert_called_once()

    def test_snapshot(self):
        with mock.patch.object(prometheus_client.PrometheusAPIClient,
                               'snapshot') as m:
            self.manager.snapshot()
        m.assert_called_once()
