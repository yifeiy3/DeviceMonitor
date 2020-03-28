# DeviceMonitor
Simple device monitor for Samsung SmartThings to check for anomalous behaviors at runtime

## Requirements
____________
To run, first log on to Samsung Smartthings IDE, create new device handler `monitor` under
`My Device Handler` with `DeviceHandler.groovy`

Under `My Devices`, create a new device called `Monitor Device` of type `monitor`

Under `My SmartApp`, create a monitor app with `MonitorApp.groovy`. Go to smartapp settings to make sure Oauth is enabled. You can change the attributes for devices asked in the preference section to adjust more to your need.

For each app that you want to monitor, add the following code to its source code in your environment under the preference section.
```
    section("Monitor the app using..."){
    	input "monitor", "capability.execute", required:false
    }
```
And each time the app tries to change the state of the device, add the following code before state change to send information to the monitor.
```
    monitor?.execute("AppName: $Appname, ($DeviceName $Devicestate : $value, ...)")
```
Example:
```
    monitor?.execute("AppName: Big Turn ON, ($switch1 switch : on, $switches2 switch : off)")
```
The state name and possible value of states can be obtained through the attribute description of each device capability specified in the preference section.(Our monitor has capability execute) and can be found here: https://docs.smartthings.com/en/latest/capabilities-reference.html

## Running Monitor
____
To run our monitor, first click `simulate` on the monitor app and add all the devices in the system to their corresponding attributes/capabilities. On the bottom of the simulation window, there should be an `API Key` and `API Endpoint`.

Under `getlog.py`, change the `API Key` and `API Endpoint` correspondingly and add any important devices in the system that you want to be alarmed if any state change for them happens to the `important` field.

Then, running `python3 getlog.py` should output an analysis file under the `output path` specified in the file.

## Analysis Details
___
In our analysis file, we are tracking all the direct conflicts happened in the system, which are state changes of a single device that occurs within a very short amount of time. We also kept track of the last five actions in the system before any important device performs a state change. Finally, we check the difference between actual device states to what is described in our monitor to see if there is any discrepancies in them.
