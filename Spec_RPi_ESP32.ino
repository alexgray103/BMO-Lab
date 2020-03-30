// Based on work down by Steven Cogswell
// Demo Code for SerialCommand Library
// May 2011

#include <SerialCommand.h> /* http://github.com/p-v-o-s/Arduino-SerialCommand */
///download the ZIP from github to get library and simple serial examples

#define LED 2   // Arduino LED on board

#define SPEC_ST          15
#define SPEC_CLK         16
#define SPEC_VIDEO       4
#define WHITE_LED        5
#define LASER_404        17

SerialCommand sCmd;     // SerialCommand object

#include <elapsedMillis.h>  // Need to insert library
//#include <digitalWriteFast.h>  /// look up github and add ZIP file to arduino

#define SPEC_CHANNELS    288 // New Spec Channel
uint16_t data[SPEC_CHANNELS];

int duration_micros = 300;  /// min value is 150 uSec
int timer_usec = 0;
float delayTime = 1;
int integration_time = 500; // default integ time is 200 usec 


void setup() {
  // Test for serial command to make sure there is still connection 
  pinMode(LED, OUTPUT);      // Configure the onboard LED for output
  digitalWrite(LED, LOW);    // default to LED off

  //Set desired pins to OUTPUT for spectrometer 
  pinMode(SPEC_CLK, OUTPUT);
  pinMode(SPEC_ST, OUTPUT);
  pinMode(LASER_404, OUTPUT);
  pinMode(WHITE_LED, OUTPUT);

  digitalWrite(SPEC_CLK, LOW); // Set SPEC_CLK High
  digitalWrite(SPEC_ST, LOW); // Set SPEC_ST Low
  digitalWrite(WHITE_LED, LOW);


  Serial.begin(115200);
  // Setup callbacks for SerialCommand commands
  sCmd.addCommand("ON",    LED_on);          // Turns LED on
  sCmd.addCommand("OFF",   LED_off);         // Turns LED off   
  sCmd.addCommand("set_integ",  integ_time);  // Converts two arguments to integers and echos them back
  sCmd.addCommand("read", read_value);   /// read the data
}

void loop() {
  sCmd.readSerial();     // We don't do much, just process serial commands
 delay(10);
}

void LED_on() {
  digitalWrite(LED, HIGH);
}

void LED_off() {
  digitalWrite(LED, LOW);
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
// default integration time in micro seconds
for(int i = 0; i < 12; i++) {
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    
  }
  int timer_usec = duration_48;
  //Serial.println(timer_usec);

// start the actual sequence to meaasure
// Start clock cycle and set start pulse to signal start
  digitalWrite(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, LOW);
  digitalWrite(SPEC_ST, HIGH);
  delayMicroseconds(delayTime);

  // 3 clock pulses before integration starts
  digitalWrite(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);

  // start integration portion of the measurement 
  elapsedMicros start = 0;
  
  int integ_time = integration_time - timer_usec;
  integ_time = max(integ_time, 0);
  while(start < integ_time) {
     digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime); 
  }
  // set ST pin low to signal end of integration after 48 more CLK pulses
  digitalWrite(SPEC_ST, LOW);
  //Serial.println(start);
  
  elapsedMicros start1 = 0;
  // 48 clock pulses to keep sampling (part of integration time) 
for(int i = 0; i < 12; i++) {
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    
  }
//Serial.println(start1);
for(int i = 0; i < 10; i++) {
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, HIGH);
    delayMicroseconds(delayTime);
    digitalWrite(SPEC_CLK, LOW);
    delayMicroseconds(delayTime);
  }


  //Read from SPEC_VIDEO
  for(int i = 0; i < SPEC_CHANNELS; i++){
    
      data[i] = analogRead(SPEC_VIDEO);
      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime);

  }
  
  //Set SPEC_ST to high
  digitalWrite(SPEC_ST, HIGH);

 // digitalWrite(SPEC_CLK, LOW);
  //delayMicroseconds(delayTime);
  
  delay(10);
  
  for (int i = 0; i < SPEC_CHANNELS-1; i++){
    Serial.print(data[i]);
    Serial.print(',');
    
  }
  Serial.print(data[SPEC_CHANNELS - 1]);
  Serial.print("\n");
}
