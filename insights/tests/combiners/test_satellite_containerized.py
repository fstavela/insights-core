import doctest
import pytest

from insights.core.exceptions import SkipComponent
from insights.parsers.installed_rpms import InstalledRpms
from insights.parsers.podman import PodmanPsAllJson, PodmanPsAllJsonRootless
from insights.combiners.podman_containers import PodmanContainers
from insights.combiners import satellite_containerized
from insights.combiners.satellite_containerized import SatelliteContainerized
from insights.tests import context_wrap

FOREMANCTL_RPM = "foremanctl-1.1.0-1.el9.noarch"

PODMAN_PS_SATELLITE = """
[
    {
        "Id": "aaa",
        "Image": "quay.io/foreman/foreman:3.16",
        "Names": ["dynflow-sidekiq-worker"],
        "State": "running",
        "Status": "Up 59 minutes"
    },
    {
        "Id": "bbb",
        "Image": "quay.io/sclorg/postgresql-13-c9s:latest",
        "Names": ["postgresql"],
        "State": "running",
        "Status": "Up 2 hours"
    },
    {
        "Id": "ccc",
        "Image": "quay.io/foreman/foreman:3.16",
        "Names": ["foreman"],
        "State": "running",
        "Status": "Up 41 minutes"
    },
    {
        "Id": "ddd",
        "Image": "quay.io/foreman/foreman-proxy:3.16",
        "Names": ["foreman-proxy"],
        "State": "exited",
        "Status": "Exited (0) 5 minutes ago"
    }
]
""".strip()

PODMAN_PS_SERVER_ONLY = """
[
    {
        "Id": "ccc",
        "Image": "quay.io/foreman/foreman:3.16",
        "Names": ["foreman"],
        "State": "running",
        "Status": "Up 41 minutes"
    }
]
""".strip()

PODMAN_PS_CAPSULE_ONLY = """
[
    {
        "Id": "ddd",
        "Image": "quay.io/foreman/foreman-proxy:3.16",
        "Names": ["foreman-proxy"],
        "State": "running",
        "Status": "Up 30 minutes"
    }
]
""".strip()

PODMAN_PS_NO_FOREMAN = """
[
    {
        "Id": "bbb",
        "Image": "quay.io/sclorg/postgresql-13-c9s:latest",
        "Names": ["postgresql"],
        "State": "running",
        "Status": "Up 2 hours"
    }
]
""".strip()


def test_satellite_containerized_both():
    rpms = InstalledRpms(context_wrap(FOREMANCTL_RPM))
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_SATELLITE)), None)
    comb = SatelliteContainerized(rpms, podman)
    assert comb.foremanctl_version == "1.1.0"
    # exact name match isolates foreman from the dynflow-sidekiq container
    assert [c["Id"] for c in comb.containers] == ["ccc", "ddd"]


def test_satellite_containerized_rpm_only():
    # podman not collected -> containers is None (distinct from "not found")
    rpms = InstalledRpms(context_wrap(FOREMANCTL_RPM))
    comb = SatelliteContainerized(rpms, None)
    assert comb.foremanctl_version == "1.1.0"
    assert comb.containers is None


def test_satellite_containerized_podman_only():
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_SATELLITE)), None)
    comb = SatelliteContainerized(None, podman)
    assert comb.foremanctl_version is None
    assert [c["Id"] for c in comb.containers] == ["ccc", "ddd"]


def test_satellite_containerized_server_only_with_rpm():
    rpms = InstalledRpms(context_wrap(FOREMANCTL_RPM))
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_SERVER_ONLY)), None)
    comb = SatelliteContainerized(rpms, podman)
    assert comb.foremanctl_version == "1.1.0"
    assert [c["Id"] for c in comb.containers] == ["ccc"]


def test_satellite_containerized_server_only_without_rpm():
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_SERVER_ONLY)), None)
    comb = SatelliteContainerized(None, podman)
    assert comb.foremanctl_version is None
    assert [c["Id"] for c in comb.containers] == ["ccc"]


def test_satellite_containerized_capsule_only_with_rpm():
    rpms = InstalledRpms(context_wrap(FOREMANCTL_RPM))
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_CAPSULE_ONLY)), None)
    comb = SatelliteContainerized(rpms, podman)
    assert comb.foremanctl_version == "1.1.0"
    assert [c["Id"] for c in comb.containers] == ["ddd"]


def test_satellite_containerized_capsule_only_without_rpm():
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_CAPSULE_ONLY)), None)
    comb = SatelliteContainerized(None, podman)
    assert comb.foremanctl_version is None
    assert [c["Id"] for c in comb.containers] == ["ddd"]


def test_satellite_containerized_skip_no_data():
    # nothing collected at all -> SkipComponent
    with pytest.raises(SkipComponent):
        SatelliteContainerized(None, None)


def test_satellite_containerized_no_foreman():
    # podman was collected but has no foreman containers -> empty list, and
    # no foremanctl RPM; the combiner still fires (podman was collected)
    rpms = InstalledRpms(context_wrap("bash-5.1.8-6.el9"))
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_NO_FOREMAN)), None)
    comb = SatelliteContainerized(rpms, podman)
    assert comb.foremanctl_version is None
    assert comb.containers == []


PODMAN_PS_ROOTLESS_SATELLITE = """
[
    {"Id": "ccc", "Image": "quay.io/foreman/foreman:3.16", "Names": ["foreman"], "State": "running", "Status": "Up 41 minutes"},
    {"Id": "ddd", "Image": "quay.io/foreman/foreman-proxy:3.16", "Names": ["foreman-proxy"], "State": "running", "Status": "Up 30 minutes"}
]
""".strip()


def test_satellite_containerized_rootless_only():
    rootless = PodmanPsAllJsonRootless(context_wrap(PODMAN_PS_ROOTLESS_SATELLITE))
    podman = PodmanContainers(None, rootless)
    comb = SatelliteContainerized(None, podman)
    assert [c["Id"] for c in comb.containers] == ["ccc", "ddd"]


def test_satellite_containerized_docs():
    rpms = InstalledRpms(context_wrap(FOREMANCTL_RPM))
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_SATELLITE)), None)
    comb = SatelliteContainerized(rpms, podman)
    failed, _ = doctest.testmod(
        satellite_containerized,
        globs={"satellite_containerized": comb},
    )
    assert failed == 0
