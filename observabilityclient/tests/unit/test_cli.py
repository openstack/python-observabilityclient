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

from observabilityclient.prometheus_client import PrometheusMetric
from observabilityclient.utils import metric_utils
from observabilityclient.v1 import cli


class CliTest(testtools.TestCase):
    def setUp(self):
        super(CliTest, self).setUp()
        self.client = mock.Mock()
        self.client.query = mock.Mock()

    def test_list(self):
        args_enabled = {'disable_rbac': False}
        args_disabled = {'disable_rbac': True}

        metric_names = ['name1', 'name2', 'name3']
        expected = (['metric_name'], [['name1'], ['name2'], ['name3']])
        cli_list = cli.List(mock.Mock(), mock.Mock())

        with (mock.patch.object(metric_utils, 'get_client',
                                return_value=self.client),
              mock.patch.object(self.client.query, 'list',
                                return_value=metric_names) as m):
            ret1 = cli_list.take_action(args_enabled)
            m.assert_called_with(disable_rbac=False)

            ret2 = cli_list.take_action(args_disabled)
            m.assert_called_with(disable_rbac=True)

        self.assertEqual(ret1, expected)
        self.assertEqual(ret2, expected)

    def test_show(self):
        args_enabled = {'name': 'metric_name', 'disable_rbac': False}
        args_disabled = {'name': 'metric_name', 'disable_rbac': True}

        metric = {
            'value': [123456, 12],
            'metric': {'label1': 'value1'}
        }
        prom_metric = [PrometheusMetric(metric)]
        expected = ['label1', 'value'], [['value1', 12]]

        cli_show = cli.Show(mock.Mock(), mock.Mock())

        with (mock.patch.object(metric_utils, 'get_client',
                                return_value=self.client),
              mock.patch.object(self.client.query, 'show',
                                return_value=prom_metric) as m):

            ret1 = cli_show.take_action(args_enabled)
            m.assert_called_with('metric_name', disable_rbac=False)

            ret2 = cli_show.take_action(args_disabled)
            m.assert_called_with('metric_name', disable_rbac=True)

        self.assertEqual(ret1, expected)
        self.assertEqual(ret2, expected)

    def test_query(self):
        query = ("some_query{label!~'not_this_value'} - "
                 "sum(second_metric{label='this'})")
        args_enabled = {'query': query, 'disable_rbac': False}
        args_disabled = {'query': query, 'disable_rbac': True}

        metric = {
            'value': [123456, 12],
            'metric': {'label1': 'value1'}
        }

        prom_metric = [PrometheusMetric(metric)]
        expected = ['label1', 'value'], [['value1', 12]]

        cli_query = cli.Query(mock.Mock(), mock.Mock())

        with (mock.patch.object(metric_utils, 'get_client',
                                return_value=self.client),
              mock.patch.object(self.client.query, 'query',
                                return_value=prom_metric) as m):

            ret1 = cli_query.take_action(args_enabled)
            m.assert_called_with(query, disable_rbac=False)

            ret2 = cli_query.take_action(args_disabled)
            m.assert_called_with(query, disable_rbac=True)

        self.assertEqual(ret1, expected)
        self.assertEqual(ret2, expected)

    def test_delete(self):
        matches = "some_label_name"
        args = {'matches': matches, 'start': 0, 'end': 10}

        cli_delete = cli.Delete(mock.Mock(), mock.Mock())

        with (mock.patch.object(metric_utils, 'get_client',
                                return_value=self.client),
              mock.patch.object(self.client.query, 'delete') as m):

            cli_delete.take_action(args)
            m.assert_called_with(matches, 0, 10)

    def test_clean_combstones(self):
        cli_clean_tombstones = cli.CleanTombstones(mock.Mock(), mock.Mock())

        with (mock.patch.object(metric_utils, 'get_client',
                                return_value=self.client),
              mock.patch.object(self.client.query, 'clean_tombstones') as m):

            cli_clean_tombstones.take_action({})
            m.assert_called_once()

    def test_snapshot(self):
        cli_snapshot = cli.Snapshot(mock.Mock(), mock.Mock())
        file_name = 'some_file_name'

        with (mock.patch.object(metric_utils, 'get_client',
                                return_value=self.client),
              mock.patch.object(self.client.query, 'snapshot',
                                return_value=file_name) as m):

            ret = cli_snapshot.take_action({})
            m.assert_called_once()
        self.assertEqual(ret, (["Snapshot file name"], [[file_name]]))
