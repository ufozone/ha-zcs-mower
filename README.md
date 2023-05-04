# ZCS Lawn Mower Robot

> :warning: **This integration is in development.**

ZCS Lawn Mower Robots platform as a Custom Component for Home Assistant. Ambrogio, Techline, Wiper and old Stiga and Kubota robotic lawn mowers with Connect module are supported.

## Installation
* First: This is not a Home Assistant Add-On. It's a custom component.
* There are two ways to install. First you can download the folder custom_component and copy it into your Home-Assistant config folder. Second option is to install HACS (Home Assistant Custom Component Store) and select "ZCS Lawn Mower Robot" from the Integrations catalog.
* Restart Home Assistant after installation
* Make sure that you refresh your browser window too
* Use the "Add Integration" in Home Assistant, Settings, Devices & Services and select "ZCS Lawn Mower Robot"
* In the best case, create a new account (via the mobile app) and connect it to your lawn mower(s). Then there should be no problems when you use the HA integration and the mobile app at the same time.
* Get account key and IMEI from lawn mower:
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

## Available components 

### General

* all entities

    ```
    attributes: 
    imei, connected, last_communication, last_seen, last_poll
    ```

### Binary Sensors

* error

    ```
    attributes: 
    reason
    ```

### Device Tracker

* location

### Sensors

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

### Services

* set_profile
  Configure the profile for auto-mode.
  
* work_until
  Command the lawn mower to mow until a certain time.
  
* border_cut
  Command the lawn mower to cut the border.
  
* charge_until
  Command the lawn mower to charge until a certain time.
  
* trace_position
  Command the lawn mower to report its current position.

### Logging

Set the logging to debug with the following settings in case of problems.

```
logger:
  default: warn
  logs:
    custom_components.zcsmower: debug
```
