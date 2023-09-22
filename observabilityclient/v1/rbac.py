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

import re

from keystoneauth1.exceptions.auth_plugins import MissingAuthPlugin

from observabilityclient.utils.metric_utils import format_labels


class ObservabilityRbacError(Exception):
    pass


class Rbac(object):
    def __init__(self, client, session, disable_rbac=False):
        self.client = client
        self.session = session
        self.disable_rbac = disable_rbac
        try:
            self.project_id = self.session.get_project_id()
            self.default_labels = {
                "project": self.project_id
            }
            self.rbac_init_successful = True
        except MissingAuthPlugin:
            self.project_id = None
            self.default_labels = {
                "project": "no-project"
            }
            self.rbac_init_successful = False

    def _find_label_value_end(self, query, start, quote_char):
        end = start
        while (end == start or
               query[end - 1] == '\\'):
            # Looking for first unescaped quotes
            end = query.find(quote_char, end + 1)
        # returns the quote position or -1
        return end

    def _find_match_operator(self, query, start):
        eq_sign_pos = query.find('=', start)
        tilde_pos = query.find('~', start)
        if eq_sign_pos == -1:
            return tilde_pos
        if tilde_pos == -1:
            return eq_sign_pos
        return min(eq_sign_pos, tilde_pos)

    def _find_label_pair_end(self, query, start):
        match_operator_pos = self._find_match_operator(query, start)
        quote_char = "'"
        quote_start_pos = query.find(quote_char, match_operator_pos)
        if quote_start_pos == -1:
            quote_char = '"'
            quote_start_pos = query.find(quote_char, match_operator_pos)
        end = self._find_label_value_end(query, quote_start_pos, quote_char)
        # returns the pair end or -1
        return end

    def _find_label_section_end(self, query, start):
        nearest_curly_brace_pos = None
        while nearest_curly_brace_pos != -1:
            pair_end = self._find_label_pair_end(query, start)
            nearest_curly_brace_pos = query.find("}", pair_end)
            nearest_match_operator_pos = self._find_match_operator(query,
                                                                   pair_end)
            if (nearest_curly_brace_pos < nearest_match_operator_pos or
                    nearest_match_operator_pos == -1):
                # If we have "}" before the nearest "=" or "~",
                # then we must be at the end of the label section
                # and the "=" or "~" is a part of the next section.
                return nearest_curly_brace_pos
            start = pair_end
        return -1

    def enrich_query(self, query, disable_rbac=False):
        """Add rbac labels to queries.

        :param query: The query to enrich
        :type query: str
        :param disable_rbac: Disables rbac injection if set to True
        :type disable_rbac: boolean
        """
        # TODO(jwysogla): This should be properly tested
        if disable_rbac:
            return query
        labels = self.default_labels

        # We need to get all metric names, no matter the rbac
        metric_names = self.client.query.list(disable_rbac=False)

        # We need to detect the locations of metric names
        # inside the query
        # NOTE the locations are the locations within the original query
        name_end_locations = []
        for name in metric_names:
            # Regex for a metric name is: [a-zA-Z_:][a-zA-Z0-9_:]*
            # We need to make sure, that "name" isn't just a part
            # of a longer word, so we try to expand it by "name_regex"
            name_regex = "[a-zA-Z_:]?[a-zA-Z0-9_:]*" + name + "[a-zA-Z0-9_:]*"
            potential_names = re.finditer(name_regex, query)
            for potential_name in potential_names:
                if potential_name.group(0) == name:
                    name_end_locations.append(potential_name.end())

        name_end_locations = sorted(name_end_locations, reverse=True)
        for name_end_location in name_end_locations:
            if (name_end_location < len(query) and
               query[name_end_location] == "{"):
                # There already are some labels
                labels_end = self._find_label_section_end(query,
                                                          name_end_location)
                query = (f"{query[:labels_end]}, "
                         f"{format_labels(labels)}"
                         f"{query[labels_end:]}")
            else:
                query = (f"{query[:name_end_location]}"
                         f"{{{format_labels(labels)}}}"
                         f"{query[name_end_location:]}")
        return query

    def append_rbac(self, query, disable_rbac=False):
        """Append rbac labels to queries.

        It's a simplified and faster version of enrich_query(). This just
        appends the labels at the end of the query string. For proper handling
        of complex queries, where metric names might occure elsewhere than
        just at the end, please use the enrich_query() function.

        :param query: The query to append to
        :type query: str
        :param disable_rbac: Disables rbac injection if set to True
        :type disable_rbac: boolean
        """
        labels = self.default_labels
        if disable_rbac:
            return query
        return f"{query}{{{format_labels(labels)}}}"
