from LiquidCrystal_I2C import LiquidCrystal_I2C

DISPLAYADDR = 0x27	

def main():
  lcd = LiquidCrystal_I2C(DISPLAYADDR, 16, 2)
  lcd.begin()
  lcd.backlight()
  lcd.printStr('Hello World!')
  lcd.setCursor(3, 1)
  lcd.printStr('Second line!')

if __name__ == '__main__':
  main()
