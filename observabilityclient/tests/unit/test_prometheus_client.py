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

import requests

import testtools

from observabilityclient import prometheus_client as client


class MetricListMatcher(testtools.Matcher):
    def __init__(self, expected):
        self.expected = expected

    def __str__(self):
        return ("Matches Lists of metrics as returned "
                "by prometheus_client.PremetheusAPIClient.query")

    def metric_to_str(self, metric):
        return (f"Labels: {metric.labels}\n"
                f"Timestamp: {metric.timestamp}\n"
                f"Value: {metric.value}")

    def match(self, observed):
        if len(self.expected) != len(observed):
            description = (f"len(expected) != len(observed) because "
                           f"{len(self.expected)} != {len(observed)}")
            return testtools.matchers.Mismatch(description=description)

        for e in self.expected:
            for o in observed:
                if (e.timestamp == o.timestamp and
                        e.value == o.value and
                        e.labels == o.labels):
                    observed.remove(o)
                    break

        if len(observed) != 0:
            description = "Couldn't match the following metrics:\n"
            for o in observed:
                description += self.metric_to_str(o) + "\n\n"
            return testtools.matchers.Mismatch(description=description)
        return None


class PrometheusAPIClientTestBase(testtools.TestCase):
    def setUp(self):
        super(PrometheusAPIClientTestBase, self).setUp()

    class GoodResponse(object):
        def __init__(self):
            self.status_code = 200

        def json(self):
            return {"status": "success"}

    class BadResponse(object):
        def __init__(self):
            self.status_code = 500

        def json(self):
            return {"status": "error", "error": "test_error"}

    class NoContentResponse(object):
        def __init__(self):
            self.status_code = 204

        def json(self):
            raise requests.exceptions.JSONDecodeError("No content")


class PrometheusAPIClientTest(PrometheusAPIClientTestBase):
    def test_get(self):
        url = "test"
        root_path = "root_path"
        expected_url = f"http://localhost:9090/{root_path}/api/v1/{url}"

        params = {"query": "ceilometer_image_size{publisher='localhost'}"}
        expected_params = params

        return_value = self.GoodResponse()
        with mock.patch.object(requests.Session, 'get',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090",
                                           root_path=root_path)
            c._get(url, params)

        m.assert_called_with(expected_url,
                             params=expected_params,
                             headers={'Accept': 'application/json',
                                      'Accept-Encoding': 'identity'})

    def test_get_error(self):
        url = "test"
        params = {"query": "ceilometer_image_size{publisher='localhost'}"}

        return_value = self.BadResponse()
        with mock.patch.object(requests.Session, 'get',
                               return_value=return_value):
            c = client.PrometheusAPIClient("localhost:9090")
            self.assertRaises(client.PrometheusAPIClientError,
                              c._get, url, params)

        return_value = self.NoContentResponse()
        with mock.patch.object(requests.Session, 'get',
                               return_value=return_value):
            c = client.PrometheusAPIClient("localhost:9090")
            self.assertRaises(client.PrometheusAPIClientError,
                              c._get, url, params)

    def test_post(self):
        url = "test"
        expected_url = f"http://localhost:9090/api/v1/{url}"

        params = {"query": "ceilometer_image_size{publisher='localhost'}"}
        expected_params = params

        return_value = self.GoodResponse()
        with mock.patch.object(requests.Session, 'post',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            c._post(url, params)

        m.assert_called_with(expected_url,
                             params=expected_params,
                             headers={'Accept': 'application/json'})

    def test_post_error(self):
        url = "test"
        params = {"query": "ceilometer_image_size{publisher='localhost'}"}

        return_value = self.BadResponse()
        with mock.patch.object(requests.Session, 'post',
                               return_value=return_value):
            c = client.PrometheusAPIClient("localhost:9090")
            self.assertRaises(client.PrometheusAPIClientError,
                              c._post, url, params)

        return_value = self.NoContentResponse()
        with mock.patch.object(requests.Session, 'post',
                               return_value=return_value):
            c = client.PrometheusAPIClient("localhost:9090")
            self.assertRaises(client.PrometheusAPIClientError,
                              c._post, url, params)


class PrometheusAPIClientQueryTest(PrometheusAPIClientTestBase):
    def setUp(self):
        super().setUp()

    class GoodQueryResponse(PrometheusAPIClientTestBase.GoodResponse):
        def __init__(self):
            super().__init__()
            self.result1 = {
                "metric": {
                    "__name__": "test1",
                },
                "value": [103254, "1"]
            }
            self.result2 = {
                "metric": {
                    "__name__": "test2",
                },
                "value": [103255, "2"]
            }
            self.expected = [client.PrometheusMetric(self.result1),
                             client.PrometheusMetric(self.result2)]

        def json(self):
            return {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": [self.result1, self.result2]
                }
            }

    class EmptyQueryResponse(PrometheusAPIClientTestBase.GoodResponse):
        def __init__(self):
            super().__init__()
            self.expected = []

        def json(self):
            return {
                "status": "success",
                "data": {
                    "resultType": "vector",
                    "result": []
                }
            }

    def test_query(self):
        query = "ceilometer_image_size{publisher='localhost.localdomain'}"

        matcher = MetricListMatcher(self.GoodQueryResponse().expected)
        return_value = self.GoodQueryResponse().json()
        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            ret = c.query(query)

            m.assert_called_with("query", {"query": query})
            self.assertThat(ret, matcher)

        return_value = self.EmptyQueryResponse().json()
        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            ret = c.query(query)

            self.assertEqual(self.EmptyQueryResponse().expected, ret)

    def test_query_error(self):
        query = "ceilometer_image_size{publisher='localhost.localdomain'}"
        client_exception = client.PrometheusAPIClientError(self.BadResponse())

        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               side_effect=client_exception):
            c = client.PrometheusAPIClient("localhost:9090")

            self.assertRaises(client.PrometheusAPIClientError, c.query, query)


class PrometheusAPIClientSeriesTest(PrometheusAPIClientTestBase):
    def setUp(self):
        super().setUp()

    class GoodSeriesResponse(PrometheusAPIClientTestBase.GoodResponse):
        def __init__(self):
            super().__init__()
            self.data = [{
                "__name__": "up",
                "job": "prometheus",
                "instance": "localhost:9090"
            }, {
                "__name__": "up",
                "job": "node",
                "instance": "localhost:9091"
            }, {
                "__name__": "process_start_time_seconds",
                "job": "prometheus",
                "instance": "localhost:9090"
            }]
            self.expected = self.data

        def json(self):
            return {
                "status": "success",
                "data": self.data
            }

    class EmptySeriesResponse(PrometheusAPIClientTestBase.GoodResponse):
        def __init__(self):
            super().__init__()
            self.data = []
            self.expected = self.data

        def json(self):
            return {
                "status": "success",
                "data": self.data
            }

    def test_series(self):
        matches = ["up", "ceilometer_image_size"]

        return_value = self.GoodSeriesResponse().json()
        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            ret = c.series(matches)

            m.assert_called_with("series", {"match[]": matches})
            self.assertEqual(ret, self.GoodSeriesResponse().data)

        return_value = self.EmptySeriesResponse().json()
        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            ret = c.series(matches)

            m.assert_called_with("series", {"match[]": matches})
            self.assertEqual(ret, self.EmptySeriesResponse().data)

    def test_series_error(self):
        matches = ["up", "ceilometer_image_size"]
        client_exception = client.PrometheusAPIClientError(self.BadResponse())

        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               side_effect=client_exception):
            c = client.PrometheusAPIClient("localhost:9090")

            self.assertRaises(client.PrometheusAPIClientError,
                              c.series,
                              matches)


class PrometheusAPIClientLabelsTest(PrometheusAPIClientTestBase):
    def setUp(self):
        super().setUp()

    class GoodLabelsResponse(PrometheusAPIClientTestBase.GoodResponse):
        def __init__(self):
            super().__init__()
            self.labels = ["up", "job", "project_id"]

        def json(self):
            return {
                "status": "success",
                "data": self.labels
            }

    def test_labels(self):
        return_value = self.GoodLabelsResponse().json()
        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            ret = c.labels()

            m.assert_called_with("labels")
            self.assertEqual(ret, self.GoodLabelsResponse().labels)

    def test_labels_error(self):
        client_exception = client.PrometheusAPIClientError(self.BadResponse())
        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               side_effect=client_exception):
            c = client.PrometheusAPIClient("localhost:9090")

            self.assertRaises(client.PrometheusAPIClientError, c.labels)


class PrometheusAPIClientLabelValuesTest(PrometheusAPIClientTestBase):
    def setUp(self):
        super().setUp()

    class GoodLabelValuesResponse(PrometheusAPIClientTestBase.GoodResponse):
        def __init__(self):
            super().__init__()
            self.values = ["prometheus", "some_other_value"]

        def json(self):
            return {
                "status": "success",
                "data": self.values
            }

    class EmptyLabelValuesResponse(PrometheusAPIClientTestBase.GoodResponse):
        def __init__(self):
            super().__init__()
            self.values = []

        def json(self):
            return {
                "status": "success",
                "data": self.values
            }

    def test_label_values(self):
        label_name = "job"

        return_value = self.GoodLabelValuesResponse().json()
        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            ret = c.label_values(label_name)

            m.assert_called_with(f"label/{label_name}/values")
            self.assertEqual(ret, self.GoodLabelValuesResponse().values)

        return_value = self.EmptyLabelValuesResponse().json()
        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            ret = c.label_values(label_name)

            m.assert_called_with(f"label/{label_name}/values")
            self.assertEqual(ret, self.EmptyLabelValuesResponse().values)

    def test_label_values_error(self):
        label_name = "job"
        client_exception = client.PrometheusAPIClientError(self.BadResponse())

        with mock.patch.object(client.PrometheusAPIClient, '_get',
                               side_effect=client_exception):
            c = client.PrometheusAPIClient("localhost:9090")

            self.assertRaises(client.PrometheusAPIClientError,
                              c.label_values,
                              label_name)


class PrometheusAPIClientDeleteTest(PrometheusAPIClientTestBase):
    def setUp(self):
        super().setUp()

    class GoodDeleteResponse(PrometheusAPIClientTestBase.NoContentResponse):
        pass

    def test_delete(self):
        matches = ["{job='prometheus'}", "up"]
        start = 1
        end = 12
        resp = self.GoodDeleteResponse()
        post_exception = client.PrometheusAPIClientError(resp)

        with mock.patch.object(client.PrometheusAPIClient, '_post',
                               side_effect=post_exception) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            # _post is expected to raise an exception. It's expected
            # that the exception is caught inside delete. This
            # test should run without exception getting out of delete
            try:
                c.delete(matches, start, end)
            except Exception as ex:  # noqa: B902
                self.fail("Exception risen by delete: " + ex)

            m.assert_called_with("admin/tsdb/delete_series",
                                 {"match[]": matches,
                                  "start": start,
                                  "end": end})

    def test_delete_error(self):
        matches = ["{job='prometheus'}", "up"]
        client_exception = client.PrometheusAPIClientError(self.BadResponse())

        with mock.patch.object(client.PrometheusAPIClient, '_post',
                               side_effect=client_exception):
            c = client.PrometheusAPIClient("localhost:9090")

            self.assertRaises(client.PrometheusAPIClientError,
                              c.delete,
                              matches)


class PrometheusAPIClientCleanTombstonesTest(PrometheusAPIClientTestBase):
    def setUp(self):
        super().setUp()

    class GoodCleanTombResponse(PrometheusAPIClientTestBase.NoContentResponse):
        pass

    def test_clean_tombstones(self):
        resp = self.GoodCleanTombResponse()
        post_exception = client.PrometheusAPIClientError(resp)

        with mock.patch.object(client.PrometheusAPIClient, '_post',
                               side_effect=post_exception) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            # _post is expected to raise an exception. It's expected
            # that the exception is caught inside clean_tombstones. This
            # test should run without exception getting out of clean_tombstones
            try:
                c.clean_tombstones()
            except Exception as ex:  # noqa: B902
                self.fail("Exception risen by clean_tombstones: " + ex)

            m.assert_called_with("admin/tsdb/clean_tombstones")

    def test_snapshot_error(self):
        client_exception = client.PrometheusAPIClientError(self.BadResponse())

        with mock.patch.object(client.PrometheusAPIClient, '_post',
                               side_effect=client_exception):
            c = client.PrometheusAPIClient("localhost:9090")

            self.assertRaises(client.PrometheusAPIClientError,
                              c.clean_tombstones)


class PrometheusAPIClientSnapshotTest(PrometheusAPIClientTestBase):
    def setUp(self):
        super().setUp()

    class GoodSnapshotResponse(PrometheusAPIClientTestBase.NoContentResponse):
        def __init__(self):
            super().__init__()
            self.filename = "somefilename"

        def json(self):
            return {
                "status": "success",
                "data": {
                    "name": self.filename
                }
            }

    def test_snapshot(self):
        return_value = self.GoodSnapshotResponse().json()
        with mock.patch.object(client.PrometheusAPIClient, '_post',
                               return_value=return_value) as m:
            c = client.PrometheusAPIClient("localhost:9090")
            ret = c.snapshot()

            m.assert_called_with("admin/tsdb/snapshot")
            self.assertEqual(ret, self.GoodSnapshotResponse().filename)

    def test_snapshot_error(self):
        client_exception = client.PrometheusAPIClientError(self.BadResponse())

        with mock.patch.object(client.PrometheusAPIClient, '_post',
                               side_effect=client_exception):
            c = client.PrometheusAPIClient("localhost:9090")

            self.assertRaises(client.PrometheusAPIClientError,
                              c.snapshot)
