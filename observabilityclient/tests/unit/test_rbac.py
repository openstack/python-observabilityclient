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

from keystoneauth1.exceptions.auth_plugins import MissingAuthPlugin
from keystoneauth1 import session
import testtools

from observabilityclient.v1 import rbac


class RbacTest(testtools.TestCase):
    def setUp(self):
        super(RbacTest, self).setUp()
        self.rbac = rbac.Rbac(mock.Mock(), mock.Mock())
        self.rbac.project_id = "secret_id"
        self.rbac.default_labels = {
            "project": self.rbac.project_id
        }

    def test_constructor(self):
        with mock.patch.object(session.Session, 'get_project_id',
                               return_value="123"):
            r = rbac.Rbac("client", session.Session(), False)
            self.assertEqual(r.project_id, "123")
            self.assertEqual(r.default_labels, {
                "project": "123"
            })

    def test_constructor_error(self):
        with mock.patch.object(session.Session, 'get_project_id',
                               side_effect=MissingAuthPlugin()):
            r = rbac.Rbac("client", session.Session(), False)
            self.assertIsNone(r.project_id)

    def test_enrich_query(self):
        test_cases = [
            (
                "test_query",
                f"test_query{{project='{self.rbac.project_id}'}}"
            ), (
                "test_query{somelabel='value'}",

                (f"test_query{{somelabel='value', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "test_query{somelabel='value', label2='value2'}",

                (f"test_query{{somelabel='value', label2='value2', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "test_query{somelabel='unicode{}{'}",

                (f"test_query{{somelabel='unicode{{}}{{', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "test_query{doesnt_match_regex!~'regex'}",

                (f"test_query{{doesnt_match_regex!~'regex', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "delta(cpu_temp_celsius{host='zeus'}[2h]) - "
                "sum(http_requests) + "
                "sum(http_requests{instance=~'.*'}) + "
                "sum(http_requests{or_regex=~'smth1|something2|3'})",

                (f"delta(cpu_temp_celsius{{host='zeus', "
                 f"project='{self.rbac.project_id}'}}[2h]) - "
                 f"sum(http_requests"
                 f"{{project='{self.rbac.project_id}'}}) + "
                 f"sum(http_requests{{instance=~'.*', "
                 f"project='{self.rbac.project_id}'}}) + "
                 f"sum(http_requests{{or_regex=~'smth1|something2|3', "
                 f"project='{self.rbac.project_id}'}})")
            )
        ]

        self.rbac.client.query.list = lambda disable_rbac: ['test_query',
                                                            'cpu_temp_celsius',
                                                            'http_requests']

        for query, expected in test_cases:
            ret = self.rbac.enrich_query(query)
            self.assertEqual(ret, expected)

    def test_enrich_query_disable(self):
        test_cases = [
            (
                "test_query",
                "test_query"
            ), (
                "test_query{somelabel='value'}",
                "test_query{somelabel='value'}"
            ), (
                "test_query{somelabel='value', label2='value2'}",
                "test_query{somelabel='value', label2='value2'}"
            ), (
                "test_query{somelabel='unicode{}{'}",
                "test_query{somelabel='unicode{}{'}"
            ), (
                "test_query{doesnt_match_regex!~'regex'}",
                "test_query{doesnt_match_regex!~'regex'}",
            ), (
                "delta(cpu_temp_celsius{host='zeus'}[2h]) - "
                "sum(http_requests) + "
                "sum(http_requests{instance=~'.*'}) + "
                "sum(http_requests{or_regex=~'smth1|something2|3'})",

                "delta(cpu_temp_celsius{host='zeus'}[2h]) - "
                "sum(http_requests) + "
                "sum(http_requests{instance=~'.*'}) + "
                "sum(http_requests{or_regex=~'smth1|something2|3'})"
            )
        ]

        self.rbac.client.query.list = lambda disable_rbac: ['test_query',
                                                            'cpu_temp_celsius',
                                                            'http_requests']
        for query, expected in test_cases:
            ret = self.rbac.enrich_query(query, disable_rbac=True)
            self.assertEqual(ret, query)

    def test_append_rbac(self):
        query = "test_query"
        expected = f"{query}{{project='{self.rbac.project_id}'}}"
        ret = self.rbac.append_rbac(query)
        self.assertEqual(ret, expected)

    def test_append_rbac_disable(self):
        query = "test_query"
        expected = query
        ret = self.rbac.append_rbac(query, disable_rbac=True)
        self.assertEqual(ret, expected)
