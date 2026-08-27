"""
Satellite Containerized
=======================
Combiner to collect data about a containerized Satellite deployment: the
``foremanctl`` RPM version and the ``foreman`` / ``foreman-proxy`` containers.
"""

from typing import List, Optional

from insights.core.exceptions import SkipComponent
from insights.core.plugins import combiner
from insights.parsers.installed_rpms import InstalledRpms
from insights.combiners.podman_containers import PodmanContainers

FOREMANCTL_PKG = "foremanctl"
FOREMAN_CONTAINER = "foreman"
FOREMAN_PROXY_CONTAINER = "foreman-proxy"


@combiner(optional=[InstalledRpms, PodmanContainers])
class SatelliteContainerized(object):
    """
    Collects data about a containerized Satellite deployment.

    The ``foreman`` and ``foreman-proxy`` containers are located by exact
    container name. Matching by name (not image) is deliberate: the foreman
    image is shared by the ``dynflow-sidekiq-*`` containers, so an image match
    would wrongly capture those too. All matches are kept (a list rather than a
    single container) because container names are only unique per user, so
    rootless deployments may expose several containers with the same name.

    Attributes:
        foremanctl_version (str): Version of the ``foremanctl`` RPM, or ``None``.
        containers (list): Raw podman jsons for the ``foreman`` and
            ``foreman-proxy`` containers. ``None`` when the podman containers
            were not collected, or an empty list when they were collected but
            no matching containers were found.

    Raises:
        SkipComponent: When nothing was collected (neither ``InstalledRpms``
            nor the podman containers).

    Examples:
        >>> type(satellite_containerized)
        <class 'insights.combiners.satellite_containerized.SatelliteContainerized'>
        >>> satellite_containerized.foremanctl_version
        '1.1.0'
        >>> len(satellite_containerized.containers)
        2
        >>> satellite_containerized.containers[0]["Names"]
        ['foreman']
    """

    def __init__(
        self,
        rpms: Optional[InstalledRpms],
        podman_ps: Optional[PodmanContainers],
    ) -> None:
        if rpms is None and podman_ps is None:
            raise SkipComponent("Not a containerized Satellite: nothing collected")

        self.foremanctl_version: Optional[str] = None
        self.containers: Optional[List[dict]] = None

        if rpms:
            foremanctl = rpms.get_max(FOREMANCTL_PKG)
            if foremanctl:
                self.foremanctl_version = foremanctl.version

        if podman_ps:
            self.containers = podman_ps.search_by_name(
                FOREMAN_CONTAINER
            ) + podman_ps.search_by_name(FOREMAN_PROXY_CONTAINER)
