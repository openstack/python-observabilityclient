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
        self.rbac.disable_rbac = False

        self.rbac.client.query.list = lambda disable_rbac: [
            'test_query',
            'cpu_temp_celsius',
            'http_requests',
            'test:query:with:colon:',
            'test_query_with_digit1',
            'method_code:http_errors:rate5m',
            'method:http_requests:rate5m'
        ]
        self.test_cases = [
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
                "test_query{somelabel='unicode{}{ \t/-_#~$&%\\'}",

                (f"test_query{{somelabel='unicode{{}}{{ \t/-_#~$&%\\', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "test_query{somelabel='s p a c e'}",

                (f"test_query{{somelabel='s p a c e', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "test_query{somelabel='doublequotes\"'}",

                (f"test_query{{somelabel='doublequotes\"', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                'test_query{somelabel="singlequotes\'"}',

                (f'test_query{{somelabel="singlequotes\'", '
                 f'project=\'{self.rbac.project_id}\'}}')
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
            ), (
                "round(test_query{label='something'},5)",

                (f"round(test_query{{label='something', "
                 f"project='{self.rbac.project_id}'}},5)")
            ), (
                "sum by (foo) (test_query{label_1='baz'})",

                (f"sum by (foo) (test_query{{label_1='baz', "
                 f"project='{self.rbac.project_id}'}})")
            ), (
                "test_query{} + avg without (application, group) "
                "(test:query:with:colon:{label='baz'})",

                (f"test_query{{project='{self.rbac.project_id}'}} + "
                 f"avg without (application, group) "
                 f"(test:query:with:colon:{{label='baz', "
                 f"project='{self.rbac.project_id}'}})")
            ), (
                "test_query{label1='foo'} + on (label1,label2) "
                "avg by (label3) (test_query_with_digit1{label='baz',"
                "label1='foo',label2='bar'})",

                (f"test_query{{label1='foo', "
                 f"project='{self.rbac.project_id}'}} "
                 f"+ on (label1,label2) avg by (label3) "
                 f"(test_query_with_digit1{{label='baz',"
                 f"label1='foo',label2='bar', "
                 f"project='{self.rbac.project_id}'}})")
            ), (
                "{label='no-metric'}",

                (f"{{label='no-metric', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "http_requests{environment=~"
                "'staging|testing|development',method!='GET'}",

                (f"http_requests{{environment=~"
                 f"'staging|testing|development',method!='GET', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "http_requests{replica!='rep-a',replica=~'rep.*'}",

                (f"http_requests{{replica!='rep-a',replica=~'rep.*', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "{__name__=~'job:.*'}",

                (f"{{__name__=~'job:.*', "
                 f"project='{self.rbac.project_id}'}}")
            ), (
                "http_requests offset 5m",

                (f"http_requests"
                 f"{{project='{self.rbac.project_id}'}} "
                 f"offset 5m")
            ), (
                "rate(http_requests[5m] offset -1w)",

                (f"rate(http_requests"
                 f"{{project='{self.rbac.project_id}'}}"
                 f"[5m] offset -1w)")
            ), (
                "http_requests @ 1609746000",

                (f"http_requests"
                 f"{{project='{self.rbac.project_id}'}} "
                 f"@ 1609746000")
            ), (
                "histogram_quantile(0.9, sum by (le) "
                "(rate(http_requests[10m])))",

                (f"histogram_quantile(0.9, sum by (le) "
                 f"(rate(http_requests"
                 f"{{project='{self.rbac.project_id}'}}"
                 f"[10m])))"
                 )
            )
        ]

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
        for query, expected in self.test_cases:
            ret = self.rbac.enrich_query(query)
            self.assertEqual(expected, ret)

    def test_enrich_query_disable(self):
        for query, expected in self.test_cases:
            ret = self.rbac.enrich_query(query, disable_rbac=True)
            self.assertEqual(query, ret)

    def test_append_rbac(self):
        query = "test_query"
        expected = f"{query}{{project='{self.rbac.project_id}'}}"
        ret = self.rbac.append_rbac(query)
        self.assertEqual(expected, ret)

    def test_append_rbac_disable(self):
        query = "test_query"
        expected = query
        ret = self.rbac.append_rbac(query, disable_rbac=True)
        self.assertEqual(expected, ret)
