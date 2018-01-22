# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import tempfile
import unittest

from azure.cli.testsdk import (
    ResourceGroupPreparer, RoleBasedServicePrincipalPreparer, ScenarioTest)
from azure.cli.testsdk.checkers import StringContainCheck

# flake8: noqa

class AzureKubernetesServiceScenarioTest(ScenarioTest):

    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_default_service(self, resource_group, resource_group_location, sp_name, sp_password):
        # the simplest aks create scenario
        ssh_pubkey_file = self.generate_ssh_keys().replace('\\', '\\\\')
        aks_name = self.create_random_name('cliakstest', 16)
        dns_prefix = self.create_random_name('cliaksdns', 16)

        # create
        create_cmd = 'aks create --resource-group={} --name={} --dns-name-prefix={} --ssh-key-value={} ' \
                     '--location={} --service-principal={} --client-secret={}'
        self.cmd(
            create_cmd.format(resource_group, aks_name, dns_prefix, ssh_pubkey_file,
                              resource_group_location, sp_name, sp_password),
            checks=[
                self.exists('fqdn'),
                self.check('provisioningState', 'Succeeded')
        ])

        # list
        self.cmd('aks list -g {}'.format(resource_group), checks=[
            self.check('[0].type', 'Microsoft.ContainerService/ManagedClusters'),
            StringContainCheck(aks_name),
            StringContainCheck(resource_group)
        ])

        # list in tabular format
        self.cmd('aks list -g {} -o table'.format(resource_group), checks=[
            StringContainCheck(aks_name),
            StringContainCheck(resource_group)
        ])

        # show
        self.cmd('aks show -g {} -n {}'.format(resource_group, aks_name), checks=[
            self.check('type', 'Microsoft.ContainerService/ManagedClusters'),
            self.check('name', aks_name),
            self.check('resourceGroup', resource_group),
            self.check('agentPoolProfiles[0].count', 3),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D1_v2'),
            self.check('dnsPrefix', dns_prefix),
            self.exists('kubernetesVersion')
        ])

        # get-credentials
        fd, temp_path = tempfile.mkstemp()
        try:
            self.cmd('aks get-credentials -g {} -n {} --file {}'.format(resource_group, aks_name, temp_path))
        finally:
            os.close(fd)
            os.remove(temp_path)

        # get-credentials to stdout
        self.cmd('aks get-credentials -g {} -n {} -f -'.format(resource_group, aks_name))

        # get-credentials without directory in path
        temp_path = 'kubeconfig.tmp'
        try:
            self.cmd('aks get-credentials -g {} -n {} -f {}'.format(resource_group, aks_name, temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)
        finally:
            os.remove(temp_path)

        # scale up
        self.cmd('aks scale -g {} -n {} --node-count 5'.format(resource_group, aks_name), checks=[
            self.check('agentPoolProfiles[0].count', 5)
        ])

        # show again
        self.cmd('aks show -g {} -n {}'.format(resource_group, aks_name), checks=[
            self.check('agentPoolProfiles[0].count', 5)
        ])

        # scale down
        self.cmd('aks scale -g {} -n {} -c 1'.format(resource_group, aks_name), checks=[
            self.check('agentPoolProfiles[0].count', 1)
        ])

        # show again
        self.cmd('aks show -g {} -n {}'.format(resource_group, aks_name), checks=[
            self.check('agentPoolProfiles[0].count', 1)
        ])

        # delete
        self.cmd('aks delete -g {} -n {} -y'.format(resource_group, aks_name), checks=[
            self.is_empty()
        ])

        # show again and expect failure
        self.cmd('aks show -g {} -n {}'.format(resource_group, aks_name), expect_failure=True)

    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_service_no_wait(self, resource_group, resource_group_location, sp_name, sp_password):
        ssh_pubkey_file = self.generate_ssh_keys().replace('\\', '\\\\')
        aks_name = self.create_random_name('cliakstest', 16)
        dns_prefix = self.create_random_name('cliaksdns', 16)

        # create --no-wait
        create_cmd = 'aks create -g {} -n {} -p {} --ssh-key-value {} -l {} ' \
                     '--service-principal {} --client-secret {} --tags scenario_test --no-wait'
        self.cmd(
            create_cmd.format(resource_group, aks_name, dns_prefix, ssh_pubkey_file,
                              resource_group_location, sp_name, sp_password), checks=[
            self.is_empty()
        ])

        # wait
        self.cmd('aks wait -g {} -n {} --created'.format(resource_group, aks_name))

        # delete
        self.cmd('aks delete -g {} -n {} --yes'.format(resource_group, aks_name), checks=[
            self.is_empty()
        ])

    @ResourceGroupPreparer(random_name_length=17, name_prefix='clitest', location='eastus')
    @RoleBasedServicePrincipalPreparer()
    def test_aks_create_with_upgrade(self, resource_group, resource_group_location, sp_name, sp_password):
        ssh_pubkey_file = self.generate_ssh_keys().replace('\\', '\\\\')
        aks_name = self.create_random_name('cliakstest', 16)
        dns_prefix = self.create_random_name('cliaksdns', 16)
        original_k8s_version = '1.7.12'

        # create
        create_cmd = 'aks create -g {} -n {} --dns-name-prefix {} --ssh-key-value {} --kubernetes-version {} -l {} ' \
                     '--service-principal {} --client-secret {} -k {} -c 1'
        self.cmd(
            create_cmd.format(resource_group, aks_name, dns_prefix, ssh_pubkey_file, original_k8s_version,
                              resource_group_location, sp_name, sp_password, original_k8s_version),
            checks=[
                self.exists('fqdn'),
                self.check('provisioningState', 'Succeeded')
        ])

        # show
        self.cmd('aks show -g {} -n {}'.format(resource_group, aks_name), checks=[
            self.check('type', 'Microsoft.ContainerService/ManagedClusters'),
            self.check('name', aks_name),
            self.check('resourceGroup', resource_group),
            self.check('agentPoolProfiles[0].count', 1),
            self.check('agentPoolProfiles[0].vmSize', 'Standard_D1_v2'),
            self.check('dnsPrefix', dns_prefix),
            self.check('provisioningState', 'Succeeded'),
            self.check('kubernetesVersion', original_k8s_version)
        ])

        # get versions for upgrade
        self.cmd('aks get-versions -g {} -n {}'.format(resource_group, aks_name), checks=[
            self.exists('id'),
            self.check('resourceGroup', resource_group),
            self.check('agentPoolProfiles[0].kubernetesVersion', original_k8s_version),
            self.check('agentPoolProfiles[0].osType', 'Linux'),
            self.exists('controlPlaneProfile.upgrades'),
            self.check('type', 'Microsoft.ContainerService/managedClusters/upgradeprofiles')
        ])

        # upgrade
        new_k8s_version = '1.8.6'
        upgrade_cmd = 'aks upgrade -g {} -n {} --kubernetes-version {} --yes'
        self.cmd(upgrade_cmd.format(resource_group, aks_name, new_k8s_version), checks=[
            self.check('provisioningState', 'Succeeded')
        ])

        # show again
        self.cmd('aks show -g {} -n {}'.format(resource_group, aks_name), checks=[
            self.check('kubernetesVersion', new_k8s_version)
        ])

        # delete
        self.cmd('aks delete -g {} -n {} -y'.format(resource_group, aks_name), checks=[
            self.is_empty()
        ])


    @classmethod
    def generate_ssh_keys(cls):
        TEST_SSH_KEY_PUB = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCbIg1guRHbI0lV11wWDt1r2cUdcNd27CJsg+SfgC7miZeubtwUhbsPdhMQsfDyhOWHq1+ZL0M+nJZV63d/1dhmhtgyOqejUwrPlzKhydsbrsdUor+JmNJDdW01v7BXHyuymT8G4s09jCasNOwiufbP/qp72ruu0bIA1nySsvlf9pCQAuFkAnVnf/rFhUlOkhtRpwcq8SUNY2zRHR/EKb/4NWY1JzR4sa3q2fWIJdrrX0DvLoa5g9bIEd4Df79ba7v+yiUBOS0zT2ll+z4g9izHK3EO5d8hL4jYxcjKs+wcslSYRWrascfscLgMlMGh0CdKeNTDjHpGPncaf3Z+FwwwjWeuiNBxv7bJo13/8B/098KlVDl4GZqsoBCEjPyJfV6hO0y/LkRGkk7oHWKgeWAfKtfLItRp00eZ4fcJNK9kCaSMmEugoZWcI7NGbZXzqFWqbpRI7NcDP9+WIQ+i9U5vqWsqd/zng4kbuAJ6UuKqIzB0upYrLShfQE3SAck8oaLhJqqq56VfDuASNpJKidV+zq27HfSBmbXnkR/5AK337dc3MXKJypoK/QPMLKUAP5XLPbs+NddJQV7EZXd29DLgp+fRIg3edpKdO7ZErWhv7d+3Kws+e1Y+ypmR2WIVSwVyBEUfgv2C8Ts9gnTF4pNcEY/S2aBicz5Ew2+jdyGNQQ== test@example.com\n"  # pylint: disable=line-too-long
        _, pathname = tempfile.mkstemp()
        with open(pathname, 'w') as key_file:
            key_file.write(TEST_SSH_KEY_PUB)
        return pathname
