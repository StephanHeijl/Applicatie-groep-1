# querytest

from ElegantAPI import *
from models import *

n1 = Node(id=10)

q = Query(id__lt=6)
print q.execute(n1)
