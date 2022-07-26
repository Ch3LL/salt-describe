# pylint: disable=line-too-long
import logging
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import mock_open
from unittest.mock import patch

import pytest
import salt.config  # pylint: disable=import-error
import salt.runners.salt as salt_runner  # pylint: disable=import-error
import saltext.salt_describe.runners.salt_describe as salt_describe_runner
import saltext.salt_describe.runners.salt_describe_user as salt_describe_user_runner

log = logging.getLogger(__name__)


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"salt.execute": salt_runner.execute},
        "__opts__": salt.config.DEFAULT_MASTER_OPTS.copy(),
    }
    return {
        salt_describe_runner: module_globals,
        salt_describe_user_runner: module_globals,
    }


def test_group():
    group_getent = {
        "minion": [
            {"gid": 4, "members": ["syslog", "whytewolf"], "name": "adm", "passwd": "x"},
            {"gid": 0, "members": [], "name": "root", "passwd": "x"},
        ]
    }

    expected_calls = [
        call().write(
            "group-adm:\n  group.present:\n  - name: adm\n  - gid: 4\ngroup-root:\n  group.present:\n  - name: root\n  - gid: 0\n"
        ),
        call().write("include:\n- minion.groups\n"),
    ]

    with patch.dict(
        salt_describe_runner.__salt__, {"salt.execute": MagicMock(return_value=group_getent)}
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {"config.get": MagicMock(return_value=["/srv/salt", "/srv/spm/salt"])},
        ):
            with patch("os.listdir", return_value=["groups.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_user_runner.group("minion") is True
                    open_mock.return_value.write.assert_has_calls(expected_calls, any_order=True)


def test_user():
    user_getent = {
        "minion": [
            {
                "name": "testuser",
                "uid": 1000,
                "gid": 1000,
                "groups": ["adm"],
                "home": "/home/testuser",
                "passwd": "x",
                "shell": "/usr/bin/zsh",
                "fullname": "",
                "homephone": "",
                "other": "",
                "roomnumber": "",
                "workphone": "",
            }
        ]
    }
    user_shadow = {
        "minion": {
            "expire": -1,
            "inact": -1,
            "lstchg": 19103,
            "max": 99999,
            "min": 0,
            "name": "testuser",
            "passwd": "$5$k69zJBp1LxA3q8az$XKEp1knAex0j.xoi/sdU4XllHpZ0JzYYRfASKGl6qZA",
            "warn": 7,
        }
    }
    fileexists = {"minion": True}
    expected_calls = [
        call().write(
            'user-testuser:\n  user.present:\n  - name: testuser\n  - uid: 1000\n  - gid: 1000\n  - allow_uid_change: true\n  - allow_gid_change: true\n  - home: /home/testuser\n  - shell: /usr/bin/zsh\n  - groups:\n    - adm\n  - password: \'{{ salt["pillar.get"]("users:testuser","*") }}\'\n  - date: 19103\n  - mindays: 0\n  - maxdays: 99999\n  - inactdays: -1\n  - expire: -1\n  - createhome: true\n'
        ),
        call().write("include:\n- minion.users\n"),
    ]

    with patch.dict(
        salt_describe_user_runner.__salt__,
        {"salt.execute": MagicMock(side_effect=[user_getent, user_shadow, fileexists])},
    ):
        with patch.dict(
            salt_describe_runner.__salt__,
            {
                "config.get": MagicMock(
                    side_effect=[["/srv/salt"], ["/srv/salt"], ["/srv/pillar"], ["/srv/pillar"]]
                )
            },
        ):
            with patch("os.listdir", return_value=["users.sls"]):
                with patch("salt.utils.files.fopen", mock_open()) as open_mock:
                    assert salt_describe_user_runner.user("minion") is True
                    open_mock.return_value.write.assert_has_calls(expected_calls, any_order=True)


# pylint: enable=line-too-long