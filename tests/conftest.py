# Copyright 2023 VMware, Inc.
# SPDX-License-Identifier: Apache-2.0
#
import os

import pytest
from saltext.salt_describe import PACKAGE_ROOT
from saltfactories.utils import random_string


@pytest.fixture(scope="session")
def salt_factories_config():
    """
    Return a dictionary with the keyworkd arguments for FactoriesManager
    """
    return {
        "code_dir": str(PACKAGE_ROOT),
        "start_timeout": 120 if os.environ.get("CI") else 60,
    }


@pytest.fixture(scope="package")
def master(salt_factories):
    return salt_factories.salt_master_daemon(random_string("master-"))


@pytest.fixture(scope="package")
def minion(master):
    return master.salt_minion_daemon(random_string("minion-"))
