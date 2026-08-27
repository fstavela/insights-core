import doctest

from insights.parsers.podman import PodmanPsAllJson, PodmanPsAllJsonRootless
from insights.combiners.podman_containers import PodmanContainers
from insights.combiners import ansible_containerized
from insights.combiners.ansible_containerized import AnsibleContainerized
from insights.tests import context_wrap

PODMAN_PS_AAP = """
[
    {
        "Id": "pg",
        "Image": "registry.redhat.io/rhel9/postgresql-15:latest",
        "Names": ["postgresql"],
        "State": "running",
        "Status": "Up 38 minutes"
    },
    {
        "Id": "gw",
        "Image": "registry.redhat.io/ansible-automation-platform-27/gateway-rhel9:latest",
        "Names": ["automation-gateway"],
        "State": "running",
        "Status": "Up 36 minutes"
    },
    {
        "Id": "rc",
        "Image": "registry.redhat.io/ansible-automation-platform-27/receptor-rhel9:latest",
        "Names": ["receptor"],
        "State": "running",
        "Status": "Up 34 minutes"
    }
]
""".strip()

PODMAN_PS_EXEC_NODE = """
[
    {
        "Id": "rc",
        "Image": "registry.redhat.io/ansible-automation-platform-27/receptor-rhel9:latest",
        "Names": ["receptor"],
        "State": "running",
        "Status": "Up 41 minutes"
    }
]
""".strip()

PODMAN_PS_NO_AAP = """
[
    {
        "Id": "pg",
        "Image": "registry.redhat.io/rhel9/postgresql-15:latest",
        "Names": ["postgresql"],
        "State": "running",
        "Status": "Up 38 minutes"
    }
]
""".strip()


PODMAN_PS_ROOTLESS_AAP = """
[
    {"Id": "gw", "Image": "registry.redhat.io/ansible-automation-platform-27/gateway-rhel9:latest", "Names": ["automation-gateway"], "State": "running", "Status": "Up 36 minutes"},
    {"Id": "pg", "Image": "registry.redhat.io/rhel9/postgresql-15:latest", "Names": ["postgresql"], "State": "running", "Status": "Up 38 minutes"}
]
""".strip()


def test_ansible_containerized_mixed():
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_AAP)), None)
    comb = AnsibleContainerized(podman)
    # postgresql excluded; gateway + receptor captured
    assert len(comb.containers) == 2
    names = sorted(c["Names"][0] for c in comb.containers)
    assert names == ["automation-gateway", "receptor"]


def test_ansible_containerized_exec_node():
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_EXEC_NODE)), None)
    comb = AnsibleContainerized(podman)
    assert len(comb.containers) == 1
    assert comb.containers[0]["Names"] == ["receptor"]
    assert comb.containers[0]["State"] == "running"


def test_ansible_containerized_no_aap():
    # podman was collected but no AAP containers are present -> empty list,
    # no SkipComponent (the required PodmanContainers dependency was satisfied)
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_NO_AAP)), None)
    comb = AnsibleContainerized(podman)
    assert comb.containers == []


def test_ansible_containerized_rootless_only():
    rootless = PodmanPsAllJsonRootless(context_wrap(PODMAN_PS_ROOTLESS_AAP))
    podman = PodmanContainers(None, rootless)
    comb = AnsibleContainerized(podman)
    assert len(comb.containers) == 1
    assert comb.containers[0]["Id"] == "gw"


def test_ansible_containerized_docs():
    podman = PodmanContainers(PodmanPsAllJson(context_wrap(PODMAN_PS_AAP)), None)
    comb = AnsibleContainerized(podman)
    failed, _ = doctest.testmod(
        ansible_containerized,
        globs={"ansible_containerized": comb},
    )
    assert failed == 0
