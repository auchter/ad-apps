import appdaemon.plugins.hass.hassapi as hass
from datetime import date

# 1: bedroom
# 16: office
# 21: rug

class Vacuum(hass.Hass):
    def initialize(self):
        self.log("init Vacuum")

        self.vacuum_entity = self.args.get('vacuum_entity')
        self.listen_state(self.button_cb, self.args.get('button_entity'))
        self.areas = self.args.get('areas')
        self.listen_state(self.presence_cb, self.args.get('presence_entity'), duration=10)

    def presence_cb(self, entity, attribute, old, new, *kwargs):
        if new != 'home':
            self.vacuum_daily()

    def button_cb(self, entity, attribute, old, new, *kwargs):
        segments = []
        for name, opts in self.areas.items():
            if 'enable' in opts:
                if self.get_state(opts['enable']) == 'off':
                    self.log(f'skipping area {name}')
                    continue
            segments.append(opts['segment'])

        self.run_vacuum(segments)

    def run_vacuum(self, segments):
        self.log(f"vacuuming {segments}")
        self.call_service('xiaomi_miio/vacuum_clean_segment',
                          entity_id=self.vacuum_entity, segments=segments)
        self.update_vacuumed(segments)

    def get_date(self, entity):
        s = self.get_state(entity)
        return date.fromisoformat(s)

    def update_date(self, entity):
        self.call_service('input_datetime/set_datetime', entity_id=entity,
                          date=str(date.today()))
        
    def update_vacuumed(self, segments):
        for name, opts in self.areas.items():
            if opts['segment'] in segments and 'dt' in opts:
                self.update_date(opts['dt'])

    def vacuum_daily(self):
        segments = []
        for area in self.args.get('daily'):
            if area not in self.areas:
                self.log(f"warning, did not find {area}")
                continue
            opts = self.areas[area]
            if date.today() > self.get_date(opts['dt']):
                segments.append(opts['segment'])

        self.log(f"Going to vacuum: {segments}")
        if len(segments) > 0:
            self.run_vacuum(segments)
