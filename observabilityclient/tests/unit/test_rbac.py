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

from observabilityclient import rbac


class PromQLRbacTest(testtools.TestCase):
    def setUp(self):
        super(PromQLRbacTest, self).setUp()
        self.project_id = "project123"
        self.rbac = rbac.PromQLRbac(mock.Mock(), mock.Mock())
        self.rbac.labels = {
            "project": "project123"
        }
        self.rbac.client.label_values = lambda label: [
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
                f"test_query{{project='{self.project_id}'}}"
            ), (
                "test_query{somelabel='value'}",

                (f"test_query{{somelabel='value', "
                 f"project='{self.project_id}'}}")
            ), (
                "test_query{somelabel='value', label2='value2'}",

                (f"test_query{{somelabel='value', label2='value2', "
                 f"project='{self.project_id}'}}")
            ), (
                "test_query{somelabel='unicode{}{ \t/-_#~$&%\\'}",

                (f"test_query{{somelabel='unicode{{}}{{ \t/-_#~$&%\\', "
                 f"project='{self.project_id}'}}")
            ), (
                "test_query{somelabel='s p a c e'}",

                (f"test_query{{somelabel='s p a c e', "
                 f"project='{self.project_id}'}}")
            ), (
                "test_query{somelabel='doublequotes\"'}",

                (f"test_query{{somelabel='doublequotes\"', "
                 f"project='{self.project_id}'}}")
            ), (
                'test_query{somelabel="singlequotes\'"}',

                (f'test_query{{somelabel="singlequotes\'", '
                 f'project=\'{self.project_id}\'}}')
            ), (
                "test_query{doesnt_match_regex!~'regex'}",

                (f"test_query{{doesnt_match_regex!~'regex', "
                 f"project='{self.project_id}'}}")
            ), (
                "delta(cpu_temp_celsius{host='zeus'}[2h]) - "
                "sum(http_requests) + "
                "sum(http_requests{instance=~'.*'}) + "
                "sum(http_requests{or_regex=~'smth1|something2|3'})",

                (f"delta(cpu_temp_celsius{{host='zeus', "
                 f"project='{self.project_id}'}}[2h]) - "
                 f"sum(http_requests"
                 f"{{project='{self.project_id}'}}) + "
                 f"sum(http_requests{{instance=~'.*', "
                 f"project='{self.project_id}'}}) + "
                 f"sum(http_requests{{or_regex=~'smth1|something2|3', "
                 f"project='{self.project_id}'}})")
            ), (
                "round(test_query{label='something'},5)",

                (f"round(test_query{{label='something', "
                 f"project='{self.project_id}'}},5)")
            ), (
                "sum by (foo) (test_query{label_1='baz'})",

                (f"sum by (foo) (test_query{{label_1='baz', "
                 f"project='{self.project_id}'}})")
            ), (
                "test_query{} + avg without (application, group) "
                "(test:query:with:colon:{label='baz'})",

                (f"test_query{{project='{self.project_id}'}} + "
                 f"avg without (application, group) "
                 f"(test:query:with:colon:{{label='baz', "
                 f"project='{self.project_id}'}})")
            ), (
                "test_query{label1='foo'} + on (label1,label2) "
                "avg by (label3) (test_query_with_digit1{label='baz',"
                "label1='foo',label2='bar'})",

                (f"test_query{{label1='foo', "
                 f"project='{self.project_id}'}} "
                 f"+ on (label1,label2) avg by (label3) "
                 f"(test_query_with_digit1{{label='baz',"
                 f"label1='foo',label2='bar', "
                 f"project='{self.project_id}'}})")
            ), (
                "{label='no-metric'}",

                (f"{{label='no-metric', "
                 f"project='{self.project_id}'}}")
            ), (
                "http_requests{environment=~"
                "'staging|testing|development',method!='GET'}",

                (f"http_requests{{environment=~"
                 f"'staging|testing|development',method!='GET', "
                 f"project='{self.project_id}'}}")
            ), (
                "http_requests{replica!='rep-a',replica=~'rep.*'}",

                (f"http_requests{{replica!='rep-a',replica=~'rep.*', "
                 f"project='{self.project_id}'}}")
            ), (
                "{__name__=~'job:.*'}",

                (f"{{__name__=~'job:.*', "
                 f"project='{self.project_id}'}}")
            ), (
                "http_requests offset 5m",

                (f"http_requests"
                 f"{{project='{self.project_id}'}} "
                 f"offset 5m")
            ), (
                "rate(http_requests[5m] offset -1w)",

                (f"rate(http_requests"
                 f"{{project='{self.project_id}'}}"
                 f"[5m] offset -1w)")
            ), (
                "http_requests @ 1609746000",

                (f"http_requests"
                 f"{{project='{self.project_id}'}} "
                 f"@ 1609746000")
            ), (
                "histogram_quantile(0.9, sum by (le) "
                "(rate(http_requests[10m])))",

                (f"histogram_quantile(0.9, sum by (le) "
                 f"(rate(http_requests"
                 f"{{project='{self.project_id}'}}"
                 f"[10m])))"
                 )
            )
        ]

    def test_constructor(self):
        r = rbac.PromQLRbac("client", "123")
        self.assertEqual(r.labels, {
            "project": "123"
        })

    def test_modify_query(self):
        for query, expected in self.test_cases:
            ret = self.rbac.modify_query(query)
            self.assertEqual(expected, ret)

    def test_append_rbac_labels(self):
        query = "test_query"
        expected = f"{query}{{project='{self.project_id}'}}"
        ret = self.rbac.append_rbac_labels(query)
        self.assertEqual(expected, ret)
