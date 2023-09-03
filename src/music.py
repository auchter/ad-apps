import appdaemon.plugins.hass.hassapi as hass

class MusicLightBar(hass.Hass):
    def initialize(self):
        self._playing = None
        self._loud = None
        self._timer = None
        entity = 'media_player.stereo'
        self.listen_state(self.playing_cb, entity, immediate=True)
        self.listen_state(self.loud_cb, entity, attribute='volume_level', immediate=True)
    
    def playing_cb(self, entity, attribute, old, new, *kwargs):
        self._playing = new == 'playing'
        self.update_state()
    
    def loud_cb(self, entity, attribute, old, new, *kwargs):
        self.log(new)
        self._loud = new > 0.9
        self.update_state()
        
    def _turn_on(self):
        self.turn_on("scene.wled_noise_fire")
    
    def _turn_off(self, cb_args):
        self.turn_off("light.wled")
        
    def update_state(self):
        print(self._playing, self._loud)
        if self._playing and self._loud:
            if self._timer is not None:
                self.cancel_timer(self._timer)
                self._timer = None
            self._turn_on()
        else:
            if self._timer is None:
                self._timer = self.run_in(self._turn_off, 300)