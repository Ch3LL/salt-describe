"""
Module for building state file

.. versionadded:: 3006

"""
import logging

import yaml
from saltext.salt_describe.utils.salt_describe import generate_pillars
from saltext.salt_describe.utils.salt_describe import generate_sls

__virtualname__ = "describe"


log = logging.getLogger(__name__)


def __virtual__():
    return __virtualname__


def user(tgt, require_groups=False, tgt_type="glob"):
    """
    read users on the minions and build a state file
    to manage the users.

    CLI Example:

    .. code-block:: bash

        salt-run describe.user minion-tgt
    """

    state_contents = {}
    if require_groups is True:
        __salt__["describe.group"](tgt=tgt, include_members=False, tgt_type=tgt_type)

    users = __salt__["salt.execute"](
        tgt,
        "user.getent",
        tgt_type=tgt_type,
    )

    pillars = {"users": {}}
    for minion in list(users.keys()):
        for user in users[minion]:
            shadow = __salt__["salt.execute"](
                minion, "shadow.info", arg=[user["name"]], tgt_type="glob"
            )[minion]

            homeexists = __salt__["salt.execute"](
                minion, "file.directory_exists", arg=[user["home"]], tgt_type="glob"
            )[minion]
            username = user["name"]
            payload = [
                {"name": username},
                {"uid": user["uid"]},
                {"gid": user["gid"]},
                {"allow_uid_change": True},
                {"allow_gid_change": True},
                {"home": user["home"]},
                {"shell": user["shell"]},
                {"groups": user["groups"]},
                {"password": f'{{{{ salt["pillar.get"]("users:{username}","*") }}}}'},
                {"date": shadow["lstchg"]},
                {"mindays": shadow["min"]},
                {"maxdays": shadow["max"]},
                {"inactdays": shadow["inact"]},
                {"expire": shadow["expire"]},
            ]
            if homeexists:
                payload.append({"createhome": True})
            else:
                payload.append({"createhome": False})
            # GECOS
            if user["fullname"]:
                payload.append({"fullname": user["fullname"]})
            if user["homephone"]:
                payload.append({"homephone": user["homephone"]})
            if user["other"]:
                payload.append({"other": user["other"]})
            if user["roomnumber"]:
                payload.append({"roomnumber": user["roomnumber"]})
            if user["workphone"]:
                payload.append({"workphone": user["workphone"]})

            state_contents[f"user-{username}"] = {"user.present": payload}
            passwd = shadow["passwd"]
            if passwd != "*":
                pillars["users"].update({user["name"]: f"{passwd}"})

        state = yaml.dump(state_contents)
        pillars = yaml.dump(pillars)
        generate_sls(minion, state, "users")
        generate_pillars(minion, pillars, "users")
    return True


def group(tgt, include_members=False, tgt_type="glob"):
    """
    read groups on the minions and build a state file
    to managed th groups.

    CLI Example:

    .. code-block:: bash

        salt-run describe.group minion-tgt
    """
    groups = __salt__["salt.execute"](
        tgt,
        "group.getent",
        tgt_type=tgt_type,
    )

    state_contents = {}
    for minion in list(groups.keys()):
        for group in groups[minion]:
            groupname = group["name"]
            payload = [{"name": groupname}, {"gid": group["gid"]}]
            if include_members is True:
                payload.append({"members": group["members"]})
            state_contents[f"group-{groupname}"] = {"group.present": payload}

        state = yaml.dump(state_contents)

        generate_sls(minion, state, "groups")

    return True