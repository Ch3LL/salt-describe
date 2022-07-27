import os.path
import pathlib

import salt.config
import salt.syspaths
import salt.utils.files
import yaml


def generate_sls(opts, minion, state, sls_name="default"):
    """
    Generate an sls file for the minion with given state contents
    """
    state_file_root = pathlib.Path(opts.get("file_roots").get("base")[0])

    minion_state_root = state_file_root / minion
    if not os.path.exists(minion_state_root):
        os.mkdir(minion_state_root)

    minion_state_file = minion_state_root / f"{sls_name}.sls"

    with salt.utils.files.fopen(minion_state_file, "w") as fp_:
        fp_.write(state)

    generate_init(opts, minion)
    return True


def generate_init(opts, minion=None, env="base"):
    """
    Generate the init.sls for the minion or minions
    """
    state_file_root = opts.get("file_roots").get("base")[0]

    minion_state_root = f"{state_file_root}/{minion}"
    if not os.path.exists(minion_state_root):
        os.mkdir(minion_state_root)

    minion_init_file = f"{minion_state_root}/init.sls"

    include_files = []
    for file in os.listdir(minion_state_root):
        if file.endswith(".sls") and file != "init.sls":
            _file = os.path.splitext(file)[0]
            include_files.append(f"{minion}.{_file}")

    state_contents = {"include": include_files}

    with salt.utils.files.fopen(minion_init_file, "w") as fp_:
        fp_.write(yaml.dump(state_contents))

    return True


def generate_pillar_init(opts, minion=None, env="base"):
    """
    Generate the init.sls for the minion or minions
    """
    pillar_file_root = pathlib.Path(opts.get("pillar_roots").get("base")[0])

    minion_pillar_root = pillar_file_root / minion
    if not os.path.exists(minion_pillar_root):
        os.mkdir(minion_pillar_root)

    minion_init_file = f"{minion_pillar_root}/init.sls"

    include_files = []
    for file in os.listdir(minion_pillar_root):
        if file.endswith(".sls") and file != "init.sls":
            _file = os.path.splitext(file)[0]
            include_files.append(f"{minion}.{_file}")

    pillar_contents = {"include": include_files}

    with salt.utils.files.fopen(minion_init_file, "w") as fp_:
        fp_.write(yaml.dump(pillar_contents))

    return True


def generate_pillars(opts, minion, pillar, sls_name="default"):
    """
    Generate pillar files for the minion to hold more sensitive information
    """
    pillar_file_root = pathlib.Path(opts.get("pillar_roots").get("base")[0])

    minion_pillar_root = pillar_file_root / minion
    if not os.path.exists(minion_pillar_root):
        os.mkdir(minion_pillar_root)

    minion_pillar_file = minion_pillar_root / f"{sls_name}.sls"

    with salt.utils.files.fopen(minion_pillar_file, "w") as fp_:
        fp_.write(pillar)

    generate_pillar_init(opts, minion)
    return True
