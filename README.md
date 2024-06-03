A basic python script to allow controlling of heating, fan, and AC electronic relays connected to a Rasperry Pi 5's GPIO pins over HTTP requests. Useful to provide smart functionality to systems which don't support modern smart thermostats. I used this instead of my HVAC control board, but it could also work in the place of a thermostat.

[Home Assistant's Rasperry Pi GPIO Integration](https://www.home-assistant.io/integrations/remote_rpi_gpio/) doesn't work with the Pi 5s, so I used the [RESTful Integration](https://www.home-assistant.io/integrations/rest/) instead in combination with this webserver. Also, run this script as a linux service rather than with HA's python integration.

This might not be the best way to do this, but now I can control my old HVAC system with Home Assistant instantly. To get an actual digital thermostat, I used [this dual smart thermostat integration](https://github.com/swingerman/ha-dual-smart-thermostat).
