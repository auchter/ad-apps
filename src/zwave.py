import appdaemon.plugins.hass.hassapi as hass

# Ping Zwave entities that become unavailable in an attempt to revive them
class ZwavePinger(hass.Hass):
    def initialize(self):
        self.entity = self.args.get('entity')
        self.ping_entity = self.args.get('ping_entity')
        self.ping_timer = None
        self.listen_state(self.state_cb, self.entity, immediate=True)

    def state_cb(self, entity, attribute, old, new, *kwargs):
        if new == 'unavailable':
            self.log(f'{self.entity} is unavailable, starting the machine that goes PING')
            self.ping()
        else:
            if self.ping_timer is not None:
                self.log(f'{self.entity} state transitioned to {new} after ping, cancelling timer')
                self.cancel_timer(self.ping_timer, silent=True)
                self.ping_timer = None

    def ping(self, *kwargs):
        self.log(f'pinging {self.entity} using {self.ping_entity}')
        self.call_service('button/press', entity_id=self.ping_entity)
        self.ping_timer = self.run_in(self.ping, delay=300)
