import appdaemon.plugins.hass.hassapi as hass

# - enable: input boolean that enables/disables control
# - fan_entity: fan entity to control
# - presence_entity: home/away entity.
# - motion_entity: sensor to indicate motion was detected
# - timeout: how long after last motion was detected before turning off, in minutes
class FanControl(hass.Hass):
    def initialize(self):
        self.log("init FanControl")

        self.fan_entity = self.args.get('fan_entity')
        self.timeout = self.args.get('timeout', 60) * 60

        self.cached_state = None
        self.motion = False
        self.enable = True
        self.at_home = True
        self.timer = None
        if 'enable' in self.args:
            self.listen_state(self.enable_cb, self.args.get('enable'), immediate=True)

        if 'presence_entity' in self.args:
            self.listen_state(self.presence_cb, self.args.get('presence_entity'), duration=10, immediate=True)

        if 'motion_entity' in self.args:
            self.listen_state(self.motion_cb, self.args.get('motion_entity'), new_state='on')

        self.listen_state(self.fan_cb, self.args.get('fan_entity'))

    def fan_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f"fan_cb: {new}")
        self.cached_state = new == 'on'

    def motion_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f"motion_cb: {new}")
        if new == 'on':
            self.motion = True
            if self.timer is not None:
                self.cancel_timer(self.timer, silent=True)
            self.timer = self.run_in(self.timeout_cb, delay=self.timeout)
        self.update_state()

    def timeout_cb(self, *kwargs):
        self.log(f'motion timed out, turning fan off')
        self.motion = False
        self.update_state()
        
    def presence_cb(self, entity, attribute, old, new, *kwargs):
        self.at_home = new == 'home'
        self.log(f'at_home: {self.at_home}')
        self.update_state()

    def enable_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f"enable: {new}")
        self.enable = new != "off"
        self.update_state()

    def update_state(self):
        if not self.enable:
            return

        state = False
        if not self.at_home:
            state = False
        elif self.motion:
            state = True

        if state != self.cached_state:
            if state:
                self.log("Turning fan on")
                self.turn_on(self.fan_entity)
            else:
                self.log("Turning fan off")
                self.turn_off(self.fan_entity)
