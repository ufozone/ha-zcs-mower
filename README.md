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

> :warning: **This integration is in development.**

ZCS Lawn Mower Robots platform as a Custom Component for Home Assistant. Ambrogio, Techline, Wiper, Kubota, Stiga and Wolf robotic lawn mowers with Connect module are supported.

## Installation
* First: This is not a Home Assistant Add-On. It's a custom component.
* There are three ways to install:
    * First you can download the folder custom_component and copy it into your Home-Assistant config folder.
    * Second option is to install HACS (Home Assistant Custom Component Store) and visit the HACS _Integrations_ pane and add `https://github.com/ufozone/ha-zcs-mower.git` as an `Integration` by following [these instructions](https://hacs.xyz/docs/faq/custom_repositories/). You'll then be able to install it through the _Integrations_ pane.
    * ~~Third option is to install HACS (Home Assistant Custom Component Store) and select "ZCS Lawn Mower Robot" from the Integrations catalog.~~
* Restart Home Assistant after installation.
* Make sure that you refresh your browser window too.
* Use the "Add Integration" in Home Assistant, Settings, Devices & Services and select "ZCS Lawn Mower Robot".
* In the best case, create a new account (via the mobile app) and connect it to your lawn mower(s). Then there should be no problems when you use the HA integration and the mobile app at the same time.
* Get client key and IMEI from lawn mower:
    * Open the app on your mobile device.
    * Click on the `Setup` tab.
    * In the `Connect Settings` section, click `Registered "Connect Clients"`:
    * ![Registered "Connect Clients"](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/setup_account1.jpg?raw=true)
    * You need your account key (italicized string):
    * ![Get account key](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/setup_account2.jpg?raw=true)
    * Now you need the IMEI of your lawn mower
    * Click on the `More info` tab and scroll to the `Connect Informations` section:
    * ![Get IMEI address](https://github.com/ufozone/ha-zcs-mower/blob/main/screenshots/setup_imei.jpg?raw=true)
	* Type both information into the config flow dialog.
* Configure map camera:
    * The best way is to create a new map on [Google My Maps](https://mymaps.google.com/).
    * Take a snapshot of the desired area.
    * Mark the corner points and export as CSV.
    * Type the coordinates into the config flow dialog. Pay attention to the correct order of latitude and longitude.

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

### Camera

* map

    ```
    attributes: 
    calibration_points
    ```

### Device Tracker

* location

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

### Logging

Set the logging to debug with the following settings in case of problems.

```
logger:
  default: warn
  logs:
    custom_components.zcsmower: debug
```


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
