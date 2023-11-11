import appdaemon.plugins.hass.hassapi as hass


class PatioLight(hass.Hass):
    def initialize(self):
        self.log("init patio lights")
        self.run_at_sunrise(self.sunrise_cb, offset=1800)
        self.run_at_sunset(self.sunset_cb, offset=-1800)
        self.sunset_cb()

    def sunrise_cb(self, *kwargs):
        self.log("sunrise (well a bit after) turning off light")
        for e in self.args.get('light_entities', []):
            self.turn_off(e)

    def sunset_cb(self, *kwargs):
        self.log("sunset (well a bit before) turning on light")
        for e in self.args.get('light_entities', []):
            self.turn_on(e, brightness=255, effect='effect_colorloop')


class SunBasedLights(hass.Hass):
    def initialize(self):
        self.log("Init sun based lights")
        self.elevation_threshold = 7
        self.entity = self.args.get('light_entity')

        self.dark_outside = False

        self.enable = True
        if 'enable' in self.args:
            self.listen_state(self.enable_cb, self.args.get('enable'), immediate=True)

        self.at_home = True
        if 'presence_entity' in self.args:
            self.listen_state(self.presence, self.args.get('presence_entity'), duration=10, immediate=True)

        self.listen_state(self.sun_elevation, 'sun.sun', attribute='elevation', immediate=True)

    def sun_elevation(self, entity, attribute, old, new, *kwargs):
        self.dark_outside = new < self.elevation_threshold
        self.log(f'dark_outside: {self.dark_outside}, elevation: {new}')
        self.update_light()

    def presence(self, entity, attribute, old, new, *kwargs):
        self.at_home = new == 'home'
        self.log(f'at_home: {self.at_home}')
        self.update_light()

    def enable_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f"enable: {new}")
        self.enable = new == 'on'
        self.update_light()

    def update_light(self):
        if not self.enable:
            return

        light_on = self.dark_outside and self.at_home
        light_state = self.get_state(self.entity) == 'on'
        self.log(f'light_on: {light_on}, cur: {light_state}')
        if light_on == light_state:
            return
        if light_on:
            self.turn_on(self.entity, brightness=255)
        else:
            self.turn_off(self.entity)
