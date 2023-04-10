# %%
import init
from controllably.Compound.LiquidMover import LiquidMoverSetup
from controllably import Helper, Factory

details = Factory.get_details(Helper.read_yaml('configs/skwr.yaml'))['setup']
me = LiquidMoverSetup(**details['settings'])
me.__dict__
# %%
