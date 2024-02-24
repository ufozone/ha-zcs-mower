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
    CameraEntityFeature,
)
from homeassistant.helpers.entity import (
    Entity,
    EntityCategory,
)

from .const import (
    LOGGER,
    DOMAIN,
    UPDATE_INTERVAL_WORKING,
    UPDATE_INTERVAL_STANDBY,
    MAP_POINTS_DEFAULT,
    CONF_MAP_ENABLE,
    CONF_MAP_IMAGE_PATH,
    CONF_MAP_MARKER_PATH,
    CONF_MAP_GPS_TOP_LEFT,
    CONF_MAP_GPS_BOTTOM_RIGHT,
    CONF_MAP_HISTORY_ENABLE,
    CONF_MAP_POINTS,
    CONF_MAP_DRAW_LINES,
    ATTR_WORKING,
    ATTR_LOCATION_HISTORY,
    ATTR_CALIBRATION,
)
from .coordinator import ZcsMowerDataUpdateCoordinator
from .entity import ZcsMowerEntity

ENTITY_DESCRIPTIONS = (
    CameraEntityDescription(
        key="map",
        icon="mdi:map",
        translation_key="map",
        entity_category=EntityCategory.DIAGNOSTIC,
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
            ZcsMowerCameraEntity(
                hass=hass,
                config_entry=config_entry,
                coordinator=coordinator,
                entity_description=entity_description,
                imei=imei,
            )
            for imei in coordinator.mowers
            for entity_description in ENTITY_DESCRIPTIONS
        ],
        update_before_add=True,
    )


class ZcsMowerCameraEntity(ZcsMowerEntity, Camera):
    """Representation of a ZCS Lawn Mower Robot camera."""

    _attr_entity_registry_enabled_default = False
    _attr_frame_interval: float = UPDATE_INTERVAL_WORKING
    _attr_name = "Map"
    _attr_should_poll = True

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        coordinator: ZcsMowerDataUpdateCoordinator,
        entity_description: CameraEntityDescription,
        imei: str,
    ) -> None:
        """Initialize the camera class."""
        Camera.__init__(self)
        super().__init__(
            hass=hass,
            config_entry=config_entry,
            coordinator=coordinator,
            imei=imei,
            entity_type="camera",
            entity_key=entity_description.key,
        )
        self.content_type = "image/png"
        self.entity_description = entity_description

        self.gps_top_left = None
        self.gps_bottom_right = None

        self._attr_entity_registry_enabled_default = self.config_entry.options.get(CONF_MAP_ENABLE, False)
        if self._attr_entity_registry_enabled_default:
            LOGGER.info("Map enabled")
            self.gps_top_left = self.config_entry.options.get(CONF_MAP_GPS_TOP_LEFT, None)
            self.gps_bottom_right = self.config_entry.options.get(CONF_MAP_GPS_BOTTOM_RIGHT, None)
        else:
            LOGGER.info("Map disabled")
            latitude_current = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LATITUDE, None)
            longitude_current = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LONGITUDE, None)
            if latitude_current and longitude_current:
                earth_radius = 6371008  # meters
                offset = 100  # meters
                top_left_latitude = latitude_current - (offset / earth_radius) * (180 / math.pi)
                top_left_longitude = longitude_current - (offset / earth_radius) * (180 / math.pi) / math.cos(latitude_current * math.pi / 180)
                bottom_right_latitude = latitude_current + (offset / earth_radius) * (180 / math.pi)
                bottom_right_longitude = longitude_current + (offset / earth_radius) * (180 / math.pi) / math.cos(latitude_current * math.pi / 180)
                self.gps_top_left = (top_left_latitude, top_left_longitude)
                self.gps_bottom_right = (bottom_right_latitude, bottom_right_longitude)

        self._image = self._create_empty_map_image("Map initialization.")
        self._image_bytes = None
        self._image_to_bytes()
        self._generate_image()

    def _generate_image(self) -> None:
        """Generate image."""
        if self.config_entry.options.get(CONF_MAP_ENABLE, False):
            map_image_path = self.config_entry.options.get(CONF_MAP_IMAGE_PATH, None)
            if map_image_path and os.path.isfile(map_image_path):
                map_image = Image.open(map_image_path, "r")
                map_image = map_image.convert("RGB")
                map_image_size = self._calculate_image_size(map_image, (600, 600))
                map_image = map_image.resize(map_image_size)
            else:
                map_image = self._create_empty_map_image("No valid path configured to a map image.")
                LOGGER.warning("No valid map image path configured")
        else:
            map_image = self._create_empty_map_image("Map is disabled.")

        try:
            if self.gps_top_left is not None and self.gps_bottom_right is not None:
                img_draw = ImageDraw.Draw(map_image, "RGBA")
                latitude_current = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LATITUDE, None)
                longitude_current = self._get_attribute(ATTR_LOCATION, {}).get(ATTR_LONGITUDE, None)
                if latitude_current and longitude_current:
                    location_current = (latitude_current, longitude_current)
                else:
                    location_current = None

                # Get location history
                history_enable = self.config_entry.options.get(CONF_MAP_HISTORY_ENABLE, True)
                location_history = self._get_attribute(ATTR_LOCATION_HISTORY, [])
                if history_enable and location_history is not None:
                    # If current location is not last item in location history, append to it
                    if location_current and location_current not in location_history[-1:]:
                        LOGGER.debug("Map: Current location is not last item in location history")
                        location_history.append(location_current)

                    # Calculate map points
                    location_history_items = len(location_history)
                    map_point_max = int(self.config_entry.options.get(CONF_MAP_POINTS, MAP_POINTS_DEFAULT))
                    map_point_count = min(map_point_max, location_history_items)
                    map_point_first = location_history_items - map_point_count

                    # At first draw lines between location points, if lines should show
                    draw_lines = self.config_entry.options.get(CONF_MAP_DRAW_LINES, True)
                    if draw_lines:
                        for i in range(location_history_items - 1, map_point_first, -1):
                            point_1 = location_history[i]
                            scaled_loc_1 = self._scale_to_image(
                                point_1, map_image.size
                            )
                            point_2 = location_history[i - 1]
                            scaled_loc_2 = self._scale_to_image(
                                point_2, map_image.size
                            )
                            opacity = self._get_location_opacity(i, map_point_count, map_point_first)
                            plot_points = self._find_points_on_line(scaled_loc_1, scaled_loc_2)
                            for p in range(0, len(plot_points) - 1, 2):
                                img_draw.line(
                                    (plot_points[p], plot_points[p + 1]),
                                    fill=(64, 185, 60, opacity),
                                    width=1
                                )

                    # At second draw location points
                    marker_radius = 4
                    map_point_items = location_history_items -1 if latitude_current and longitude_current else location_history_items
                    for i in range(map_point_first, map_point_items):
                        point = location_history[i]
                        scaled_loc = self._scale_to_image(
                            point, map_image.size
                        )
                        opacity = self._get_location_opacity(i, map_point_count, map_point_first)
                        img_draw.ellipse(
                            [
                                (scaled_loc[0] - marker_radius, scaled_loc[1] - marker_radius),
                                (scaled_loc[0] + marker_radius, scaled_loc[1] + marker_radius)
                            ],
                            fill=(255, 0, 0, opacity),
                            outline=(64, 185, 60, opacity),
                            width=3
                        )

                if location_current:
                    map_marker_path = self.config_entry.options.get(CONF_MAP_MARKER_PATH, None)
                    if not map_marker_path or not os.path.isfile(map_marker_path):
                        map_marker_path = f"{os.path.dirname(__file__)}/resources/marker.png"
                    map_marker = Image.open(map_marker_path, "r")
                    map_marker_size = self._calculate_image_size(map_marker, (32, 32))
                    map_marker = map_marker.resize(map_marker_size)

                    x1, y1 = self._scale_to_image(location_current, map_image.size)
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

    def _get_location_opacity(
        self,
        loc_index: int,
        loc_count: int,
        loc_first: int | None = 0,
    ) -> int:
        """Get opacity of one location point for map."""
        return round((loc_index - loc_first) * (200 / loc_count)) + 55

    def _find_points_on_line(
        self,
        point_1: ImgPoint,
        point_2: ImgPoint,
    ) -> list[ImgPoint]:
        """Find points on line between two points."""
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
        """Get point on vector."""
        v = np.array(initial_pt, dtype=float)
        u = np.array(terminal_pt, dtype=float)
        n = v - u
        n /= np.linalg.norm(n, 2)
        point = v - distance * n

        return tuple(point)

    def _scale_to_image(
        self,
        location: GpsPoint,
        size: ImgDimensions
    ) -> ImgPoint:
        """Convert from latitude and longitude to the image pixels."""
        y_gps = (self.gps_bottom_right[0], self.gps_top_left[0])
        y_img = (0, size[1])
        y = ((location[0] - y_gps[0]) * (y_img[1] - y_img[0]) / (y_gps[1] - y_gps[0])) + y_img[0]

        x_gps = (self.gps_top_left[1], self.gps_bottom_right[1])
        x_img = (0, size[0])
        x = ((location[1] - x_gps[0]) * (x_img[1] - x_img[0]) / (x_gps[1] - x_gps[0])) + x_img[0]

        return (int(x), size[1] - int(y))

    def _calculate_image_size(
        self,
        image: Image,
        max_size: ImgDimensions,
    ) -> ImgDimensions:
        """Calculate new image size with max dimensions."""
        img_w, img_h = image.size
        max_w, max_h = max_size

        scale = max(1, max((img_w / max_w), (img_h / max_h)))
        new_w = round(img_w / scale)
        new_h = round(img_h / scale)

        return (new_w, new_h)

    def _create_empty_map_image(self, text: str = "No map") -> Image:
        """Create empty map image."""
        map_image = Image.new("RGB", (600, 400), color=(255, 255, 255))
        img_draw = ImageDraw.Draw(map_image)
        _, _, w, h = img_draw.textbbox((0,0), text.upper())
        img_draw.text(((map_image.size[0] - w) / 2, (map_image.size[1] - h) / 2), text.upper(), fill=(0, 0, 0))
        return map_image

    def _image_to_bytes(self) -> None:
        """Save generated image in variable."""
        img_byte_arr = io.BytesIO()
        self._image.save(
            img_byte_arr,
            format="PNG",
            #optimize=True,
            #compress_level=9,
        )
        self._image_bytes = img_byte_arr.getvalue()

    def _update_extra_state_attributes(self) -> None:
        """Update extra attributes."""
        if self._attr_entity_registry_enabled_default:
            calibration_points = []
            for point in [
                self.gps_top_left,
                self.gps_bottom_right,
            ]:
                img_point = self._scale_to_image(
                    (point[0], point[1]), (self._image.size[0], self._image.size[1])
                )
                calibration_points.append(
                    {
                        "vacuum": {
                            "x": point[0],
                            "y": point[1],
                        },
                        "map": {
                            "x": int(img_point[0]),
                            "y": int(img_point[1])
                        },
                    }
                )
            self._additional_extra_state_attributes = {
                ATTR_CALIBRATION: calibration_points,
            }

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
        return CameraEntityFeature.ON_OFF

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
            self._attr_frame_interval = UPDATE_INTERVAL_STANDBY
