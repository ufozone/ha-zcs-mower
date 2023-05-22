"""ZCS Lawn Mower Robot camera platform."""
from __future__ import annotations

import io
import os
import math
import numpy as np

from PIL import (
    Image,
    ImageDraw,
)

from homeassistant.core import (
    callback,
    HomeAssistant,
)
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
from homeassistant.helpers.entity import Entity

from .const import (
    LOGGER,
    DOMAIN,
    UPDATE_INTERVAL_DEFAULT,
    UPDATE_INTERVAL_WORKING,
    MAP_POINTS_DEFAULT,
    CONF_CAMERA_ENABLE,
    CONF_IMG_PATH_MAP,
    CONF_IMG_PATH_MARKER,
    CONF_GPS_TOP_LEFT,
    CONF_GPS_BOTTOM_RIGHT,
    CONF_MAP_POINTS,
    ATTR_WORKING,
    ATTR_LOCATION_HISTORY,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ENTITY_DESCRIPTIONS = (
    CameraEntityDescription(
        key="map",
        icon="mdi:map",
        translation_key="map",
    ),
)

GpsPoint = tuple[float, float]
ImgPoint = tuple[int, int]
ImgDimensions = tuple[int, int]


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


class ZcsMowerCamera(ZcsMowerEntity, Camera):
    """Representation of a ZCS Lawn Mower Robot camera."""

    _attr_entity_registry_enabled_default = False
    _attr_frame_interval: float = UPDATE_INTERVAL_DEFAULT
    _attr_name = "Map"
    _attr_should_poll = True

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
            entity_type="camera",
            entity_key=entity_description.key,
        )
        self.content_type = "image/png"
        self.entity_description = entity_description

        self.gps_top_left = None
        self.gps_bottom_right = None

        if self.config_entry.options.get(CONF_CAMERA_ENABLE, False):
            LOGGER.debug("Camera enabled")
            self.gps_top_left = self.config_entry.options.get(CONF_GPS_TOP_LEFT, None)
            self.gps_bottom_right = self.config_entry.options.get(CONF_GPS_BOTTOM_RIGHT, None)
        else:
            LOGGER.debug("Camera disabled")
            latitude = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LATITUDE, None)
            longitude = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LONGITUDE, None)
            if latitude and longitude:
                self._attr_entity_registry_enabled_default = True
                earth_radius = 6371008  # meters
                offset = 100  # meters
                pi = 3.14159
                top_left_latitude = latitude - (offset / earth_radius) * (180 / pi)
                top_left_longitude = longitude - (offset / earth_radius) * (180 / pi) / math.cos(latitude * pi / 180)
                bottom_right_latitude = latitude + (offset / earth_radius) * (180 / pi)
                bottom_right_longitude = longitude + (offset / earth_radius) * (180 / pi) / math.cos(latitude * pi / 180)
                self.gps_top_left = (top_left_latitude, top_left_longitude)
                self.gps_bottom_right = (bottom_right_latitude, bottom_right_longitude)

        self._image = self._create_empty_map_image("Map camera initialization.")
        self._image_bytes = None
        self._image_to_bytes()
        self._generate_image()

    def _image_to_bytes(self) -> None:
        img_byte_arr = io.BytesIO()
        self._image.save(img_byte_arr, format="PNG")
        self._image_bytes = img_byte_arr.getvalue()

    def _generate_image(self) -> None:
        if self.config_entry.options.get(CONF_CAMERA_ENABLE, False):
            map_image_path = self.config_entry.options.get(CONF_IMG_PATH_MAP, None)
            if map_image_path and os.path.isfile(map_image_path):
                map_image = Image.open(map_image_path, "r")
            else:
                map_image = self._create_empty_map_image("No path configured to a map cutout.")
                LOGGER.warning("No map camera path configured")
        else:
            map_image = self._create_empty_map_image("Map camera is disabled.")
            LOGGER.warning("Map camera is disabled")

        try:
            if self.gps_top_left is not None and self.gps_bottom_right is not None:
                img_draw = ImageDraw.Draw(map_image)
                location_history = self._get_attribute(ATTR_LOCATION_HISTORY, [])
                if location_history is not None:
                    map_points_max = int(self.config_entry.options.get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT))
                    map_points = min(map_points_max, len(location_history) - 1)
                    LOGGER.debug(map_points)
                    for i in range(map_points, 0, -1):
                        point_1 = location_history[i]
                        scaled_loc_1 = self._scale_to_img(
                            point_1, (map_image.size[0], map_image.size[1])
                        )
                        point_2 = location_history[i - 1]
                        scaled_loc_2 = self._scale_to_img(
                            point_2, (map_image.size[0], map_image.size[1])
                        )
                        plot_points = self._find_points_on_line(scaled_loc_1, scaled_loc_2)
                        for p in range(0, len(plot_points) - 1, 2):
                            img_draw.line(
                                (plot_points[p], plot_points[p + 1]),
                                fill=(153, 194, 136),
                                width=2
                            )

                latitude = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LATITUDE, None)
                longitude = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LONGITUDE, None)
                if latitude and longitude:
                    map_marker_path = self.config_entry.options.get(CONF_IMG_PATH_MARKER, None)
                    if not map_marker_path or not os.path.isfile(map_marker_path):
                        map_marker_path = f"{os.path.dirname(__file__)}/resources/marker.png"
                    map_marker = Image.open(map_marker_path, "r")
                    img_w, img_h = map_marker.size
                    if img_w > img_h:
                        img_h = int((img_h / img_w) * 64)
                        img_w = 64
                    else:
                        img_w = int((img_w / img_h) * 64)
                        img_h = 64
                    map_marker = map_marker.resize((img_w, img_h))

                    location = (latitude, longitude)
                    x1, y1 = self._scale_to_img(location, (map_image.size[0], map_image.size[1]))
                    img_w, img_h = map_marker.size
                    # TODO: sometimes we get ValueError: bad transparency mask
                    try:
                        map_image.paste(
                            map_marker, (x1 - img_w // 2, y1 - img_h // 2), map_marker
                        )
                    except Exception as exception:
                        LOGGER.exception(exception)
        except Exception as exception:
            map_image = self._create_empty_map_image("Could not generate the map. Check error log for details.")
            LOGGER.exception(exception)

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
        for _i in range(dashes):
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

    def _create_empty_map_image(self, text: str = "No map") -> Image:
        """Create empty map image."""
        map_image = Image.new("RGBA", (600, 400), color=(255, 255, 255))
        img_draw = ImageDraw.Draw(map_image)
        w, h = img_draw.textsize(text.upper())
        img_draw.text(((map_image.size[0] - w) / 2, (map_image.size[1] - h) / 2), text.upper(), fill=(0, 0, 0))
        return map_image

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

    @property
    def is_streaming(self) -> bool:
        """Return true if the lawn mower is working."""
        return self._get_attribute(ATTR_WORKING, False)

    @property
    def should_poll(self) -> bool:
        """Return polling enabled."""
        return self._attr_should_poll

    def turn_off(self) -> None:
        """Disable polling for map image."""
        self._attr_should_poll = False

    def turn_on(self) -> None:
        """Enable polling for map image."""
        self._attr_should_poll = True

    async def async_update(self) -> None:
        """Handle map image update."""
        self._generate_image()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator and set frame interval according to working status."""
        super()._handle_coordinator_update()
        self._generate_image()

        if self._get_attribute(ATTR_WORKING, False):
            self._attr_frame_interval = UPDATE_INTERVAL_WORKING
        else:
            self._attr_frame_interval = UPDATE_INTERVAL_DEFAULT
