# -----------------------------------------------------------------------------
"""

Convert an *.svd file to a python objects representing the device.

"""
# -----------------------------------------------------------------------------

import lxml.etree as ET

# -----------------------------------------------------------------------------
# utility functions

def description_cleanup(s):
  """cleanup a description string"""
  if s is None:
    return None
  # remove un-needed white space
  s = ' '.join([x.strip() for x in s.split()])
  # strip trailing period
  s = s.strip('.')
  return s

def sizeof_address_blocks(blocks, usage):
  """return the consolidated size (offset == 0) for a list of address blocks"""
  end = 0
  for b in blocks:
    if b.usage != usage:
      continue
    e = b.offset + b.size
    if e > end:
      end = e
  # return the size
  return end

# -----------------------------------------------------------------------------

def lookup_derived_from(e, df_set):
  """return the end of the derivedFrom chain"""
  if e.derivedFrom is None:
    # this is the end of the chain
    return e
  for df in df_set:
    if e.derivedFrom == df.name:
      # recurse for multi-level deriveFrom
      return lookup_derived_from(df, df_set)

def set_derived_from(x, thing):
  """setup derived_from links between svd objects"""
  for e in x:
    if e.derivedFrom:
      e.derived_from = lookup_derived_from(e, x)
      #print('%s %s is derived from %s' % (thing, e.name, e.derived_from.name))

class svd_object(object):

  def __init__(self):
    pass

  def attribute(self, x):
    name, value = x
    if value is not None:
      object.__setattr__(self, name, value)

  def __getattr__(self, name):
    return None

  def attribute_string(self, s, name):
    if self.__dict__.has_key(name):
      s.append("  '%s': '%s'," % (name, self.__dict__[name]))
    else:
      s.append("  # '%s': 'string'," % (name))

  def attribute_boolean(self, s, name):
    if self.__dict__.has_key(name):
      s.append("  '%s': %s," % (name, str(self.__dict__[name])))
    else:
      s.append("  # '%s': boolean," % (name))

  def attribute_integer(self, s, name):
    if self.__dict__.has_key(name):
      s.append("  '%s': %d," % (name, self.__dict__[name]))
    else:
      s.append("  # '%s': integer," % (name))

  def attribute_header(self, s, name):
    if self.__dict__.has_key(name):
      s.append('%s: %s' % (name, str(self.__dict__[name])))

# -----------------------------------------------------------------------------

# identifierType = string
# stringType = string
# xs:Name = string
# cpuNameType = string
# revisionType = string
# endianType = string
# xs:boolean = boolean
# scaledNonNegativeInteger = integer

def get_string(node, tag, default = None):
  """Get the text string for the tag from the node"""
  try:
    return node.find(tag).text
  except AttributeError:
    return default

def get_integer(node, tag, default = None):
  text_value = get_string(node, tag, default)
  try:
    if text_value != default:
      text_value = text_value.strip().lower()
      if text_value.startswith('0x'):
        return int(text_value[2:], 16)  # hexadecimal
      elif text_value.startswith('#'):
        # TODO(posborne): Deal with strange #1xx case better
        #
        # Freescale will sometimes provide values that look like this:
        #   #1xx
        # In this case, there are a number of values which all mean the
        # same thing as the field is a "don't care".  For now, we just
        # replace those bits with zeros.
        text_value = text_value.replace('x', '0')[1:]
        is_bin = all(x in '01' for x in text_value)
        return int(text_value, 2) if is_bin else int(text_value)  # binary
      elif text_value.startswith('true'):
        return 1
      elif text_value.startswith('false'):
        return 0
      else:
        return int(text_value)  # decimal
  except ValueError:
    return default
  return default

def get_boolean(node, tag, default = None):
  n = get_integer(node, tag, default)
  if n is None:
    return default
  return n != 0

# -----------------------------------------------------------------------------

def string_node(node, tag, default = None):
  return (tag, get_string(node, tag, default))

def boolean_node(node, tag, default = None):
  return (tag, get_boolean(node, tag, default))

def integer_node(node, tag, default = None):
  return (tag, get_integer(node, tag, default))

# -----------------------------------------------------------------------------

class parser(object):

  def __init__(self, path):
    self.tree = ET.parse(path)
    self.root = self.tree.getroot()

  def get_field(self, node):
    f = svd_object()
    f.attribute(string_node(node, 'name'))
    f.attribute(string_node(node, 'description'))
    f.description = description_cleanup(f.description)
    f.attribute(string_node(node, 'access'))
    f.attribute(integer_node(node, 'bitOffset'))
    f.attribute(integer_node(node, 'bitWidth'))
    f.attribute(integer_node(node, 'lsb'))
    f.attribute(integer_node(node, 'msb'))
    f.attribute(string_node(node, 'bitRange'))
    f.derivedFrom = node.get('derivedFrom')
    return f

  def get_register(self, node):
    r = svd_object()
    r.attribute(integer_node(node, 'dim'))
    r.attribute(integer_node(node, 'dimIncrement'))
    r.attribute(string_node(node, 'dimIndex'))
    r.attribute(string_node(node, 'name'))
    r.attribute(string_node(node, 'displayName'))
    r.attribute(string_node(node, 'description'))
    r.description = description_cleanup(r.description)
    r.attribute(string_node(node, 'alternateGroup'))
    r.attribute(string_node(node, 'alternateRegister'))
    r.attribute(integer_node(node, 'addressOffset'))
    r.attribute(integer_node(node, 'size'))
    r.attribute(string_node(node, 'access'))
    r.attribute(string_node(node, 'protection'))
    r.attribute(integer_node(node, 'resetValue'))
    r.attribute(integer_node(node, 'resetMask'))
    r.attribute(string_node(node, 'dataType'))
    r.attribute(integer_node(node, 'resetMask'))
    r.attribute(string_node(node, 'modifiedWriteValues'))
    #<xs:element name="writeConstraint" type="writeConstraintType" minOccurs="0"/>
    r.attribute(string_node(node, 'readAction'))
    r.fields = [self.get_field(x) for x in node.findall('.//field')]
    r.derivedFrom = node.get('derivedFrom')
    # if a field is "derivedFrom" another field, add a derived_from reference
    set_derived_from(r.fields, 'field')
    return r

  def get_address_block(self, node):
    b = svd_object()
    b.attribute(integer_node(node, 'offset'))
    b.attribute(integer_node(node, 'size'))
    b.attribute(string_node(node, 'usage'))
    return b

  def get_interrupt(self, node):
    i = svd_object()
    i.attribute(string_node(node, 'name'))
    i.attribute(string_node(node, 'description'))
    i.description = description_cleanup(i.description)
    i.attribute(integer_node(node, 'value'))
    return i

  def get_peripheral(self, node):
    p = svd_object()
    p.attribute(string_node(node, 'name'))
    p.attribute(string_node(node, 'version'))
    p.attribute(string_node(node, 'description'))
    p.description = description_cleanup(p.description)
    p.attribute(string_node(node, 'alternatePeripheral'))
    p.attribute(string_node(node, 'groupName'))
    p.attribute(string_node(node, 'prependToName'))
    p.attribute(string_node(node, 'appendToName'))
    p.attribute(string_node(node, 'headerStructName'))
    p.attribute(string_node(node, 'disableCondition'))
    p.attribute(integer_node(node, 'baseAddress'))
    p.attribute(integer_node(node, 'size')) # default register size
    p.addressBlock = [self.get_address_block(x) for x in node.findall('./addressBlock')]
    p.interrupts = [self.get_interrupt(x) for x in node.findall('./interrupt')]
    p.registers = [self.get_register(x) for x in node.findall('.//register')]
    p.derivedFrom = node.get('derivedFrom')
    # if a register is "derivedFrom" another register, add a derived_from reference
    set_derived_from(p.registers, 'register')
    # convert a 'None' description into a python None
    if p.description == 'None':
      p.description = None
    return p

  def get_cpu(self, node):
    c = svd_object()
    c.attribute(string_node(node, 'name'))
    c.attribute(string_node(node, 'revision'))
    c.attribute(string_node(node, 'endian'))
    c.attribute(boolean_node(node, 'mpuPresent'))
    c.attribute(boolean_node(node, 'fpuPresent'))
    c.attribute(boolean_node(node, 'fpuDP'))
    c.attribute(boolean_node(node, 'icachePresent'))
    c.attribute(boolean_node(node, 'dcachePresent'))
    c.attribute(boolean_node(node, 'itcmPresent'))
    c.attribute(boolean_node(node, 'dtcmPresent'))
    c.attribute(boolean_node(node, 'vtorPresent'))
    c.attribute(integer_node(node, 'nvicPrioBits'))
    c.attribute(boolean_node(node, 'vendorSystickConfig'))
    c.attribute(integer_node(node, 'deviceNumInterrupts'))
    c.attribute(integer_node(node, 'sauNumRegions'))
    #<xs:element name="sauRegionsConfig" minOccurs="0">
    return c

  def get_device(self, node):
    """return the device described by the svd file"""
    d = svd_object()
    d.attribute(string_node(node, 'vendor'))
    d.attribute(string_node(node, 'vendorID'))
    d.attribute(string_node(node, 'name'))
    d.attribute(string_node(node, 'series'))
    d.attribute(string_node(node, 'version'))
    d.attribute(string_node(node, 'description'))
    d.attribute(string_node(node, 'licenseText'))
    d.cpu = self.get_cpu(node.find('./cpu'))
    d.attribute(string_node(node, 'headerSystemFilename'))
    d.attribute(string_node(node, 'headerDefinitionsPrefix'))
    d.attribute(integer_node(node, 'addressUnitBits'))
    d.attribute(integer_node(node, 'width'))
    d.peripherals = [self.get_peripheral(x) for x in self.root.findall('.//peripheral')]
    # if a peripheral is "derivedFrom" another peripheral, add a derived_from reference
    set_derived_from(d.peripherals, 'peripheral')
    return d

  def parse(self):
    return self.get_device(self.root)

# -----------------------------------------------------------------------------
