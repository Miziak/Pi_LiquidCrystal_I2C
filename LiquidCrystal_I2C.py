import smbus
import time

def delayMicroseconds(t):
  time.sleep(float(t)/1000000.0)

def delay(t):
  time.sleep(float(t)/1000.0)

class LiquidCrystal_I2C:

  # commands
  LCD_CLEARDISPLAY = 0x01
  LCD_RETURNHOME = 0x02
  LCD_ENTRYMODESET = 0x04
  LCD_DISPLAYCONTROL = 0x08
  LCD_CURSORSHIFT = 0x10
  LCD_FUNCTIONSET = 0x20
  LCD_SETCGRAMADDR = 0x40
  LCD_SETDDRAMADDR = 0x80

  # flags for display entry mode
  LCD_ENTRYRIGHT = 0x00
  LCD_ENTRYLEFT = 0x02
  LCD_ENTRYSHIFTINCREMENT = 0x01
  LCD_ENTRYSHIFTDECREMENT = 0x00

  # flags for display on/off control
  LCD_DISPLAYON = 0x04
  LCD_DISPLAYOFF = 0x00
  LCD_CURSORON = 0x02
  LCD_CURSOROFF = 0x00
  LCD_BLINKON = 0x01
  LCD_BLINKOFF = 0x00

  # flags for display/cursor shift
  LCD_DISPLAYMOVE = 0x08
  LCD_CURSORMOVE = 0x00
  LCD_MOVERIGHT = 0x04
  LCD_MOVELEFT = 0x00

  # flags for function set
  LCD_8BITMODE = 0x10
  LCD_4BITMODE = 0x00
  LCD_2LINE = 0x08
  LCD_1LINE = 0x00
  LCD_5x10DOTS = 0x04
  LCD_5x8DOTS = 0x00

  # flags for backlight control
  LCD_BACKLIGHT = 0x08
  LCD_NOBACKLIGHT = 0x00

  En = 0x04 # B00000100  Enable bit
  Rw = 0x02 # B00000010 Read/Write bit
  Rs = 0x01 # B00000001 Register select bit

  def __init__(self, addr, lcd_cols, lcd_rows, charsize = 0):
    self.addr = addr
    self.lcd_cols = lcd_cols
    self.lcd_rows = lcd_rows
    self.charsize = charsize
    self.backlightval = self.LCD_BACKLIGHT

  def begin(self, busNo = 0):
    self.bus = smbus.SMBus(busNo)
    self.displayfunction = self.LCD_4BITMODE | self.LCD_1LINE | self.LCD_5x8DOTS  

    if self.lcd_rows > 1:
      self.displayfunction |= self.LCD_2LINE

    # for some 1 line displays you can select a 10 pixel high font
    if self.charsize != 0 and self.lcd_rows == 1:
      self.displayfunction |= self.LCD_5x10DOTS

    # SEE PAGE 45/46 FOR INITIALIZATION SPECIFICATION!
    # according to datasheet, we need at least 40ms after power rises above 2.7V
    # before sending commands. Arduino can turn on way befer 4.5V so we'll wait 50     
    delay(50)

    # Now we pull both RS and R/W low to begin commands
    self.expanderWrite(self.backlightval)
    delay(1000)

    # put the LCD into 4 bit mode
    # this is according to the hitachi HD44780 datasheet
    # figure 24, pg 46

    # we start in 8bit mode, try to set 4 bit mode
    self.write4bits(0x03 << 4)
    delayMicroseconds(4500) # wait min 4.1ms

    # second try
    self.write4bits(0x03 << 4)
    delayMicroseconds(4500) # wait min 4.1ms

    # third go!
    self.write4bits(0x03 << 4)
    delayMicroseconds(150)

    # finally, set to 4-bit interface
    self.write4bits(0x02 << 4)

    # set # lines, font size, etc.
    self.command(self.LCD_FUNCTIONSET | self.displayfunction)

    # turn the display on with no cursor or blinking default
    self.displaycontrol = self.LCD_DISPLAYON | self.LCD_CURSOROFF | self.LCD_BLINKOFF
    self.display()

    # clear it off
    self.clear()

    # Initialize to default text direction (for roman languages)
    self.displaymode = self.LCD_ENTRYLEFT | self.LCD_ENTRYSHIFTDECREMENT;

    # set the entry mode
    self.command(self.LCD_ENTRYMODESET | self.displaymode);

    self.home()

  #********** high level commands, for the user! *#

  def clear(self):
    self.command(self.LCD_CLEARDISPLAY) # clear display, set cursor position to zero
    delayMicroseconds(2000) # this command takes a long time!

  def home(self):
    self.command(self.LCD_RETURNHOME) # set cursor position to zero
    delayMicroseconds(2000) # this command takes a long time!

  def setCursor(self, col, row):
    row_offsets = [ 0x00, 0x40, 0x14, 0x54 ]
    if row > self.lcd_rows:
      row = self.lcd_rows-1 # we count rows starting w/0

    self.command(self.LCD_SETDDRAMADDR | (col + row_offsets[row]));

  # Turn the display on/off (quickly)
  def noDisplay(self):
    self.displaycontrol &= ~self.LCD_DISPLAYON;
    self.command(self.LCD_DISPLAYCONTROL | self.displaycontrol);

  def display(self):
    self.displaycontrol |= self.LCD_DISPLAYON
    self.command(self.LCD_DISPLAYCONTROL | self.displaycontrol)

  def noBacklight(self):
    self.backlightval = self.LCD_NOBACKLIGHT;
    self.expanderWrite(0);

  def backlight(self):
    self.backlightval = self.LCD_BACKLIGHT;
    self.expanderWrite(0);

  #*********** print functions ***************************#

  def writeBuf(self, buffer):
    n = 0;
    while n < len(buffer):
      if self.write(ord(buffer[n])):
        n+=1
      else:
        break

    return n

  def printStr(self, s):
    return self.writeBuf(s)

  def printNumber(self, n):
    return self.writeBuf(str(n))

  #*********** mid level commands, for sending data/cmds *#

  def command(self, value):
    self.send(value, 0)

  def write(self, value):
    self.send(value, self.Rs)
    return 1

  #************ low level data pushing commands **********#

  # write either command or data
  def send(self, value, mode):
    highnib = value & 0xF0
    lownib = (value << 4) & 0xF0
    self.write4bits((highnib)|mode)
    self.write4bits((lownib)|mode)

  def write4bits(self, value):
    self.expanderWrite(value)
    self.pulseEnable(value)

  def expanderWrite(self, data):
    self.bus.write_byte(self.addr, data | self.backlightval)

  def pulseEnable(self, data):
    self.expanderWrite(data | self.En)
    delayMicroseconds(1)
    self.expanderWrite(data & ~self.En)
    delayMicroseconds(50)
