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


## Running Analysis
To run our monitor for analysis, first click `simulate` on the monitor app and add all the devices in the system to their corresponding attributes/capabilities. On the bottom of the simulation window, there should be an `API Key` and `API Endpoint`.

Under `getlog.py`, change the `API Key` and `API Endpoint` correspondingly and add any important devices in the system that you want to be alarmed if any state change for them happens to the `important` field. The `since` field can be changed accordingly to the earliest event you want to monitor, the default None looks at past seven days of events.

Finally, running `python3 getlog.py` should output an analysis file under the `output path` specified in the file.

## Obtaining Device Information Only
To obtain the events, states, and all devices in the system without doing the analysis, run the monitor on Samsung IDE similar to before. Then, follow the steps in `test.py` to obtain all the info through the structure we used to communicate to the monitor on Samsung hub.

## Analysis Details
In our analysis file, we are tracking all the direct conflicts happened in the system, which are state changes of a single device that occurs within a very short amount of time. We distinguished the bad direct conflicts, which are the conflicts that actually caused a confusion of state, such as an app is called before the app before finishes execution. We also kept track of the last five actions in the system before any important device performs a state change. 

## Future Goals
We are still under implementation for indirect conflict analysis, which are two apps may have conflicting interests such as one turn on AC while another turn on heater at the same time. Also, `Devicehandler.groovy` contains our ongoing effort to build a virtual monitor device that is able to interrupt or handle when abnormal behavior occurs.
