import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
LED=8

GPIO.setup([LED], GPIO.OUT, initial=GPIO.LOW)

GPIO.output(LED, True)
GPIO.output(LED, False)

PIEZO = 11

def my_callback(number):
    print "knock on pin {0}".format(number)

GPIO.setup([PIEZO], GPIO.IN)
GPIO.add_event_detect(PIEZO, GPIO.RISING)
GPIO.add_event_callback(PIEZO, lambda pin: my_callback(42))

