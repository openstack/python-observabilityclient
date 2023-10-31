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

from cliff import lister

from observabilityclient.i18n import _
from observabilityclient.utils import metric_utils
from observabilityclient.v1 import base


class List(base.ObservabilityBaseCommand, lister.Lister):
    """Query prometheus for list of all metrics."""

    def take_action(self, parsed_args):
        client = metric_utils.get_client(self)
        metrics = client.query.list(disable_rbac=parsed_args.disable_rbac)
        return ["metric_name"], [[m] for m in metrics]


class Show(base.ObservabilityBaseCommand, lister.Lister):
    """Query prometheus for the current value of metric."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'name',
            help=_("Name of the metric to show"))
        return parser

    def take_action(self, parsed_args):
        client = metric_utils.get_client(self)
        metric = client.query.show(parsed_args.name,
                                   disable_rbac=parsed_args.disable_rbac)
        ret = metric_utils.metrics2cols(metric)
        return ret


class Query(base.ObservabilityBaseCommand, lister.Lister):
    """Query prometheus with a custom query string."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'query',
            help=_("Custom PromQL query"))
        return parser

    def take_action(self, parsed_args):
        client = metric_utils.get_client(self)
        metric = client.query.query(parsed_args.query,
                                    disable_rbac=parsed_args.disable_rbac)
        ret = metric_utils.metrics2cols(metric)
        return ret


class Delete(base.ObservabilityBaseCommand):
    """Delete data for a selected series and time range."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            'matches',
            action="append",
            nargs='+',
            help=_("Series selector, that selects the series to delete. "
                   "Specify multiple selectors delimited by space to "
                   "delete multiple series."))
        parser.add_argument(
            '--start',
            help=_("Start timestamp in rfc3339 or unix timestamp. "
                   "Defaults to minimum possible timestamp."))
        parser.add_argument(
            '--end',
            help=_("End timestamp in rfc3339 or unix timestamp. "
                   "Defaults to maximum possible timestamp."))
        return parser

    def take_action(self, parsed_args):
        client = metric_utils.get_client(self)
        return client.query.delete(parsed_args.matches,
                                   parsed_args.start,
                                   parsed_args.end)


class CleanTombstones(base.ObservabilityBaseCommand):
    """Remove deleted data from disk and clean up the existing tombstones."""

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        return parser

    def take_action(self, parsed_args):
        client = metric_utils.get_client(self)
        return client.query.clean_tombstones()


class Snapshot(base.ObservabilityBaseCommand, lister.Lister):
    def take_action(self, parsed_args):
        client = metric_utils.get_client(self)
        ret = client.query.snapshot()
        return ["Snapshot file name"], [[ret]]
