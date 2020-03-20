// Based on work down by Steven Cogswell
// Demo Code for SerialCommand Library
// May 2011

#include <SerialCommand.h> /* http://github.com/p-v-o-s/Arduino-SerialCommand */
///download the ZIP from github to get library and simple serial examples

#define arduinoLED 13   // Arduino LED on board

#define SPEC_TRG         A0
#define SPEC_ST          A1
#define SPEC_CLK         A2
#define SPEC_VIDEO       A3
#define WHITE_LED        A4
#define LASER_404        A5

SerialCommand sCmd;     // SerialCommand object

#include <elapsedMillis.h>  // Need to insert library
#include <digitalWriteFast.h>  /// look up github and add ZIP file to arduino

#define SPEC_CHANNELS    288 // New Spec Channel
uint16_t data[SPEC_CHANNELS];

int duration_micros = 500;  /// min value is 150 uSec
int timer_usec = 0;
float delayTime = 1;
int integration_time = 200; // default integ time is 200 usec 


void setup() {
  // Test for serial command to make sure there is still connection 
  pinMode(arduinoLED, OUTPUT);      // Configure the onboard LED for output
  digitalWrite(arduinoLED, LOW);    // default to LED off

  //Set desired pins to OUTPUT for spectrometer 
  pinModeFast(SPEC_CLK, OUTPUT);
  pinModeFast(SPEC_ST, OUTPUT);
  pinModeFast(LASER_404, OUTPUT);
  pinModeFast(WHITE_LED, OUTPUT);

  digitalWriteFast(SPEC_CLK, LOW); // Set SPEC_CLK High
  digitalWriteFast(SPEC_ST, LOW); // Set SPEC_ST Low
  digitalWriteFast(WHITE_LED, LOW);


  Serial.begin(115200);

  // Setup callbacks for SerialCommand commands
  sCmd.addCommand("ON",    LED_on);          // Turns LED on
  sCmd.addCommand("OFF",   LED_off);         // Turns LED off   
  sCmd.addCommand("set_integ",  integ_time);  // Converts two arguments to integers and echos them back
  sCmd.addCommand("read", read_value);   /// read the data
  //sCmd.addCommand("print", print_Data);  // actually print the data
}

void loop() {
  sCmd.readSerial();     // We don't do much, just process serial commands
 delay(10);
}


void LED_on() {
  Serial.println("LED on");
  digitalWrite(arduinoLED, HIGH);
}

void LED_off() {
  Serial.println("LED off");
  digitalWrite(arduinoLED, LOW);
}


void integ_time() {
  int aNumber;
  char *arg;

  arg = sCmd.next();
  if (arg != NULL) {
    aNumber = atoi(arg);    // Converts a char string to an integer
    integration_time = aNumber;
    
  }
}

void read_value()
{
  // Get timing for 48 clock pulses that will be incorporated into integration time 
elapsedMicros duration_48 = 0;

for(int i = 0; i < 12; i++) {
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    
  }
  int timer_usec = duration_48;


// start the actual sequence to meaasure
// Start clock cycle and set start pulse to signal start
  digitalWriteFast(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWriteFast(SPEC_CLK, LOW);
  digitalWriteFast(SPEC_ST, HIGH);
  delayMicroseconds(delayTime);

  // 3 clock pulses before integration starts
  digitalWriteFast(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWriteFast(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);
  digitalWriteFast(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWriteFast(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);
  digitalWriteFast(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWriteFast(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);

  // start integration portion of the measurement 
  elapsedMicros start = 0;

  integration_time -= timer_usec;
  integration_time = max(integration_time, 0);
  while(start < integration_time) {
     digitalWriteFast(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWriteFast(SPEC_CLK, LOW);
      delayMicroseconds(delayTime); 
  }
  // set ST pin low to signal end of integration after 48 more CLK pulses
  digitalWriteFast(SPEC_ST, LOW);

  // 48 clock pulses to keep sampling (part of integration time) 
for(int i = 0; i < 12; i++) {
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    
  }

for(int i = 0; i < 10; i++) {
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWriteFast(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
  }
 // delay(10);

  //Read from SPEC_VIDEO
  for(int i = 0; i < SPEC_CHANNELS; i++){
    
      data[i] = analogRead(SPEC_VIDEO);
      delayMicroseconds(10);
      
      digitalWriteFast(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWriteFast(SPEC_CLK, LOW);
      delayMicroseconds(delayTime);

  }
  
  //Set SPEC_ST to high
  digitalWriteFast(SPEC_ST, HIGH);

 // digitalWriteFast(SPEC_CLK, LOW);
  //delayMicroseconds(delayTime);
  
  delay(10);
  
  for (int i = 0; i < SPEC_CHANNELS-1; i++){
    Serial.print(data[i]);
    Serial.print(',');
    
  }
  Serial.print(data[SPEC_CHANNELS - 1]);
  Serial.print("\n");
  
}
