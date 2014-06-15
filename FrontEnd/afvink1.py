from Bio.Seq import Seq
from Bio.Alphabet import generic_dna
from mod_python import apache

def index(req):
    req.content_type = 'text/html'
    req.write("Typ hieronder de DNA sequentie in:")
    req.write('<form action="afvink1.py/translater" method="get"><input type="text/html" name="DNA"><input type="submit" value="Translate!"></form>')
    ##req.write('<input type="submit" value="Translate!">')


def translater(DNA,req):
    req.content_type = 'text/html'
    coding_dna = Seq(DNA, generic_dna)
    trans = coding_dna.translate()
    req.write("Hieronder staat de translatie:")
    req.write("<BR><textarea>"+str(trans)+"</textarea><BR>")
    req.write('<form action="http://cytosine.nl/~owe8_pg1/Thierry/afvink1.py"><BR><input type="submit" value="Terug"></form>')
