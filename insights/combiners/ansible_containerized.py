"""
Ansible Containerized
=====================
Combiner to collect data about a containerized Ansible Automation Platform
(AAP) deployment: the AAP containers (those whose image contains
``ansible-automation-platform``).
"""

from typing import List

from insights.core.plugins import combiner
from insights.parsers.podman import PodmanPsAllJson

AAP_IMAGE_MARKER = "ansible-automation-platform"


@combiner(PodmanPsAllJson)
class AnsibleContainerized(object):
    """
    Collects the AAP containers from the root-owned podman containers
    (``PodmanPsAllJson``).

    Containers are matched by image: any container whose image contains
    ``ansible-automation-platform``. This captures the whole AAP stack
    (gateway, controller, receptor, eda, hub, metrics, ...) including the
    execution-node case where ``receptor`` may be the only AAP container.

    ``PodmanPsAllJson`` is a required dependency, so this combiner only runs
    when the podman containers were collected. When it runs but no AAP
    containers are present, ``containers`` is an empty list.

    Attributes:
        containers (list): The raw podman jsons for the AAP containers
            (empty list if none were found).

    Examples:
        >>> type(ansible_containerized)
        <class 'insights.combiners.ansible_containerized.AnsibleContainerized'>
        >>> len(ansible_containerized.containers)
        2
    """

    def __init__(self, podman_ps: PodmanPsAllJson) -> None:
        self.containers: List[dict] = podman_ps.search_by_image(AAP_IMAGE_MARKER, partial=True)
