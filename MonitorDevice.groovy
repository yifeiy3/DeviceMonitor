/**
 *  Monitor
 *
 *  Copyright 2020 Eric Yang
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 *  in compliance with the License. You may obtain a copy of the License at:
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
 *  on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License
 *  for the specific language governing permissions and limitations under the License.
 */
import groovy.json.JsonSlurper
import groovy.json.JsonOutput
metadata {
	definition (name: "Monitor", namespace: "Eric Yang", author: "Eric Yang", cstHandler: true) {
		capability "execute"
        attribute "lastExec", "String"
	}

	simulator {
		// TODO: define status and reply messages here
	}

	tiles {
		// TODO: define your main and details tiles here
	}
}

// parse events into attributes
def parse(String description) {
	log.debug "Parsing '${description}'"
	// TODO: handle 'data' attribute

}

// handle commands
def execute(String command) {
	log.debug "Executing 'execute with command: ${command}"
    state.last = command
    sendEvent(name:"lastExec", value:command, descriptionText: "the last event performed is ${command}")
    log.debug "Last command is: ${state.last}"
	// TODO: handle 'execute' command
}

