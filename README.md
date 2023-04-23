# ZCS Lawn Mower Robot

> :warning: **This integration is in development.**

ZCS Lawn Mower Robots platform as a Custom Component for Home Assistant.

## Installation
* First: This is not a Home Assistant Add-On. It's a custom component.
* There are two ways to install. First you can download the folder custom_component and copy it into your Home-Assistant config folder. Second option is to install HACS (Home Assistant Custom Component Store) and select "ZCS Lawn Mower Robot" from the Integrations catalog.
* Restart Home Assistant after installation
* Make sure that you refresh your browser window too
* Use the "Add Integration" in Home Assistant, Settings, Devices & Services and select "ZCS Lawn Mower Robot"
* Get account key and IMEI from lawn mower:
    * Open the app on your mobile device.
    * Click on the `Setup` tab.
    * In the `Connect Settings` section, click `Registered "Connect Clients"`:
      ![Registered "Connect Clients"](https://github.com/ufozone/ha-zcs-mower/blob/main/setup_account1.jpg?raw=true)
    * You need your account key (italicized string):
      ![Get account key](https://github.com/ufozone/ha-zcs-mower/blob/main/setup_account2.jpg?raw=true)
    * Now you need the IMEI of your lawn mower
    * Click on the `More info` tab and scroll to the `Connect Informations` section:
      ![Get IMEI address](https://github.com/ufozone/ha-zcs-mower/blob/main/setup_imei.jpg?raw=true)
* Type both information into the config flow dialog.

## Available components 

### Binary Sensors
* _coming soon_

### Device Tracker
* _coming soon_

### Sensors
* _coming soon_

### Switches
* _coming soon_

### Backup and Restore
* In case of problems after a restore of Home Assistant, please delete the file .zcsmower-session-cache in your HA-config folder and restart HA
