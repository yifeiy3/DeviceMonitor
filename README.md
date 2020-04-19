# DeviceMonitor
Simple device monitor for Samsung SmartThings to check for anomalous behaviors at runtime

## Requirements

Under `My SmartApp`, create a monitor app with `MonitorApp.groovy`. Go to smartapp settings to make sure Oauth is enabled. You can change the attributes for devices asked in the preference section to adjust more to your need. 

For example, to add devices of the switch capability to the system, simply add following under preference section:
```
section ("Switch access") {
    input "switches",
        "capability.switch",
        title: "Switch",
        multiple: true,
        required: false
}
```
The capability.switch indicate you are adding a switch object for monitor to keep track of. For more information on the supported capabilities for devices, visit: https://docs.smartthings.com/en/latest/capabilities-reference.html

Additionally, 
- If you want to get access to all the location mode changes in the system in the analysis, create a location mode monitor device handler with `Devicehandler.groovy`,create a device using the device handler under `My Devices`, and finally create another smartapp to monitor the location mode with `LocModeMonitor.groovy`.
- If you want to perform additional analysis corresponds to specific rules for the devices in the environment, create a rule file with each rule of the format corresponding to the rules example under `rules/rule.txt` in the directory, the supported format is listed below.
```
    DO/DONT $deviceMethod THE $device WHEN $attribute OF $devicename IS $value AND $attri.....
    DO/DONT $deviceMethod ....  WHEN LOCATION MODE IS $mode
    DO/DONT SET LOCATION MODE TO $mode WHEN ...
```
## Running Analysis
To run our monitor for analysis, first click `simulate` on the monitor app and add all the devices in the system to their corresponding attributes/capabilities. On the bottom of the simulation window, there should be an `API Key` and `API Endpoint`.

Under `getlog.py`, change the `API Key` and `API Endpoint` correspondingly and add any important devices in the system that you want to be alarmed if any state change for them happens to the `important` field. The `since` field can be changed accordingly to the earliest event you want to monitor, the default None looks at past seven days of events.

If additional analysis corresponds to specfic rules is desired, provide the `rules_input`, `rules_output` field in the file.

Finally, running `python3 getlog.py` should output an analysis file under the `log_output` and `rules_output` files.

## Obtaining Device Information Only
To obtain the events, states, and all devices in the system without doing the analysis, run the monitor on Samsung IDE similar to before. Then, follow the steps in `test.py` to obtain all the info through the structure we used to communicate to the monitor on Samsung hub.

## Analysis Details
In our analysis file, we are tracking all the direct conflicts happened in the system, which are state changes of a single device that occurs within a very short amount of time. We distinguished the bad direct conflicts, which are the conflicts that actually caused a confusion of state, such as an app is called before the app before finishes execution. We also kept track of the last six actions in the system before any important device performs a state change. Example abnormal interactions can be found under the `Interactions` folder.

Additionally, if the user provides details of specific rules the system should follow, the analysis checks if any of the rules are violated and output in the log
of which app violated it under what conditions.

## Future Goals
While user provided rules can help testing for majority of possible indirect conflicts in the system such as two apps may have conflicting interests such as one turn on AC while another turn on heater at the same time, we are still trying to find a more automated analysis scheme for these conflicts without the need of user rule input. Currently, we only support simple DO and DONT rules for analysis, and we would like to expand the possible rules we can have in the system. Furthermore,we would like to explore more abnormal interactions and possibly build a virtual monitor device that is able to interrupt or handle abnormal behavior when it occurs.
