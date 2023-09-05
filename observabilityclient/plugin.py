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

"""OpenStackClient Plugin interface."""

from osc_lib import utils


DEFAULT_API_VERSION = '1'
API_NAME = 'observabilityclient'
API_VERSION_OPTION = 'os_observabilityclient_api_version'
API_VERSIONS = {
    '1': 'observabilityclient.v1.client.Client',
}


def make_client(instance):
    """Return a client to the ClientManager.

    Called to instantiate the requested client version.  instance has
    any available auth info that may be required to prepare the client.

    :param ClientManager instance: The ClientManager that owns the new client
    """
    observability_client = utils.get_client_class(
        API_NAME,
        instance._api_version[API_NAME],
        API_VERSIONS)

    client = observability_client(session=instance.session,
                                  adapter_options={
                                      'interface': instance.interface,
                                      'region_name': instance.region_name
                                  })
    return client


def build_option_parser(parser):
    """Add global options.

    Called from openstackclient.shell.OpenStackShell.__init__()
    after the builtin parser has been initialized.  This is
    where a plugin can add global options such as an API version setting.

    :param argparse.ArgumentParser parser: The parser object that has been
        initialized by OpenStackShell.
    """
    parser.add_argument(
        '--os-observability-api-version',
        metavar='<observability-api-version>',
        help='Observability Plugin API version, default='
             + DEFAULT_API_VERSION
             + ' (Env: OS_OSCPLUGIN_API_VERSION)')
    return parser
