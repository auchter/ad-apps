import appdaemon.plugins.hass.hassapi as hass

# snapcast_entity: the media_player for snapcast
# switch_entity: the power switch
# volume_entity: the input_number that controls the volume.
# Overall behavior:
#   - If the input volume changes from 0 to nonzero:
#      - turn on the switch entity
#      - set the input volume to the media_player state.
#   - After, mirror the input-volume to the media_player volume and vice-versa
#   - If the input volume goes to zero, schedule a 30 minute timer. Turn off the switch if the volume remains at this level.
class Snapcast(hass.Hass):
    def initialize(self):
        self.snapcast_entity = self.args.get('snapcast_entity')
        self.switch_entity = self.args.get('switch_entity')
        self.volume_entity = self.args.get('volume_entity')
        self.power_off_timer = None

        self.listen_state(self.volume_cb, self.volume_entity, immediate=True)
        self.listen_state(self.sc_volume_cb, self.snapcast_entity, attribute='volume_level', immediate=True, duration=1)

    def volume_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f'volume cb, old: {old}, new: {new}, t: {type(new)}')
        if new is None:
            return
        vol = float(new)
        if vol == 0.0:
            self.log('scheduling power off')
            self.power_off_timer = self.run_in(self.power_off, delay=30*60)
        else:
            if self.get_state(self.switch_entity) == 'off':
                self.power_on()
            if self.power_off_timer is not None:
                self.log("cancelling power off timer")
                self.cancel_timer(self.power_off_timer, silent=True)

        self.call_service('media_player/volume_set', entity_id=self.snapcast_entity, volume_level=vol/100.0)

    def sc_volume_cb(self, entity, attribute, old, new, *kwargs):
        self.log(f'scvolume cb, old: {old}, new: {new}, t: {type(new)}')
        self.call_service('input_number/set_value', entity_id=self.volume_entity, value=new * 100.0)

    def power_on(self):
        self.log('power on')
        self.call_service('switch/turn_on', entity_id=self.switch_entity)
        self.call_service('media_player/volume_mute', entity_id=self.snapcast_entity, is_volume_muted=False)

    def power_off(self, *kwargs):
        self.log('power off')
        self.call_service('media_player/volume_mute', entity_id=self.snapcast_entity, is_volume_muted=True)
        self.call_service('switch/turn_off', entity_id=self.switch_entity)
