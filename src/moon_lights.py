import appdaemon.plugins.hass.hassapi as hass

class MoonLights(hass.Hass):
    def initialize(self):
        self.listen_state(self.moon_cb, 'sensor.moon_phase', immediate=True)

    def moon_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f"Moon phase cb: {new} (old: {old})")
        phase_colors = self.args.get('phase_colors')

        if new not in phase_colors:
            self.log(f"{new} not in {phase_colors}")
            return
        
        color = phase_colors[new]
        self.log(f"color {color}")
        for entity in self.args.get('lifx_entities'):
            self.call_service('lifx/set_state', entity_id=entity, hs_color=color)
