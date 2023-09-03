import appdaemon.plugins.hass.hassapi as hass

# - enable: input boolean to enable/disable
# - motion_entity: sensor to indicate motion was detected
# - presence_entity: home/away
# - illuminance_entity: light sensor
# - illuminance_threshold:
#       if the illuminance is above this level and the light is off, it
#       won't be turned on.
# - illuminance_timeout
#       if the illuminance is above the threshold for this amount of time
#       and the light is on, it will be turned off
# - motion_timeout: how long after motion was last detected should the light be turned off?
# - light_entity: light to control
class LightControl(hass.Hass):
    def initialize(self):
        self.log("init LightControl")

        self.light_entity = self.args.get('light_entity')
        self.motion_timeout = self.args.get('motion_timeout', 60) * 60
        self.illuminance_threshold = float(self.args.get('illuminance_threshold'))
        self.illuminance_timeout = self.args.get('illuminance_timeout', 10) * 60

        self.cached_state = None
        self.motion = False
        self.enable = True
        self.at_home = True
        self.dark_enough = True
        self.timer = None
        self.illuminance_timer = None

        if 'enable' in self.args:
            self.listen_state(self.enable_cb, self.args.get('enable'), immediate=True)

        if 'presence_entity' in self.args:
            self.listen_state(self.presence_cb, self.args.get('presence_entity'), duration=10, immediate=True)

        if 'motion_entity' in self.args:
            self.listen_state(self.motion_cb, self.args.get('motion_entity'), new_state='on')

        if 'illuminance_entity' in self.args:
            self.listen_state(self.illuminance_cb, self.args.get('illuminance_entity'))

        self.listen_state(self.light_cb, self.args.get('light_entity'))

    def light_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f"light_cb: {new}")
        self.cached_state = new == 'on'

    def illuminance_cb(self, entity, attribute, old, new, *kwargs):
        new = float(new)
        self.log(f"illuminance_cb: {new}")
        if new < self.illuminance_threshold:
            self.log(f"illuminance_cb: below threshold")
            self.dark_enough = True
            if self.illuminance_timer is not None:
                self.cancel_timer(self.illuminance_timer)
                self.illuminance_timer = None
            self.update_state()
        elif self.illuminance_timer is None:
            self.log(f"illuminance_cb: above threshold, starting timer")
            self.illuminance_timer = self.run_in(self.ill_timer_cb, delay=self.illuminance_timeout)

    def ill_timer_cb(self, *kwargs):
        self.log(f"ill_timer_cb")
        self.dark_enough = False
        self.illuminance_timer = None
        self.update_state()

    def enable_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f"enable: {new}")
        self.enable = new != "off"
        self.update_state()

    def presence_cb(self, entity, attribute, old, new, *kwargs):
        self.at_home = new == 'home'
        self.log(f'at_home: {self.at_home}')
        self.update_state()

    def motion_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f"motion_cb: {new}")
        if new == 'on':
            self.motion = True
            if self.timer is not None:
                self.cancel_timer(self.timer, silent=True)
            self.timer = self.run_in(self.timeout_cb, delay=self.motion_timeout)
        self.update_state()

    def timeout_cb(self, *kwargs):
        self.log(f'motion timed out')
        self.motion = False
        self.update_state()

    def update_state(self):
        if not self.enable:
            return

        state = False
        if not self.at_home:
            state = False
        elif self.motion and self.dark_enough:
            state = True

        if state != self.cached_state:
            if state:
                self.log("Turning light on")
                self.turn_on(self.light_entity)
            else:
                self.log("Turning light off")
                self.turn_off(self.light_entity)

