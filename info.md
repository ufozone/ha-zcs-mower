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

ZCS Lawn Mower Robots platform as a Custom Component for Home Assistant. Ambrogio, Techline, Wiper, Kubota, Stiga and Wolf robotic lawn mowers with Connect module are supported.

## Installation

Requires Home Assistant 2023.6.0 or newer.

### Installation through HACS

Installation using Home Assistant Community Store (HACS) is recommended.

1. If HACS is not installed, follow HACS installation and configuration at https://hacs.xyz/.

2. Visit the HACS _Integrations_ pane and add `https://github.com/ufozone/ha-zcs-mower.git` as an `Integration` by following [these instructions](https://hacs.xyz/docs/faq/custom_repositories/).

3. In HACS, search under integrations for "ZCS Lawn Mower Robot" and install.

4. Restart Home Assistant!

4. Make sure that you refresh your browser window too.

### Manual installation

1. Download the `zcsmower.zip` file from the repository [release section](https://github.com/ufozone/ha-zcs-mower/releases).

2. Extract and copy the content into the path `/config/custom_components/zcsmower` of your HA installation.

   Do **not** download directly from the `main` branch.

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

1. Open the app on your mobile device.

   In the best case, you create a new account (via the mobile app) and connect it to your lawn mower(s). Then there should be no problems when you use the HA integration and the mobile app at the same time.

2. Click on the `Setup` tab.

3. In the `Connect Settings` section, click `Registered "Connect Clients"`:

    ![Registered "Connect Clients"](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/setup_account1.jpg?raw=true)

4. You need your account key (italicized string):

    ![Get account key](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/setup_account2.jpg?raw=true)

5. Type this information into the config flow dialog.

### Map Camera

The camera entity will plot the current coordinates and location history of the lawn mower on a user provided image. To configure the entity you need to upload your desired map image and determine the coordinates of the top left corner and the bottom right corner of your selected image.

The camera entity is configured via the setup and options flow on the integration. 

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

* all entities

    ```
    attributes: 
    imei, connected, last_communication, last_seen, last_poll
    ```

### Binary Sensor

* error

    ```
    attributes: 
    reason
    ```

### Button

* work_now

* charge_now

* border_cut

* trace_position

### Camera

* map

    ```
    attributes: 
    calibration_points
    ```

### Device Tracker

* location

### Number

* work_for

* charge_for

### Sensor

* state
  | Values      | Description   |
  |-------------|---------------|
  | unknown     | Unknown       |
  | charging    | Charging      |
  | working     | Working       |
  | stop        | Stop          |
  | error       | Error         |
  | nosignal    | No signal     |
  | gotostation | Go to station |
  | gotoarea    | Go to area    |
  | bordercut   | Border cut    |

### Vacuum

* mower
  | Values      | Description       |
  |-------------|-------------------|
  | cleaning    | Mowing            |
  | docked      | Docked            |
  | paused      | Paused            |
  | idle        | Idle              |
  | returning   | Returning to dock |
  | error       | Error             |

    ```
    attributes: 
    status
    ```

### Services

* set_profile:

    Configure the profile for auto-mode.
  
* work_now:

    Command the lawn mower to mow now.
  
* work_for:

    Command the lawn mower to mow for a certain duration.
  
* work_until:

    Command the lawn mower to mow until a certain time.
  
* border_cut:

    Command the lawn mower to cut the border.
  
* charge_now:

    Command the lawn mower to charge now.
  
* charge_for:

    Command the lawn mower to charge for a certain duration.
  
* charge_until:

    Command the lawn mower to charge until a certain time.
  
* trace_position:

    Command the lawn mower to report its current position.
  
* keep_out:

    Commands the lawn mower to keep out of a location (no-go area).

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
