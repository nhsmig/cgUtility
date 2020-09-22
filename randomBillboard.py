import random

sel = cmds.ls(sl = True)[0]
facetRange = cmds.polyEvaluate(f = True)
for f in range(facetRange):
	uPos = random.randint(0,15)
	vPos =  -0.125 * random.randint(0,7)
	
	print vPos
	cmds.select(sel + '.f[%d]' %f)
	cmds.polyEditUV(u=uPos, v=vPos)
	
