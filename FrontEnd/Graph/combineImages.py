from mod_python import apache
from pprint import pformat as pf
import Image,os,base64, StringIO

def index(req):
	try:
		os.remove(os.getcwd()+"\\Graph.png")
	except:
		pass

	req.content_type = "text/plain"
	#req.write(pf(req.form.keys()))
	images = {}
	
	for key, field in reversed(req.form.items()):
		buffer = StringIO.StringIO()
		buffer.write(base64.b64decode(str(field)[22:]))
		buffer.seek(0)
		images[key] = Image.open(buffer)
		
	
	background = Image.new("RGB", images[images.keys()[0]].size, "white")
	for key, img in images.items():
		foreground = img
		background.paste(foreground, (0,0), foreground)
	
	
	final = StringIO.StringIO()
	
	background.save(final, "png")
	req.write(base64.b64encode( final.getvalue()) )

def autocrop(padding,im):
	print im
	pixmap = im.load()

	ylist = list(range(int(im.size[1]*0.5)))
	xlist = list(range(int(im.size[0]*0.5)))
	ylistr = list(range(int(im.size[1]*0.5),im.size[1]))
	xlistr = list(range(int(im.size[0]*0.5),im.size[0]))

	xvs,yvs,xvs2,yvs2 = [],[],[],[]

	for x in xlist:
		for y in ylist:
			if pixmap[x,y] != (44,44,44,255):
				xvs.append(x)
				yvs.append(y)
				break
				
	for x in reversed(xlistr):		
		for y in reversed(ylistr):
			if pixmap[x,y] != (44,44,44,255):
				xvs2.append(x)
				yvs2.append(y)
				break
				
	tlx = 0 if min(xvs)-padding < 0 else min(xvs)-padding
	tly = 0 if min(yvs)-padding < 0 else min(yvs)-padding
	brx = im.size[0] if max(xvs2)+padding > im.size[0] else max(xvs2)+padding 
	bry = im.size[1] if max(yvs2)+padding > im.size[1] else max(yvs2)+padding 

	box = (tlx, tly,brx,bry)
	print box
	im = im.crop( box )
	
	return im