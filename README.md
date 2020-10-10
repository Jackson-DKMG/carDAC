# carDAC

An audio system for a car. In this case, a 2000 Jaguar XJ8 with a failing CD charger.

The system uses a Raspberry Pi Zero with a Hifiberry DAC+ Light (should work with any DAC, just need to adjust the Pi config).

Audio player is Audacious, controlled with 4 buttons. 

The system is powered by the 12V of the car (with a voltage converter to avoid frying it) and located under the armrest (there used to be the car phone stuff here). The audio cable are soldered into the main wire from the CD changer in the trunk,
so for the car, the music comes from there.
There is a switch to the voltage converter to avoid draining the battery as it is plugged on the permanent 12V.

cardac_V2 includes a 128x64 OLED display to show the currently playing track.
