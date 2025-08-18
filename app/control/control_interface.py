from abc import ABC, abstractmethod

class Control(ABC):

  @property
  @abstractmethod
  def control_state(self):
    pass
  
  @abstractmethod
  def releaseAll():
    pass

  @abstractmethod
  def openWater():
    pass

  @abstractmethod
  def closeWater():
    pass

  @abstractmethod
  def debugWaterLevels():
    pass

  @abstractmethod
  def getLevel():
    pass

  @abstractmethod
  def cleanup():
    pass


  @abstractmethod
  def setup():
    pass

