"""ZCS Lawn Mower Robot camera platform."""
from __future__ import annotations

import io
import math
import numpy as np

from datetime import (
    timedelta,
)

from PIL import (
    Image,
    ImageDraw,
)

from collections.abc import Callable

from homeassistant.core import HomeAssistant
from homeassistant.const import (
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_LOCATION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.camera import (
    Camera,
    CameraEntityDescription,
    SUPPORT_ON_OFF,
)
from homeassistant.components.recorder import (
    get_instance,
    history,
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import homeassistant.util.dt as dt_util

from .const import (
    LOGGER,
    DOMAIN,
    CONF_CAMERA_ENABLE,
    CONF_IMG_PATH_MAP,
    CONF_IMG_PATH_MOWER,
    CONF_GPS_TOP_LEFT,
    CONF_GPS_BOTTOM_RIGHT,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ENTITY_DESCRIPTIONS = (
    CameraEntityDescription(
        key="map",
        translation_key="map",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Entity,
) -> None:
    """Do setup cameras from a config entry created in the integrations UI."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities(
        [
            ZcsMowerCamera(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                entity_description=entity_description,
                imei=imei,
                name=name,
            )
            for imei, name in coordinator.mowers.items()
            for entity_description in ENTITY_DESCRIPTIONS
        ],
        update_before_add=True,
    )


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    # TODO
    LOGGER.debug("async_setup_platform")


class ZcsMowerCamera(ZcsMowerEntity, Camera):
    """Representation of a ZCS Lawn Mower Robot camera."""

    _attr_entity_registry_enabled_default = False
    _attr_frame_interval: float = 300
    _attr_name = "Map"

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: CameraEntityDescription,
        imei: str,
        name: str,
    ) -> None:
        """Initialize the camera class."""
        Camera.__init__(self)
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            imei=imei,
            name=name,
            entity_type="sensor",
            entity_key=entity_description.key,
        )
        self.entity_description = entity_description
        self._position_history = []
        self._image = Image.new(mode="RGB", size=(200, 200))
        self._image_bytes = None
        self._image_to_bytes()
        
        self.gps_top_left = None
        self.gps_bottom_right = None

        if self.config_entry.options.get(CONF_CAMERA_ENABLE, False):
            LOGGER.debug("Camera enabled")
            self.gps_top_left = self.config_entry.options.get(CONF_GPS_TOP_LEFT)
            self.gps_bottom_right = self.config_entry.options.get(CONF_GPS_BOTTOM_RIGHT)
            self._generate_image()
        else:
            LOGGER.debug("Camera disabled")
            lat = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LATITUDE, None)
            lon = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LONGITUDE, None)
            if lat and lon:
                self._attr_entity_registry_enabled_default = True
                earth_radius = 6371008  # meters
                offset = 100  # meters
                pi = 3.14159
                top_left_lat = lat - (offset / earth_radius) * (180 / pi)
                top_left_lon = lon - (offset / earth_radius) * (180 / pi) / math.cos(lat * pi / 180)
                bottom_right_lat = lat + (offset / earth_radius) * (180 / pi)
                bottom_right_lon = lon + (offset / earth_radius) * (180 / pi) / math.cos(lat * pi / 180)
                self.gps_top_left = (top_left_lat, top_left_lon)
                self.gps_bottom_right = (bottom_right_lat, bottom_right_lon)

        _res = history.state_changes_during_period(
            self.hass,
            dt_util.now() - timedelta(hours=48),
            dt_util.now(),
            "device_tracker.mower_356234104718239",
            include_start_time_state=True,
            no_attributes=True,
        ).get("device_tracker.mower_356234104718239", [])
        LOGGER.debug(_res)

    def camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the camera image."""
        return self._image_bytes

    @property
    def brand(self) -> str | None:
        """Return the lawn mower brand."""
        return self._get_attribute(ATTR_MANUFACTURER)

    @property
    def model(self) -> str:
        """Return the lawn mower model."""
        return self._get_attribute(ATTR_MODEL)

    @property
    def supported_features(self) -> int:
        """Show supported features."""
        return SUPPORT_ON_OFF

    def turn_off(self) -> None:
        """Turn off camera."""
        raise NotImplementedError()

    async def async_turn_off(self) -> None:
        """Turn off camera."""
        await self.hass.async_add_executor_job(self.turn_off)

    def turn_on(self) -> None:
        """Turn off camera."""
        raise NotImplementedError()

    def _image_to_bytes(self) -> None:
        img_byte_arr = io.BytesIO()
        self._image.save(img_byte_arr, format="PNG")
        self._image_bytes = img_byte_arr.getvalue()

    def _generate_image(self) -> None:
        latitude = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LATITUDE, None)
        longitude = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LONGITUDE, None)
        if latitude is None or longitude is None:
            return None

        location = (latitude, longitude)
        #map_image_path = self.entry.options.get(CONF_IMG_PATH_MAP)
        map_image_path = "/config/custom_components/zcsmower/resources/map_image.png"
        map_image = Image.open(map_image_path, "r")
        #overlay_path = self.entry.options.get(CONF_IMG_PATH_MOWER)
        overlay_path = "/config/custom_components/zcsmower/resources/mower.png"
        overlay_image = Image.open(overlay_path, "r")
        x1, y1 = self._scale_to_img(location, (map_image.size[0], map_image.size[1]))
        img_draw = ImageDraw.Draw(map_image)


        overlay_image = overlay_image.resize((64, 64))
        img_w, img_h = overlay_image.size
        map_image.paste(
            overlay_image, (x1 - img_w // 2, y1 - img_h // 2), overlay_image
        )

        self._image = map_image
        self._image_to_bytes()

    def _find_points_on_line(
        self,
        point_1: ImgPoint,
        point_2: ImgPoint,
    ) -> list[ImgPoint]:
        dash_length = 10
        line_length = math.sqrt(
            (point_2[0] - point_1[0]) ** 2 + (point_2[1] - point_1[1]) ** 2
        )
        dashes = int(line_length // dash_length)

        points = []
        points.append(point_1)
        for i in range(dashes):
            points.append(self._get_point_on_vector(points[-1], point_2, dash_length))

        points.append(point_2)

        return points

    def _get_point_on_vector(
        self,
        initial_pt: ImgPoint,
        terminal_pt: ImgPoint,
        distance: int,
    ) -> ImgPoint:
        v = np.array(initial_pt, dtype=float)
        u = np.array(terminal_pt, dtype=float)
        n = v - u
        n /= np.linalg.norm(n, 2)
        point = v - distance * n

        return tuple(point)

    def _scale_to_img(
        self,
        lat_lon: GpsPoint,
        h_w: ImgDimensions
    ) -> ImgPoint:
        """Convert from latitude and longitude to the image pixels."""
        old = (self.gps_bottom_right[0], self.gps_top_left[0])
        new = (0, h_w[1])
        y = ((lat_lon[0] - old[0]) * (new[1] - new[0]) / (old[1] - old[0])) + new[0]
        old = (self.gps_top_left[1], self.gps_bottom_right[1])
        new = (0, h_w[0])
        x = ((lat_lon[1] - old[0]) * (new[1] - new[0]) / (old[1] - old[0])) + new[0]
        return int(x), h_w[1] - int(y)
