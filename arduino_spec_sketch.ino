/*
 * Macro Definitions
 */

#define SPEC_TRG         A0
#define SPEC_ST          A1
#define SPEC_CLK         A2
#define SPEC_VIDEO       A3
#define WHITE_LED        A4
#define LASER_404        A5

#define SPEC_CHANNELS    288 // New Spec Channel
uint16_t data[SPEC_CHANNELS];
int n;
const int buttonPin = 2;     // the number of the pushbutton pin
const int ledPin =  13; 
const int volts = 7;
int buttonState = 0; 

int N = 1;
int num_runs = 0;

void setup(){
  
// initialize the LED pin as an output:
  pinMode(ledPin, OUTPUT);
  pinMode(volts, OUTPUT);
  // initialize the pushbutton pin as an input:
  pinMode(buttonPin, INPUT);

  //Set desired pins to OUTPUT
  pinMode(SPEC_CLK, OUTPUT);
  pinMode(SPEC_ST, OUTPUT);
  pinMode(LASER_404, OUTPUT);
  pinMode(WHITE_LED, OUTPUT);

  digitalWrite(SPEC_CLK, LOW); // Set SPEC_CLK High
  digitalWrite(SPEC_ST, LOW); // Set SPEC_ST Low
  digitalWrite(WHITE_LED, LOW);
  digitalWrite(volts, HIGH);

  Serial.begin(115200); // Baud Rate set to 115200
  
}

/*
 * This functions reads spectrometer data from SPEC_VIDEO
 * Look at the Timing Chart in the Datasheet for more info
 */
void readSpectrometer(){

  float delayTime = 1; // delay time
  float intTime = 60;

  // Start clock cycle and set start pulse to signal start
  digitalWrite(SPEC_CLK, HIGH);
  delayMicroseconds(delayTime);
  digitalWrite(SPEC_CLK, LOW);
  digitalWrite(SPEC_ST, HIGH);
  delayMicroseconds(delayTime);

  //Sample for a period of time
  for(int i = 0; i < 3; i++){

      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime); 
 
  }
 int blockTime = delayTime * 8;
  long int numIntegrationBlocks = ((long)intTime * (long)1000) / (long)blockTime;
  for (int i = 0; i < numIntegrationBlocks; i++) {
     digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime); 
 
  }
  //Set SPEC_ST to low
  digitalWrite(SPEC_ST, LOW);

  //Sample for a period of time
  for(int i = 0; i < 89; i++){

      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime); 
      
  }

  //Read from SPEC_VIDEO
  for(int i = 0; i < SPEC_CHANNELS; i++){
    
      data[i] = analogRead(SPEC_VIDEO);
      delayMicroseconds(100);
      
      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime);
        
  }

  //Set SPEC_ST to high
  digitalWrite(SPEC_ST, HIGH);
/*
  //Sample for a small amount of time
  for(int i = 0; i < 7; i++){
    
      digitalWrite(SPEC_CLK, HIGH);
      delayMicroseconds(delayTime);
      digitalWrite(SPEC_CLK, LOW);
      delayMicroseconds(delayTime);
    
  }
*/
  digitalWrite(SPEC_CLK, LOW);
  delayMicroseconds(delayTime);
  
}

/*
 * The function below prints out data to the terminal or 
 * processing plot
 */
void printData(){
  
  for (int i = 0; i < SPEC_CHANNELS; i++){
    
    Serial.println(data[i] + ',');
  }
  
  Serial.print("\n");
}

void loop(){
  // read the state of the pushbutton value:
 // buttonState = digitalRead(buttonPin);

  // check if the pushbutton is pressed. If it is, the buttonState is HIGH:
 /// if (buttonState == LOW) {
    // turn LED on:
    
   if(Serial.available()){
    n = Serial.read();
      if (n == 's') {
          readSpectrometer();
          printData();
         delay(10);
       }
  } else {
 delay(1);
  }
//  printData();
  
}
