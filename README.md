# ZCS Lawn Mower Robot
[![License][license-shield]](LICENSE)
![Project Maintenance][maintenance-shield]
[![GitHub Activity][commits-shield]][commits]

[![hacs][hacsbadge]][hacs]
[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

Stable -
[![GitHub Release][stable-release-shield]][releases]
[![release-badge]][release-workflow]

Latest -
[![GitHub Release][latest-release-shield]][releases]
[![validate-badge]][validate-workflow]
[![lint-badge]][lint-workflow]
[![issues][issues-shield]][issues-link]

ZCS Lawn Mower Robots platform as a Custom Component for Home Assistant. All Ambrogio, Techline, Wiper and some Kubota, Stiga and Wolf robotic lawn mowers with Connect module are supported. This integration does not support Bluetooth connectivity with lawn mowers.

## Examples of use

With configured map and activated vacuum entity, the lawn mower can be displayed on a [Lovelace Vacuum Map card](https://github.com/PiotrMachowski/lovelace-xiaomi-vacuum-map-card):

![Lovelace Card](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/lovelace-card.jpg?raw=true)

## Installation

Requires Home Assistant 2024.2.0 or newer.

### Installation through HACS

Installation using Home Assistant Community Store (HACS) is recommended.

1. If HACS is not installed, follow HACS installation and configuration at https://hacs.xyz/.

2. Click the button below or visit the HACS _Integrations_ pane and search for "ZCS Lawn Mower Robot".

    [![my_button](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ufozone&repository=ha-zcs-mower&category=integration)

3. Install the integration.

4. Restart Home Assistant!

5. Make sure that you refresh your browser window too.

### Manual installation

1. Download the `zcsmower.zip` file from the repository [release section](https://github.com/ufozone/ha-zcs-mower/releases).

   Do **not** download directly from the `main` branch.

2. Extract and copy the content into the path `/config/custom_components/zcsmower` of your HA installation.

3. Restart Home Assistant!

4. Make sure that you refresh your browser window too.

### Setup integration

Start setup:

* Click this button:

    [![my_button](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=zcsmower)

* Or use the "Add Integration" in Home Assistant, Settings, Devices & Services and select "ZCS Lawn Mower Robot".

## Configuration

### Authorization

Get client key from lawn mower mobile app:

   **Note:** Android recommended, because in iPhone app all characters are displayed in capital letters.

1. Open the app on your mobile device.

   In the best case, you create a new account (via the mobile app) and connect it to your lawn mower(s). Then there should be no problems when you use the HA integration and the mobile app at the same time.

2. Click on the `Setup` tab.

3. In the `Connect Settings` section, click `Registered "Connect Clients"`:

    ![Registered "Connect Clients"](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/setup_account1.jpg?raw=true)

4. You need your account key (italicized string):

    ![Get account key](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/setup_account2.jpg?raw=true)

5. Type this information into the config flow dialog.

### Map

The image entity will plot the current coordinates and location history of the lawn mower on a user provided image. To configure the entity you need to upload your desired map image and determine the coordinates of the top left corner and the bottom right corner of your selected image.

The image entity is configured via the setup and options flow on the integration. 

You can then provide the path to the image you would like to use for the map and marker. 

Best practice:

1. Create a new map on [Google My Maps](https://mymaps.google.com/).

2. Take a snapshot of the desired area and save it. This has been tested with the PNG format, other formats may work. 

3. Store the snapshot into your home assistant instance, e.g. `/config/www/mower/`.

    The folder `/config/custom_components/zcsmower/resources/` is over written when the integration is updated, store the custom image in another location.

4. Type the full path to map into the config flow dialog.

5. Mark the corner points and export as CSV.

6. Type the coordinates into the config flow dialog. To enter the coordinates, ensure that they are in signed degree format and separated by a comma for example: `45.0135543,7.6181209`

    **Pay attention** to the correct order of latitude and longitude.

7. (Optional) Get a image of your lawn mower with transparent background as a marker for the current position. Store the image into your home assistant instance, e.g. `/config/www/mower/` and type the full path into the config flow dialog.

    The default marker `/config/custom_components/zcsmower/resources/marker.png` is over written when the integration is updated, store the custom image in another location.

### Add lawn mower(s)

Get IMEI from your lawn mower(s):

1. Open the app on your mobile device.

2. Click on the `More info` tab and scroll to the `Connect Informations` section:

3. You need the `Imei Address` (bold string, starts with `3`):

    ![Get IMEI address](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/setup_imei.jpg?raw=true)

4. Type this information into the config flow dialog.

## Available components

### General

* All entities

    ```
    attributes: 
    imei, connected, last_communication, last_seen, last_poll, next_poll
    ```

### Binary Sensor

* error

    ```
    attributes: 
    reason
    ```

### Button

* update_now

* work_now

* charge_now

* border_cut

* trace_position

### Camera

_This entity is deprecated and is disabled by default. Do not activate it as it will be removed in version 1.2.1. Use the [image](#image) entity instead._

* map

    ```
    attributes: 
    calibration_points
    ```

### Device Tracker

* location

    ```
    attributes: 
    latitude, longitude, source_type (GPS)
    ```

### Image

* map

    ```
    attributes: 
    calibration_points
    ```

### Lawn Mower

* mower
  | Values      | Description       | Lawn mower state(s)                         |
  |-------------|-------------------|---------------------------------------------|
  | mowing      | Mowing            | Work, Go to area, Go to station, Border cut |
  | docked      | Docked            | Charge                                      |
  | paused      | Paused            | Pause, Work standby                         |
  | error       | Error             | Error, No signal, Expired, Renewed          |

    ```
    attributes: 
    status
    ```

### Number

_These entities are disabled by default. You have to activate it if you want to use it._

* work_for

* charge_for

### Sensor

* state
  | Values       | Description   |
  |--------------|---------------|
  | unknown      | Unknown       |
  | charge       | Charge        |
  | work         | Work          |
  | pause        | Pause         |
  | fail         | Error         |
  | nosignal     | No signal     |
  | gotostation  | Go to station |
  | gotoarea     | Go to area    |
  | bordercut    | Border cut    |
  | expired      | Expired       |
  | renewed      | Renewed       |
  | work_standby | Work standby  |

### Vacuum

_This entity is disabled by default. You have to activate it if you want to use it._

* mower
  | Values      | Description       | Lawn mower state(s)                |
  |-------------|-------------------|------------------------------------|
  | cleaning    | Mowing            | Work, Go to area, Border cut       |
  | docked      | Docked            | Charge                             |
  | paused      | Paused            | Pause                              |
  | returning   | Returning to dock | Go to station                      |
  | idle        | Idle              | Work standby                       |
  | error       | Error             | Error, No signal, Expired, Renewed |

    ```
    attributes: 
    status
    ```

### Services

* `zcsmower.update_now`:

    Fetch data for lawn mower immediately from API.

* `zcsmower.set_profile`:

    Configure the profile for auto-mode.

* `zcsmower.work_now`:

    Command the lawn mower to mow now.

* `zcsmower.work_for`:

    Command the lawn mower to mow for a certain duration.

* `zcsmower.work_until`:

    Command the lawn mower to mow until a certain time.

* `zcsmower.border_cut`:

    Command the lawn mower to cut the border.

* `zcsmower.charge_now`:

    Command the lawn mower to charge now.

* `zcsmower.charge_for`:

    Command the lawn mower to charge for a certain duration.

* `zcsmower.charge_until`:

    Command the lawn mower to charge until a certain time.

* `zcsmower.trace_position`:

    Command the lawn mower to report its current position.

* `zcsmower.keep_out`:

    Commands the lawn mower to keep out of a location (no-go area).

* `zcsmower.custom_command`:

    Send a custom command to the mower, like a command for a new feature, which is not implemented yet by this integration.

## Usage

* `vacuum.start`:

    The lawn mower stats to mow, within the specified schedule.

* `vacuum.stop`:

    The lawn mower returns to the base and parks there until the next schedule starts.

* `vacuum.return_to_base`:

    Same as `vacuum.stop`.

* `button.charge_now`:

    Override schedule to charge lawn mower now.

* `button.work_now`:

    Override schedule to mow now.

* `button.border_cut`:

    Override schedule to cut the border now.

* `number.charge_for`:

    Override schedule to charge lawn mower for specified number of minutes.

* `number.work_for`:

    Override schedule to mow for specified number of minutes.

## Debugging

To enable debug logging for this integration you can control this in your Home Assistant `configuration.yaml` file.

Set the logging to debug with the following settings in case of problems:

```
logger:
  default: warn
  logs:
    custom_components.zcsmower: debug
```

After a restart detailed log entries will appear in `/config/home-assistant.log`.


***

[commits-shield]: https://img.shields.io/github/commit-activity/y/ufozone/ha-zcs-mower?style=for-the-badge
[commits]: https://github.com/ufozone/ha-zcs-mower/commits/main
[license-shield]: https://img.shields.io/github/license/ufozone/ha-zcs-mower.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-ufozone-blue.svg?style=for-the-badge

[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/

[issues-shield]: https://img.shields.io/github/issues/ufozone/ha-zcs-mower?style=flat
[issues-link]: https://github.com/ufozone/ha-zcs-mower/issues

[releases]: https://github.com/ufozone/ha-zcs-mower/releases
[stable-release-shield]: https://img.shields.io/github/v/release/ufozone/ha-zcs-mower?style=flat
[latest-release-shield]: https://img.shields.io/github/v/release/ufozone/ha-zcs-mower?include_prereleases&style=flat

[lint-badge]: https://github.com/ufozone/ha-zcs-mower/actions/workflows/lint.yaml/badge.svg
[lint-workflow]: https://github.com/ufozone/ha-zcs-mower/actions/workflows/lint.yaml
[validate-badge]: https://github.com/ufozone/ha-zcs-mower/actions/workflows/validate.yaml/badge.svg
[validate-workflow]: https://github.com/ufozone/ha-zcs-mower/actions/workflows/validate.yaml
[release-badge]: https://github.com/ufozone/ha-zcs-mower/actions/workflows/release.yaml/badge.svg
[release-workflow]: https://github.com/ufozone/ha-zcs-mower/actions/workflows/release.yaml
