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

import logging
import os

import yaml

from observabilityclient.prometheus_client import PrometheusAPIClient


DEFAULT_CONFIG_LOCATIONS = [os.environ["HOME"] + "/.config/openstack/",
                            "/etc/openstack/"]
CONFIG_FILE_NAME = "prometheus.yaml"
LOG = logging.getLogger(__name__)


class ConfigurationError(Exception):
    pass


def get_config_file():
    if os.path.exists(CONFIG_FILE_NAME):
        LOG.debug("Using %s as prometheus configuration", CONFIG_FILE_NAME)
        return open(CONFIG_FILE_NAME, "r")
    for path in DEFAULT_CONFIG_LOCATIONS:
        full_filename = path + CONFIG_FILE_NAME
        if os.path.exists(full_filename):
            LOG.debug("Using %s as prometheus configuration", full_filename)
            return open(full_filename, "r")
    return None


def get_prometheus_client():
    host = None
    port = None
    conf_file = get_config_file()
    if conf_file is not None:
        conf = yaml.safe_load(conf_file)
        if 'host' in conf:
            host = conf['host']
        if 'port' in conf:
            port = conf['port']
        conf_file.close()

    # NOTE(jwysogla): We allow to overide the prometheus.yaml by
    #                 the environment variables
    if 'PROMETHEUS_HOST' in os.environ:
        host = os.environ['PROMETHEUS_HOST']
    if 'PROMETHEUS_PORT' in os.environ:
        port = os.environ['PROMETHEUS_PORT']
    if host is None or port is None:
        raise ConfigurationError("Can't find prometheus host and "
                                 "port configuration.")
    return PrometheusAPIClient(f"{host}:{port}")


def get_client(obj):
    return obj.app.client_manager.observabilityclient


def format_labels(d: dict) -> str:
    def replace_doubled_quotes(string):
        if "''" in string:
            string = string.replace("''", "'")
        if '""' in string:
            string = string.replace('""', '"')
        return string

    ret = ""
    for key, value in d.items():
        ret += "{}='{}', ".format(key, value)
    ret = ret[0:-2]
    old = ""
    while ret != old:
        old = ret
        ret = replace_doubled_quotes(ret)
    return ret


def metrics2cols(m):
    cols = []
    fields = []
    first = True
    for metric in m:
        row = []
        for key, value in metric.labels.items():
            if first:
                cols.append(key)
            row.append(value)
        if first:
            cols.append("value")
        row.append(metric.value)
        fields.append(row)
        first = False
    return cols, fields
