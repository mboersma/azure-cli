# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from collections import OrderedDict

from jmespath import compile as compile_jmes, Options


def aks_list_table_format(results):
    """"Format a list of managed clusters as summary results for display with "-o table"."""
    return [_aks_table_format(r) for r in results]


def aks_show_table_format(result):
    """Format a managed cluster as summary results for display with "-o table"."""
    return [_aks_table_format(result)]


def _aks_table_format(result):
    parsed = compile_jmes("""{
        name: name,
        location: location,
        resourceGroup: resourceGroup,
        kubernetesVersion: properties.kubernetesVersion,
        provisioningState: properties.provisioningState,
        fqdn: properties.fqdn
    }""")
    return parsed.search(result, Options(dict_cls=OrderedDict))


def aks_get_versions_table_format(result):
    """Format get-versions upgrade results as a summary for display with "-o table"."""
    parsed = compile_jmes("""{
        name: name,
        resourceGroup: resourceGroup,
        masterVersion: properties.controlPlaneProfile.kubernetesVersion || `unknown`,
        masterUpgrades: properties.controlPlaneProfile.upgrades || [`None available`] | sort(@) | join(`, `, @),
        nodeVersion: properties.agentPoolProfiles[0].kubernetesVersion || `unknown`,
        nodeUpgrades: properties.agentPoolProfiles[0].upgrades || [`None available`] | sort(@) | join(`, `, @)
    }""")
    return parsed.search(result, Options(dict_cls=OrderedDict))
