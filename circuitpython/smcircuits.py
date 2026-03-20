import digitalio
import analogio
import pwmio
import simpleio
import audiopwmio
import audiocore
from time import sleep

class LEDArray:
    def __init__(self, *pins, pwm=False):
        self.pwm = pwm
        self.leds = []
        for pin in pins:
            if pwm:
                led = pwmio.PWMOut(pin, frequency=1000)
            else:
                led = digitalio.DigitalInOut(pin)
                led.direction = digitalio.Direction.OUTPUT
                led.value = False
            self.leds.append(led)

    def _to_duty(self, value):
        """Convert 0-255 to 0-65535 duty cycle."""
        return int((value / 255) * 65535)

    def set_index(self, index, value):
        """Set a single LED by index.
        value is 0-255 for PWM, or True/False for digital."""
        if self.pwm:
            self.leds[index].duty_cycle = self._to_duty(value)
        else:
            self.leds[index].value = bool(value)

    def set(self, n, brightness=255):
        """Light the first n LEDs.
        brightness is 0-255 and only applies in PWM mode."""
        for i, led in enumerate(self.leds):
            if self.pwm:
                led.duty_cycle = self._to_duty(brightness) if i < n else 0
            else:
                led.value = i < n

    def set_all(self, value):
        """Turn all LEDs on or off.
        value is 0-255 for PWM, or True/False for digital."""
        for led in self.leds:
            if self.pwm:
                led.duty_cycle = self._to_duty(value)
            else:
                led.value = bool(value)

    def set_list(self, values):
        """Set each LED individually from a list.
        values is a list of 0-255 for PWM, or True/False for digital."""
        for i, value in enumerate(values):
            if i < len(self.leds):
                self.set_index(i, value)

    def clear(self):
        """Turn off all LEDs."""
        self.set_all(0 if self.pwm else False)

    def fill(self):
        """Turn on all LEDs at full brightness."""
        self.set_all(255 if self.pwm else True)


class RGBLED:
    def __init__(self, r_pin, g_pin, b_pin):
        self.r = pwmio.PWMOut(r_pin, frequency=1000)
        self.g = pwmio.PWMOut(g_pin, frequency=1000)
        self.b = pwmio.PWMOut(b_pin, frequency=1000)

    def _to_duty(self, value):
        """Convert 0-255 to 0-65535 duty cycle."""
        return int((value / 255) * 65535)

    def set(self, r, g, b):
        """Set the RGB LED color. r, g, b are 0-255."""
        self.r.duty_cycle = self._to_duty(r)
        self.g.duty_cycle = self._to_duty(g)
        self.b.duty_cycle = self._to_duty(b)

    def clear(self):
        """Turn off the RGB LED."""
        self.set(0, 0, 0)

    # Convenience colors
    def red(self,     brightness=255): self.set(brightness, 0,          0         )
    def green(self,   brightness=255): self.set(0,          brightness, 0         )
    def blue(self,    brightness=255): self.set(0,          0,          brightness)
    def yellow(self,  brightness=255): self.set(brightness, brightness, 0         )
    def cyan(self,    brightness=255): self.set(0,          brightness, brightness)
    def magenta(self, brightness=255): self.set(brightness, 0,          brightness)
    def white(self,   brightness=255): self.set(brightness, brightness, brightness)


class LDR:
    def __init__(self, pin):
        self.sensor = analogio.AnalogIn(pin)

    @property
    def value(self):
        """Raw analog value (0-65535)."""
        return self.sensor.value

    @property
    def level(self):
        """Light level mapped to 0-255."""
        return int((self.sensor.value / 65535) * 255)


class TiltSensor:
    def __init__(self, pin):
        self.pin = digitalio.DigitalInOut(pin)
        self.pin.direction = digitalio.Direction.INPUT
        self.pin.pull = digitalio.Pull.UP

    @property
    def tilted(self):
        """Returns True when tilted."""
        return not self.pin.value


class Button:
    def __init__(self, pin):
        self.pin = digitalio.DigitalInOut(pin)
        self.pin.direction = digitalio.Direction.INPUT
        self.pin.pull = digitalio.Pull.UP
        self._pressed = False
        self.on_press = lambda: None
        self.on_release = lambda: None

    @property
    def value(self):
        """Returns True when pressed."""
        return not self.pin.value

    def update(self):
        """Call in main loop to trigger on_press and on_release callbacks."""
        if self.value and not self._pressed:
            self._pressed = True
            self.on_press()
        elif not self.value and self._pressed:
            self._pressed = False
            self.on_release()


class VR:
    def __init__(self, pin):
        self.sensor = analogio.AnalogIn(pin)

    @property
    def value(self):
        """Raw analog value (0-65535)."""
        return self.sensor.value

    @property
    def ratio(self):
        """Value mapped to 0.0-1.0."""
        return self.sensor.value / 65535

    def map(self, min_val, max_val):
        """Map the potentiometer value to a custom range."""
        return min_val + (self.ratio * (max_val - min_val))


class Speaker:
    def __init__(self, pin):
        self._pwm = pwmio.PWMOut(pin, duty_cycle=0, frequency=440, variable_frequency=True)

    def beep(self, frequency, duration):
        """Play a tone at a frequency for a duration."""
        self._pwm.frequency = int(frequency)
        self._pwm.duty_cycle = 32768
        sleep(duration)
        self._pwm.duty_cycle = 0

    def play_wav(self, filename):
        """Play a WAV file (16-bit PCM mono, 22050Hz or lower)."""
        self._pwm.duty_cycle = 0
        speaker = audiopwmio.PWMAudioOut(self._pwm)
        wave = audiocore.WaveFile(open(filename, "rb"))
        speaker.play(wave)
        while speaker.playing:
            pass
        speaker.deinit()
