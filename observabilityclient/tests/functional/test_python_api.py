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

from observabilityclient.tests.functional import base

import time


class PythonAPITestFunctionalRBACDisabled(base.PythonAPITestCase):
    def test_list(self):
        ret = self.client.query.list(disable_rbac=True)

        self.assertIn("up", ret)

    def test_show(self):
        ret = self.client.query.show("up", disable_rbac=True)

        for metric in ret:
            self.assertEqual("up", metric.labels["__name__"])
            self.assertEqual("1", metric.value)

    def test_query(self):
        ret = self.client.query.query("up", disable_rbac=True)

        for metric in ret:
            self.assertEqual("up", metric.labels["__name__"])
            self.assertEqual("1", metric.value)


class PythonAPITestFunctionalRBACEnabled(base.PythonAPITestCase):
    def test_list(self):
        ret = self.client.query.list(disable_rbac=False)

        self.assertIn("ceilometer_image_size", ret)
        self.assertNotIn("up", ret)

    def test_show(self):
        ret = self.client.query.show("ceilometer_image_size",
                                     disable_rbac=False)

        for metric in ret:
            self.assertEqual("ceilometer_image_size",
                             metric.labels["__name__"])
            self.assertEqual("custom",
                             metric.labels["job"])

    def test_query(self):
        ret = self.client.query.query("ceilometer_image_size",
                                      disable_rbac=False)

        for metric in ret:
            self.assertEqual("ceilometer_image_size",
                             metric.labels["__name__"])
            self.assertEqual("custom", metric.labels["job"])


class PythonAPITestFunctionalAdminCommands(base.PythonAPITestCase):
    def test_delete(self):
        now = time.time()
        metric_name = "prometheus_build_info"
        query = f"{metric_name}@{now}"

        query_before = self.client.query.query(query, disable_rbac=True)

        for metric in query_before:
            self.assertEqual(metric_name, metric.labels["__name__"])

        self.client.query.delete(metric_name)

        query_after = self.client.query.query(query, disable_rbac=True)
        self.assertEqual([], query_after)

    def test_clean_tombstones(self):
        # NOTE(jwysogla) There is not much to check here
        # except for the fact, that the command doesn't
        # raise an exception. Prometheus doesn't send any
        # data back and we don't have a reliable way to query
        # prometheus that this command did something.
        self.client.query.clean_tombstones()

    def test_snapshot(self):
        ret = self.client.query.snapshot()
        self.assertIn(time.strftime("%Y%m%d"), ret)
