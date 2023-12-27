"""Create a radar view for IRM KMI weather"""
# File inspired by https://github.com/jodur/imagesdirectory-camera/blob/main/custom_components/imagedirectory/camera.py

import logging
import os

from homeassistant.components.camera import Camera, async_get_still_stream
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IrmKmiCoordinator
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the camera entry."""

    _LOGGER.debug(f'async_setup_entry entry is: {entry}')
    coordinator = hass.data[DOMAIN][entry.entry_id]
    # await coordinator.async_config_entry_first_refresh()
    async_add_entities(
        [IrmKmiRadar(coordinator, entry)]
    )


class IrmKmiRadar(CoordinatorEntity, Camera):
    """Representation of a local file camera."""

    def __init__(self,
                 coordinator: IrmKmiCoordinator,
                 entry: ConfigEntry,
                 ) -> None:
        """Initialize Local File Camera component."""
        super().__init__(coordinator)
        Camera.__init__(self)
        self._name = f"Radar {entry.title}"
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="IRM KMI",
            name=f"Radar {entry.title}"
        )

        self._image_index = 0

    @property  # Baseclass Camera property override
    def frame_interval(self) -> float:
        """Return the interval between frames of the mjpeg stream"""
        return 0.3

    def camera_image(self,
                     width: int | None = None,
                     height: int | None = None) -> bytes | None:
        images = self.coordinator.data.get('animation', {}).get('images')
        if isinstance(images, list) and len(images) > 0:
            return images[0]
        return None

    async def async_camera_image(
            self,
            width: int | None = None,
            height: int | None = None
    ) -> bytes | None:
        """Return bytes of camera image."""
        return self.camera_image()

    async def handle_async_still_stream(self, request, interval):
        """Generate an HTTP MJPEG stream from camera images."""
        _LOGGER.info("handle_async_still_stream")
        self._image_index = 0
        return await async_get_still_stream(
            request, self.iterate, self.content_type, interval
        )

    async def handle_async_mjpeg_stream(self, request):
        """Serve an HTTP MJPEG stream from the camera."""
        _LOGGER.info("handle_async_mjpeg_stream")
        return await self.handle_async_still_stream(request, self.frame_interval)

    async def iterate(self) -> bytes | None:
        images = self.coordinator.data.get('animation', {}).get('images')
        if isinstance(images, list) and len(images) > 0:
            r = images[self._image_index]
            self._image_index = (self._image_index + 1) % len(images)
            return r
        return None

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    @property
    def extra_state_attributes(self):
        """Return the camera state attributes."""
        attrs = {"hint": self.coordinator.data.get('animation', {}).get('hint')}
        return attrs

