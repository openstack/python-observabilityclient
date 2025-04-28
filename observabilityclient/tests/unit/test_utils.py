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

import os
from unittest import mock

import testtools

from observabilityclient import prometheus_client
from observabilityclient.utils import metric_utils


class GetConfigFileTest(testtools.TestCase):
    def setUp(self):
        super(GetConfigFileTest, self).setUp()

    def test_current_dir(self):
        with mock.patch.object(os.path, 'exists', return_value=True), \
                mock.patch.object(metric_utils, 'open') as m:
            metric_utils.get_config_file()
        m.assert_called_with(metric_utils.CONFIG_FILE_NAME, 'r')

    def test_path_order(self):
        expected = [mock.call(metric_utils.CONFIG_FILE_NAME, 'r'),
                    mock.call((f"{os.environ['HOME']}/.config/openstack/"
                               f"{metric_utils.CONFIG_FILE_NAME}")),
                    mock.call((f"/etc/openstack/"
                               f"{metric_utils.CONFIG_FILE_NAME}"))]
        with mock.patch.object(os.path, 'exists', return_value=False) as m:
            ret = metric_utils.get_config_file()
        m.call_args_list == expected
        self.assertIsNone(ret)


class GetPrometheusClientTest(testtools.TestCase):
    def setUp(self):
        super(GetPrometheusClientTest, self).setUp()
        config_data = 'host: "somehost"\nport: "1234"'
        self.config_file = mock.mock_open(read_data=config_data)("name", 'r')

    def test_get_prometheus_client_from_file(self):
        with mock.patch.object(metric_utils, 'get_config_file',
                               return_value=self.config_file), \
                mock.patch.object(prometheus_client.PrometheusAPIClient,
                                  "__init__", return_value=None) as m:
            metric_utils.get_prometheus_client()
        m.assert_called_with("somehost:1234", None, "")

    def test_get_prometheus_client_env_override(self):
        with mock.patch.dict(os.environ,
                             {'PROMETHEUS_HOST': 'env_override'}), \
                mock.patch.object(metric_utils, 'get_config_file',
                                  return_value=self.config_file), \
                mock.patch.object(prometheus_client.PrometheusAPIClient,
                                  "__init__", return_value=None) as m:
            metric_utils.get_prometheus_client()
        m.assert_called_with("env_override:1234", None, "")

    def test_get_prometheus_client_no_config_file(self):
        patched_env = {'PROMETHEUS_HOST': 'env_override',
                       'PROMETHEUS_PORT': 'env_port'}
        with mock.patch.dict(os.environ, patched_env), \
                mock.patch.object(metric_utils, 'get_config_file',
                                  return_value=None), \
                mock.patch.object(prometheus_client.PrometheusAPIClient,
                                  "__init__", return_value=None) as m:
            metric_utils.get_prometheus_client()
        m.assert_called_with("env_override:env_port", None, "")

    def test_get_prometheus_client_prefix_in_env_variable(self):
        patched_env = {'PROMETHEUS_HOST': 'env_override',
                       'PROMETHEUS_PORT': 'env_port',
                       'PROMETHEUS_ROOT_PATH': 'root_path_env'}
        with mock.patch.dict(os.environ, patched_env), \
                mock.patch.object(metric_utils, 'get_config_file',
                                  return_value=None), \
                mock.patch.object(prometheus_client.PrometheusAPIClient,
                                  "__init__", return_value=None) as m:
            metric_utils.get_prometheus_client()
        m.assert_called_with("env_override:env_port", None, "root_path_env")

    def test_get_prometheus_client_missing_configuration(self):
        with mock.patch.dict(os.environ, {}), \
                mock.patch.object(metric_utils, 'get_config_file',
                                  return_value=None), \
                mock.patch.object(prometheus_client.PrometheusAPIClient,
                                  "__init__", return_value=None):
            self.assertRaises(metric_utils.ConfigurationError,
                              metric_utils.get_prometheus_client)


class FormatLabelsTest(testtools.TestCase):
    def setUp(self):
        super(FormatLabelsTest, self).setUp()

    def test_format_labels_with_normal_labels(self):
        input_dict = {"label_key1": "label_value1",
                      "label_key2": "label_value2"}
        expected = "label_key1='label_value1', label_key2='label_value2'"

        ret = metric_utils.format_labels(input_dict)
        self.assertEqual(expected, ret)

    def test_format_labels_with_quoted_labels(self):
        input_dict = {"label_key1": "'label_value1'",
                      "label_key2": "'label_value2'"}
        expected = "label_key1='label_value1', label_key2='label_value2'"

        ret = metric_utils.format_labels(input_dict)
        self.assertEqual(expected, ret)


class Metrics2ColsTest(testtools.TestCase):
    def setUp(self):
        super(Metrics2ColsTest, self).setUp()

    def test_metrics2cols(self):
        metric = {
            'value': [
                1234567,
                5
            ],
            'metric': {
                'label1': 'value1',
                'label2': 'value2',
            }
        }
        input_metrics = [prometheus_client.PrometheusMetric(metric)]
        expected = (['label1', 'label2', 'value'], [['value1', 'value2', 5]])

        ret = metric_utils.metrics2cols(input_metrics)
        self.assertEqual(expected, ret)

    def test_metrics2cols_column_ordering(self):
        metric = {
            'value': [
                1234567,
                5
            ],
            'metric': {
                'a_label1': 'value1',
                'b_label2': 'value2',
            }
        }
        input_metrics = [prometheus_client.PrometheusMetric(metric)]
        expected = (['a_label1', 'b_label2', 'value'],
                    [['value1', 'value2', 5]])

        ret = metric_utils.metrics2cols(input_metrics)
        self.assertEqual(expected, ret)

        metric = {
            'value': [
                1234567,
                5
            ],
            'metric': {
                'b_label1': 'value1',
                'a_label2': 'value2',
            }
        }
        input_metrics = [prometheus_client.PrometheusMetric(metric)]
        expected = (['a_label2', 'b_label1', 'value'],
                    [['value2', 'value1', 5]])

        ret = metric_utils.metrics2cols(input_metrics)
        self.assertEqual(expected, ret)

        metric1 = {
            'value': [
                1234567,
                5
            ],
            'metric': {
                'b_label1': 'value1',
                'a_label2': 'value2',
            }
        }
        metric2 = {
            'value': [
                1234567,
                5
            ],
            'metric': {
                'b_label1': 'value1',
                'a_label2': 'value2',
                'd_label3': 'value3',
                'c_label4': 'value4',
            }
        }
        input_metrics = [prometheus_client.PrometheusMetric(metric1),
                         prometheus_client.PrometheusMetric(metric2)]
        expected = (['a_label2', 'b_label1', 'c_label4', 'd_label3', 'value'],
                    [['value2', 'value1', '', '', 5],
                     ['value2', 'value1', 'value4', 'value3', 5]]
                    )

        ret = metric_utils.metrics2cols(input_metrics)
        self.assertEqual(expected, ret)
