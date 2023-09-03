import appdaemon.plugins.hass.hassapi as hass

class GroupControl(hass.Hass):
    def initialize(self):
        self.listen_state(self.control_cb, self.args.get('control'))

    def control_cb(self, entity, attribute, old, new, *kwargs):
        actions = self.args.get(f'turned_{new}')

        if 'turn_off' in actions:
            for entity in actions['turn_off']:
                self.turn_off(entity)

        if 'turn_on' in actions:
            for entity in actions['turn_on']:
                self.turn_on(entity)
        
        if 'call_service' in actions:
            for svc in actions['call_service']:
                self.call_service(**svc)


class Light:
    def __init__(self, hass, entity):
        self.entity = entity
        self.hass = hass
        self.state = None
        self.brightness = None
        self.kelvin = None

    def set_state(self, state):
        self.state = state

    def set_brightness(self, brightness):
        self.brightness = brightness

    def set_kelvin(self, kelvin):
        self.kelvin = kelvin

    def commit(self):
        if self.state is None or self.kelvin is None or self.brightness is None:
            return
        if self.state:
            self.hass.turn_on(self.entity, brightness=self.brightness, color_temp_kelvin=self.kelvin)
        else:
            self.hass.turn_off(self.entity)

# WhiteLight is for a Light with a fixed color temperature.  min/max kelvin
# specify the color temperatures for which this light should be on; generally
# this is a range around the light's color temperature such that it will blend
# in with the other lights with adjustable color temperatures
class WhiteLight(Light):
    def __init__(self, hass, entity, min_kelvin, max_kelvin):
        super().__init__(hass, entity)
        self.min_kelvin = min_kelvin
        self.max_kelvin = max_kelvin

    def commit(self):
        if self.state is None or self.brightness is None:
            return
        if self.state and self.kelvin >= self.min_kelvin and self.kelvin <= self.max_kelvin:
            self.hass.turn_on(self.entity, brightness=self.brightness)
        else:
            self.hass.turn_off(self.entity)


class SlaveLights(hass.Hass):
    def initialize(self):
        self.slaves = []
        for e in self.args.get('slaves'):
            entity = e['entity']
            if 'min_kelvin' in e and 'max_kelvin' in e:
                self.slaves.append(WhiteLight(self, entity, e['min_kelvin'], e['max_kelvin']))
            else:
                self.slaves.append(Light(self, entity))

        master = self.args.get('master')
        self.listen_state(self.brightness_cb, master, attribute='brightness', immediate=True)
        self.listen_state(self.temp_cb, master, attribute='color_temp_kelvin', immediate=True)
        self.listen_state(self.state_cb, master, immediate=True)

    def state_cb(self, entity, attribute, old, new, *kwargs):
        for s in self.slaves:
            s.set_state(new == 'on')
            s.commit()

    def brightness_cb(self, entity, attribute, old, new, *kwargs):
        if new is None:
            return
        for s in self.slaves:
            s.set_brightness(new)
            s.commit()

    def temp_cb(self, entity, attribute, old, new, *kwargs):
        if new is None:
            return
        for s in self.slaves:
            s.set_kelvin(new)
            s.commit()

