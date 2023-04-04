# %%
import init
from controllably.Transfer.Liquid.Pumps.TriContinent import TriContinent
me = TriContinent('COM6', channel=[1,2], model='C3000',capacity=1000, output_right=True, name=['first', 'second'])
# %%
me.cycle(2)
me.move('up', 40)
me.moveBy(-50)
me.moveTo(300)
me.getPosition()
me.getStatus()
