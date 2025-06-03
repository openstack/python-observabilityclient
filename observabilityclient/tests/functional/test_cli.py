#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from observabilityclient.tests.functional import base
import time


class CliTestFunctionalRBACNOOP(base.CliTestCase):
    """Functional tests for cli commands testing RBAC option."""

    def test_list(self):
        for cmdstr in ('metric list', 'metric list --disable-rbac'):
            cmd_output = self.openstack(
                cmdstr,
                parse_output=True,
            )
            name_list = [item.get('metric_name') for item in cmd_output]
            self.assertIn(
                'ceilometer_image_size',
                name_list
            )
            self.assertIn(
                'up',
                name_list
            )

    def test_show(self):
        for cmdstr in ('metric show up', 'metric show up --disable-rbac'):
            cmd_output = self.openstack(
                cmdstr,
                parse_output=True,
            )
            for metric in cmd_output:
                self.assertEqual(
                    "up",
                    metric["__name__"]
                )
                self.assertEqual(
                    "1",
                    metric["value"]
                )

    def test_query(self):
        for cmdstr in ('metric query up', 'metric query up --disable-rbac'):
            cmd_output = self.openstack(
                cmdstr,
                parse_output=True,
            )
            for metric in cmd_output:
                self.assertEqual(
                    "up",
                    metric["__name__"]
                )
                self.assertEqual(
                    "1",
                    metric["value"]
                )


class CliTestFunctionalAdminCommands(base.CliTestCase):
    """Functional tests for cli admin commands."""

    def test_delete(self):
        test_start_time = int(time.time())
        query_before = self.openstack(
            f'metric query prometheus_ready@{test_start_time} --disable-rbac',
            parse_output=True,
        )

        values = [item.get("__name__") for item in query_before]
        # Check, that the metric is present before the deletion
        self.assertIn(
            "prometheus_ready",
            values
        )

        self.openstack(
            'metric delete prometheus_ready --disable-rbac',
            parse_output=False,
        )

        query_after = self.openstack(
            f'metric query prometheus_ready@{test_start_time} --disable-rbac',
            parse_output=True,
        )
        values = [item.get("__name__") for item in query_after]
        # Check, that the metric is not present after the deletion
        self.assertNotIn(
            "prometheus_ready",
            values
        )

    def test_clean_tombstones(self):
        # NOTE(jwysogla) There is not much to check here
        # except for the fact, that the command doesn't
        # raise an exception. Prometheus doesn't send any
        # data back and we don't have a reliable way to query
        # prometheus that this command did something.
        self.openstack('metric clean-tombstones')

    def test_snapshot(self):
        cmd_output = self.openstack(
            'metric snapshot',
            parse_output=True,
        )
        for name in cmd_output:
            self.assertInOutput(
                time.strftime('%Y%m%d'),
                name.get("Snapshot file name")
            )
