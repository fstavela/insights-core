"""
Parsers for podman
==================

This module contains the following parsers:

PodmanPsAllJson - command ``podman ps --all --no-trunc --size --format=json``
-----------------------------------------------------------------------------

PodmanPsAllJsonRootless - datasource ``podman_ps_all_json_rootless``
--------------------------------------------------------------------
"""

from typing import List

from insights import parser, JSONParser
from insights.specs import Specs


class PodmanContainerSearch(object):
    """
    Mixin providing container search helpers over a flat ``self.data`` list of
    container dicts (as produced by ``podman ps ... --format=json``).
    """

    def search_by_name(self, name: str, partial: bool = False) -> List[dict]:
        """
        Search containers by name.

        Args:
            name (str): The container name to search for.
            partial (bool): When ``False`` (default) match the name exactly;
                when ``True`` match containers whose name contains ``name``.

        Returns:
            list: The matching raw container jsons (empty list if none match).
        """
        if partial:
            return [c for c in self.data if any(name in n for n in c.get("Names", []))]
        return [c for c in self.data if name in c.get("Names", [])]

    def search_by_image(self, image: str, partial: bool = False) -> List[dict]:
        """
        Search containers by image.

        Args:
            image (str): The image to search for.
            partial (bool): When ``False`` (default) match the image exactly;
                when ``True`` match containers whose image contains ``image``.

        Returns:
            list: The matching raw container jsons (empty list if none match).
        """
        if partial:
            return [c for c in self.data if image in c.get("Image", "")]
        return [c for c in self.data if c.get("Image", "") == image]


@parser(Specs.podman_ps_all_json)
class PodmanPsAllJson(JSONParser, PodmanContainerSearch):
    """
    Class for parsing the output of the ``podman ps --all --no-trunc --size --format=json`` command.

    The output is a JSON array containing objects with container information.

    Typical output of this command::

        [
            {
                "AutoRemove": false,
                "Command": [
                    "/usr/sbin/httpd",
                    "-DFOREGROUND"
                ],
                "Created": "2024-01-15T10:30:45.123456789-05:00",
                "CreatedAt": "2024-01-15 10:30:45 -0500 EST",
                "Exited": false,
                "ExitedAt": -62135596800,
                "ExitCode": 0,
                "Id": "03e2861336a76e29155836113ff6560cb70780c32f95062642993b2b3d0fc216",
                "Image": "rhel7_httpd",
                "ImageID": "882ab98aae5394aebe91fe6d8a4297fa0387c3cfd421b2d892bddf218ac373b2",
                "IsInfra": false,
                "Labels": {
                    "maintainer": "Red Hat"
                },
                "Mounts": [],
                "Names": [
                    "angry_saha"
                ],
                "Namespaces": {},
                "Networks": [
                    "podman"
                ],
                "Pid": 12345,
                "Pod": "",
                "PodName": "",
                "Ports": [
                    {
                        "host_ip": "0.0.0.0",
                        "container_port": 80,
                        "host_port": 8080,
                        "range": 1,
                        "protocol": "tcp"
                    }
                ],
                "Size": {
                    "rootFsSize": 221554338,
                    "rwSize": 0
                },
                "StartedAt": 1705330245,
                "State": "running",
                "Status": "Up 37 seconds"
            }
        ]

    Attributes:
        data (list): A list containing the parsed container information as dictionaries

    Examples:
        >>> type(podman_ps_json.data)
        <class 'list'>
        >>> len(podman_ps_json.data)
        2
        >>> podman_ps_json.data[0]["Id"]
        '03e2861336a76e29155836113ff6560cb70780c32f95062642993b2b3d0fc216'
        >>> podman_ps_json.data[0]["State"]
        'running'
        >>> podman_ps_json.data[0]["Names"]
        ['angry_saha']
        >>> podman_ps_json.data[0]["Image"]
        'rhel7_httpd'
        >>> len(podman_ps_json.search_by_name("angry_saha"))
        1
        >>> podman_ps_json.search_by_image("rhel7_httpd")[0]["Names"]
        ['angry_saha']
        >>> len(podman_ps_json.search_by_image("httpd", partial=True))
        1
    """

    pass


@parser(Specs.podman_ps_all_json_rootless)
class PodmanPsAllJsonRootless(JSONParser, PodmanContainerSearch):
    """
    Parses the aggregated rootless ``podman ps --all --no-trunc --format=json``
    json produced by the
    :py:func:`insights.specs.datasources.podman.podman_ps_all_json_rootless`
    datasource.

    The collected content is a flat list of raw podman container jsons (from all
    rootless users combined); the owning username is not persisted.

    Attributes:
        data (list): Flat list of all rootless container dicts (raw, unmodified).

    Examples:
        >>> type(podman_ps_rootless.data)
        <class 'list'>
        >>> len(podman_ps_rootless.data)
        3
        >>> podman_ps_rootless.search_by_name("foreman")[0]["Id"]
        'a1'
    """

    pass
