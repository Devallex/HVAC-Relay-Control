import gpiod
from time import time
import waitress
import flask
import json
import werkzeug.exceptions as exceptions
from apscheduler.schedulers.background import BackgroundScheduler
from os import system
from math import floor

SHOW_STATUS = True
TICKS_PER_SECOND = 8

class Pin():
   chip = gpiod.Chip('gpiochip4')
   def __init__(self, label, id, switchout=300, timeout=1_800):
      self.label, self.id = label, id
      self.switchout, self.timeout = switchout, timeout
      self.pause, self.time_active, self.resume_after_pause = switchout, 0, False
      self.line = Pin.chip.get_line(self.id)
      self.line.request(consumer=label, type=gpiod.LINE_REQ_DIR_OUT)
   def on(self):
      if self.pause:
         return
      self.started = time()
      self.line.set_value(1)
   def off(self):
      self.line.set_value(0)
   def get(self):
      return bool(self.line.get_value())
   def take_pause(self):
      self.time_active = 0
      self.pause = self.switchout
      self.resume_after_pause = self.get()
      self.off()

app = flask.Flask("HomeAssistant-HVAC")

units = {
   "heater": Pin("Heater", 17, switchout=30, timeout=21_600),
   "cooler": Pin("Cooler", 27, switchout=300, timeout=21_600),
   "fan": Pin("Fan", 22, switchout=5, timeout=21_600),
}

def get_status():
   status = "Units:"
   for label, unit in units.items():
      status += "\n - " + unit.label + " "
      status += (unit.get() and "ON" or "OFF")
      status += (unit.resume_after_pause and " -> RESUME ON" or "")
      status += (unit.pause and (" [TIMEOUT: " + str(floor(unit.pause)) + "s]") or ((unit.timeout and unit.get() and (" [TIMEOUT IN: " + str(floor(unit.timeout - unit.time_active)) + "s]"))) or "")
   return status

@app.route("/<string:unit_name>/", methods=["GET", "POST"])
def interact(unit_name):
   if not unit_name in units:
      raise exceptions.NotFound
   unit = units[unit_name]
   
   if flask.request.method == "GET":
      print("GET:", unit.get())
      return json.dumps({"active": (unit.pause and unit.resume_after_pause) or unit.get()})
   elif flask.request.method == "POST":
      data = flask.request.get_json()
      if not "active" in data:
         raise exceptions.BadRequest
      active = data["active"] == "true"

      if unit.pause > 0:
         unit.resume_after_pause = active
      else:
         if active:
            unit.on()
         else:
            unit.resume_after_pause = False
            unit.off()
            unit.take_pause()
      print("POST:", unit.get())

      return json.dumps({
         "active": unit.get()
      })
   
@app.route("/status/", methods=["GET"])
def status():
   status = get_status()
   status += "\n<meta http-equiv='refresh' content='1'>"
   while "\n" in status:
      status = status.replace("\n", "<br>")
   return status

def display_status():
   if not SHOW_STATUS:
      return

   system("clear")
   print(get_status() + "\n")

def tick():
   for label, unit in units.items():
      if unit.time_active >= unit.timeout:
         unit.take_pause()
      if unit.pause > 0:
         if unit.get():
            unit.off()
         unit.pause -= 1 / TICKS_PER_SECOND
         if unit.pause == 0:
            if unit.resume_after_pause:
               unit.on()
               unit.resume_after_pause = False
      if unit.get():
         unit.time_active += 1 / TICKS_PER_SECOND
      
   display_status()
   
display_status()

scheduler = BackgroundScheduler()
scheduler.add_job(func=tick, trigger="interval", seconds=1 / TICKS_PER_SECOND)
scheduler.start()

waitress.serve(app, host="0.0.0.0", port=39504)
