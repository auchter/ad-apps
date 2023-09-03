import appdaemon.plugins.hass.hassapi as hass
import math

def c_to_f(t):
    return (t * 1.8) + 32

def f_to_c(t):
    return (t - 32) / 1.8

def dewpoint(t, rh):
    a = 17.625
    b = 243.04
    def gamma(t, rh):
        return math.log(rh / 100.0) + ((a * t) / (b + t))
    return (b * gamma(t, rh)) / (a - gamma(t, rh))


class Dewpoint(hass.Hass):
    def initialize(self):
        self.temperature = self.get_entity(self.args.get('temperature'))
        self.humidity = self.get_entity(self.args.get('humidity'))
        self.sensor = self.get_entity(self.args.get('sensor'))
        self.sensor.add()

        self.unit_of_measurement = self.temperature.get_state(attribute='unit_of_measurement')
        self.sensor.set_state(attributes={
            'unit_of_measurement': self.unit_of_measurement,
            'state_class': 'measurement',
            'device_class': 'temperature',
            'friendly_name': self.args.get('friendly_name'),
        })

        self.temperature.listen_state(self.evaluate)
        self.humidity.listen_state(self.evaluate)
        self.evaluate(None, None, None, None, None)

    def evaluate(self, entity, attribute, old, new, kwargs):
        convert = False
        if 'F' in self.unit_of_measurement:
            convert = True

        t = float(self.temperature.get_state())
        rh = float(self.humidity.get_state())

        if convert:
            t = f_to_c(t)
        td = dewpoint(t, rh)
        if convert:
            td = c_to_f(td)
            t = c_to_f(t)

        td = round(td, 1)
        self.sensor.set_state(state=td)
