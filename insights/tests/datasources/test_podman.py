import json
import pwd

import pytest

from unittest.mock import Mock, patch

from insights.core.exceptions import SkipComponent
from insights.core.spec_factory import DatasourceProvider
from insights.specs.datasources.podman import (
    LocalSpecs,
    _get_rootless_podman_users,
    podman_ps_all_json_rootless,
    podman_rootless_users,
)

RELATIVE_PATH = "insights_datasources/podman_ps_all_json_rootless"


def _pw(name, home):
    # pwd.struct_passwd((name, passwd, uid, gid, gecos, dir, shell))
    return pwd.struct_passwd((name, "x", 1000, 1000, "", home, "/sbin/nologin"))


ALICE_PS = '[{"Id": "a1", "Image": "img:1", "Names": ["foreman"], "State": "running"}]'
BOB_PS = '[{"Id": "b1", "Image": "img:2", "Names": ["receptor"], "State": "exited"}]'


@patch("insights.specs.datasources.podman.os.path.isdir")
@patch("insights.specs.datasources.podman.pwd.getpwall")
def test_get_rootless_podman_users(getpwall, isdir):
    getpwall.return_value = [
        _pw("root", "/root"),  # excluded: root
        _pw("alice", "/home/alice"),  # kept: has storage
        _pw("bob", "/home/bob"),  # kept: has storage
        _pw("carol", "/home/carol"),  # excluded: no storage dir
        _pw("daemon", "/"),  # excluded: home is /
        _pw("nohome", ""),  # excluded: no home
    ]
    have_storage = {
        "/home/alice/.local/share/containers/storage",
        "/home/bob/.local/share/containers/storage",
    }
    isdir.side_effect = lambda p: p in have_storage
    assert _get_rootless_podman_users() == ["alice", "bob"]


@patch("insights.specs.datasources.podman.os.path.isdir")
@patch("insights.specs.datasources.podman.pwd.getpwall")
def test_podman_rootless_users_skip_when_none(getpwall, isdir):
    getpwall.return_value = [_pw("root", "/root"), _pw("carol", "/home/carol")]
    isdir.return_value = False
    with pytest.raises(SkipComponent):
        podman_rootless_users(None)


def test_podman_ps_all_json_rootless():
    alice = Mock()
    alice.args = "alice"
    alice.content = [ALICE_PS]
    bob = Mock()
    bob.args = "bob"
    bob.content = [BOB_PS]
    empty = Mock()
    empty.args = "carol"
    empty.content = ["[]"]  # no containers -> dropped
    broken = Mock()
    broken.args = "dave"
    broken.content = ["not json"]  # unparseable -> dropped

    broker = {LocalSpecs.podman_ps_rootless_raw: [alice, bob, empty, broken]}
    result = podman_ps_all_json_rootless(broker)

    assert isinstance(result, DatasourceProvider)
    assert result.relative_path == RELATIVE_PATH
    # flat list of containers, no per-user grouping and no username persisted
    expected = json.loads(ALICE_PS) + json.loads(BOB_PS)
    assert json.loads("".join(result.content)) == expected


def test_podman_ps_all_json_rootless_skip_when_empty():
    empty = Mock()
    empty.args = "carol"
    empty.content = ["[]"]
    broker = {LocalSpecs.podman_ps_rootless_raw: [empty]}
    with pytest.raises(SkipComponent):
        podman_ps_all_json_rootless(broker)
