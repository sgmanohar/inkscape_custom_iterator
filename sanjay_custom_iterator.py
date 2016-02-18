#!/usr/bin/env python
import sys
sys.path.append('/usr/share/inkscape/extensions')
import inkex
import simplestyle
import simplepath
import simpletransform
import pturtle
import bezmisc

import re
import math

class MatlabConverterEffect(inkex.Effect):
  def __init__(self):
    inkex.Effect.__init__(self)
    self.OptionParser.add_option('-w','--what', action='store',
      type='string', dest='what', default='', 
      help='Xpath string used to select objects')
    self.OptionParser.add_option('','--verb1', action='store', type='string', dest='verb1', default='', help='Enter text for python interpreter.')
    self.OptionParser.add_option('','--verb2', action='store', type='string', dest='verb2', default='', help='Enter text for python interpreter.')
    self.OptionParser.add_option('','--verb3', action='store', type='string', dest='verb3', default='', help='Enter text for python interpreter.')
    self.OptionParser.add_option('','--verb4', action='store', type='string', dest='verb4', default='', help='Enter text for python interpreter.')
    self.OptionParser.add_option('','--verb5', action='store', type='string', dest='verb5', default='', help='Enter text for python interpreter.')
    self.OptionParser.add_option('','--doverb1', action='store', type='string', dest='doverb1', default='', help='Execute python')
    self.OptionParser.add_option('','--doverb2', action='store', type='string', dest='doverb2', default='', help='Execute python')
    self.OptionParser.add_option('','--doverb3', action='store', type='string', dest='doverb3', default='', help='Execute python')
    self.OptionParser.add_option('','--doverb4', action='store', type='string', dest='doverb4', default='', help='Execute python')
    self.OptionParser.add_option('','--doverb5', action='store', type='string', dest='doverb5', default='', help='Execute python')
    self.OptionParser.add_option('','--variablex', action='store', type='string', dest='variablex', default='50', help='Specify a variable parameter for the script')
    self.OptionParser.add_option('-t','--tab', action='store',
      type='string', dest='tab', default='', 
      help='Does nothing')
    self.OptionParser.add_option('-i','--ignore_errors', action='store',
      type='string', dest='ignore_errors', default='', 
      help='Skip over errors in nodes')
    self.OptionParser.add_option('-d','--calculate_d', action='store',
      type='string', dest='calculate_d', default='', 
      help='Calculate coordinates d for each path object')
    self.OptionParser.add_option('-x','--decode_escapes', action='store',
      type='string', dest='decode_escapes', default='false', 
      help='Decodes escape characters from the python command')
    self.remap_stdout = True
  def effect(self):
    '''
    This is called when the effect is applied
    '''
    # get verb and query
    what=self.options.what
    verb=""
    def istrue(string):
      return string.lower() in ('true','t','1','yes','y')
    decode = istrue(self.options.decode_escapes)
    if decode: newl='\\n'
    else:      newl='\n'
    if istrue(self.options.doverb1):  verb+=self.options.verb1 + newl
    if istrue(self.options.doverb2):  verb+=self.options.verb2 + newl
    if istrue(self.options.doverb3):  verb+=self.options.verb3 + newl
    if istrue(self.options.doverb4):  verb+=self.options.verb4 + newl
    if istrue(self.options.doverb5):  verb+=self.options.verb5 + newl
    if decode:
      verb=verb.decode('string_escape')
    
    # prepare selection set
    self.getselected()
    self.getposinlayer()
    if not what:
      if self.selected:      # path left blank, and something selected?
        selset = self.selected.iteritems()     # use selection if it exists
      else:    # path left blank, and nothing selected
        print "No selection, and no XPath.\nUse '//*' to iterate all nodes."
        return # gracefully exit empty handed
    else:
      selset = self.document.xpath( what, namespaces=dict(inkex.NSS.items()+{ 
         'svg':'http://www.w3.org/2000/svg',
         's'  :'http://www.w3.org/2000/svg'       }.items() ) ) # otherwise go through all nodes
      selset = [(x.get('id'), x) for x in selset]; 
    if self.remap_stdout:
      realout   =sys.stdout    # re-map script output to stderr - so can be seen by user
      sys.stdout=sys.stderr

    # iterate over set
    for i,n in selset:
      # prepare environment for running script
      s=simplestyle.parseStyle(n.get('style'))
      oldstyle = simplestyle.parseStyle(n.get('style')) # keep track of old style
      d=[]
      p=[]
      if self.options.calculate_d: # calculate d: create a list of path elements
        d=n.get('d')   # examine the path itself
        if d: 
          p=simplepath.parsePath(d)
      try:
        class Struct:
          def __init__(self, **e):
            self.__dict__.update(e)
        oldattrib=dict(n.attrib)     # keep track of original attributes
        a=Struct(**n.attrib)     # a is a read-only object that contains the attributes of the node
        x=int(self.options.variablex) # get parameter "x" from slider
        localdict={'d':d, 'n':n, 's':s, 'p':p, 'self':self, 'a':a , 'x':x }
        globaldict = dict(math.__dict__.items() +   # what commands to allow in script?
                          re.__dict__.items() +
                          simplestyle.__dict__.items() +
                          simplepath.__dict__.items() +
                          simpletransform.__dict__.items() +
                          inkex.__dict__.items()
                          )
        ######### Actually run the script
        exec verb in globaldict, localdict
        ######### 

        
        for (k,v) in a.__dict__.items():
          if ( (k in oldattrib and oldattrib[k]!=v)  # if value has been changed in a
               or (k not in oldattrib) ):            # or key added to a
            n.set(k,v)                               # then update the object
        stylechanged=False
        for (k,v) in s.items():
          if ( (k in oldstyle and oldstyle[k]!=v)
               or (k not in oldstyle) ):
            stylechanged=True
        if stylechanged:
          n.set('style',simplestyle.formatStyle(localdict['s']))
        n.set('d',simplepath.formatPath(p))
      except Exception, e: # an error occured on this node
        if self.remap_stdout: # restore stdout before returning, to 
          sys.stdout=realout  # allow the svg to be piped to inkscape
        if not self.options.ignore_errors.lower() in ('true','t','1','yes','y'):
          raise # unless ignoring errors, this ends iteration
      else: 
        if self.remap_stdout: # restore stdout before returning, to 
          sys.stdout=realout  # allow the svg to be piped to inkscape
########## END CLASS

m=MatlabConverterEffect()
m.affect()
