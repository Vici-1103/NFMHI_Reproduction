import cst.interface

de = cst.interface.DesignEnvironment()
mws = de.new_mws()

cmd = r'''
With Brick
    .Reset
    .Name "ext_block"
    .Component "component1"
    .Material "PEC"
    .Xrange "-5", "5"
    .Yrange "-5", "5"
    .Zrange "0", "10"
    .Create
End With
'''

mws.model3d.add_to_history("External Python Brick Test", cmd)
print("External CST control OK")