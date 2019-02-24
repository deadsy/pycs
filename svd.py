# -----------------------------------------------------------------------------
"""

Convert an *.svd file to a python objects representing the device.

"""
# -----------------------------------------------------------------------------

import lxml.etree as ET

# -----------------------------------------------------------------------------

def set_derived_from(x, thing):
  """setup derived_from links between svd objects"""
  if x is None:
    return
  for e in x:
    if e.derivedFrom:
      for df in x:
        if e.derivedFrom == df.name:
          e.derived_from = df
          #print('%s %s is derived from %s' % (thing, e.name, e.derived_from.name))
    else:
      e.derived_from = None

class svd_object(object):

  def __init__(self):
    pass

  def attribute(self, x):
    name, value = x
    if value is not None:
      self.__setattr__(name, value)

  def list_attribute(self, l, name):
    if l:
      self.__setattr__(name, l)

  def __getattr__(self, name):
    if name == 'derived_from':
      # no defined derived_from attribute
      return None
    if self.derived_from is None:
      # the derived_from goes nowhere
      return None
    # try to find the attribute in the next "derived from" link
    return getattr(self.derived_from, name)

  def attribute_string(self, s, name):
    if name in self.__dict__:
      s.append("  '%s': '%s'," % (name, self.__dict__[name]))
    else:
      s.append("  # '%s': 'string'," % (name))

  def attribute_boolean(self, s, name):
    if name in self.__dict__:
      s.append("  '%s': %s," % (name, str(self.__dict__[name])))
    else:
      s.append("  # '%s': boolean," % (name))

  def attribute_integer(self, s, name):
    if name in self.__dict__:
      s.append("  '%s': %d," % (name, self.__dict__[name]))
    else:
      s.append("  # '%s': integer," % (name))

  def attribute_header(self, s, name):
    if name in self.__dict__:
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

def get_string(node, tag, default=None):
  """Get the text string for the tag from the node"""
  try:
    return node.find(tag).text
  except AttributeError:
    return default

def get_integer(node, tag, default=None):
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

def get_boolean(node, tag, default=None):
  n = get_integer(node, tag, default)
  if n is None:
    return default
  return n != 0

# -----------------------------------------------------------------------------

def string_node(node, tag, default=None):
  return (tag, get_string(node, tag, default))

def boolean_node(node, tag, default=None):
  return (tag, get_boolean(node, tag, default))

def integer_node(node, tag, default=None):
  return (tag, get_integer(node, tag, default))

# -----------------------------------------------------------------------------

class parser(object):

  def __init__(self, path):
    self.tree = ET.parse(path)
    self.root = self.tree.getroot()

  def get_enumvalue(self, node):
    e = svd_object()
    e.attribute(string_node(node, 'name'))
    e.attribute(string_node(node, 'description'))
    e.attribute(integer_node(node, 'value'))
    e.attribute(boolean_node(node, 'isDefault'))
    return e

  def get_enumvalues(self, node):
    e = svd_object()
    e.attribute(string_node(node, 'name'))
    e.attribute(string_node(node, 'usage'))
    e.list_attribute([self.get_enumvalue(x) for x in node.findall('.//enumeratedValue')], 'enumeratedValue')
    e.derivedFrom = node.get('derivedFrom')
    return e

  def get_field(self, node):
    f = svd_object()
    f.attribute(string_node(node, 'name'))
    f.attribute(string_node(node, 'description'))
    f.attribute(string_node(node, 'access'))
    f.attribute(integer_node(node, 'bitOffset'))
    f.attribute(integer_node(node, 'bitWidth'))
    f.attribute(integer_node(node, 'lsb'))
    f.attribute(integer_node(node, 'msb'))
    f.attribute(string_node(node, 'bitRange'))
    f.list_attribute([self.get_enumvalues(x) for x in node.findall('.//enumeratedValues')], 'enumeratedValues')
    f.derivedFrom = node.get('derivedFrom')
    # if an enumerated value set is "derivedFrom" another enumerated value set, add a derived_from reference
    set_derived_from(f.enumeratedValues, 'enumeratedValues')
    return f

  def get_register(self, node):
    r = svd_object()
    r.attribute(integer_node(node, 'dim'))
    r.attribute(integer_node(node, 'dimIncrement'))
    r.attribute(string_node(node, 'dimIndex'))
    r.attribute(string_node(node, 'name'))
    r.attribute(string_node(node, 'displayName'))
    r.attribute(string_node(node, 'description'))
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
    r.list_attribute([self.get_field(x) for x in node.findall('.//field')], 'fields')
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
    i.attribute(integer_node(node, 'value'))
    return i

  def get_peripheral(self, node):
    p = svd_object()
    p.attribute(string_node(node, 'name'))
    p.attribute(string_node(node, 'version'))
    p.attribute(string_node(node, 'description'))
    p.attribute(string_node(node, 'alternatePeripheral'))
    p.attribute(string_node(node, 'groupName'))
    p.attribute(string_node(node, 'prependToName'))
    p.attribute(string_node(node, 'appendToName'))
    p.attribute(string_node(node, 'headerStructName'))
    p.attribute(string_node(node, 'disableCondition'))
    p.attribute(integer_node(node, 'baseAddress'))
    p.attribute(integer_node(node, 'size')) # default register size
    p.list_attribute([self.get_address_block(x) for x in node.findall('./addressBlock')], 'addressBlock')
    p.list_attribute([self.get_interrupt(x) for x in node.findall('./interrupt')], 'interrupts')
    p.list_attribute([self.get_register(x) for x in node.findall('.//register')], 'registers')
    p.derivedFrom = node.get('derivedFrom')
    # if a register is "derivedFrom" another register, add a derived_from reference
    set_derived_from(p.registers, 'register')
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
    d.list_attribute([self.get_peripheral(x) for x in self.root.findall('.//peripheral')], 'peripherals')
    # if a peripheral is "derivedFrom" another peripheral, add a derived_from reference
    set_derived_from(d.peripherals, 'peripheral')
    return d

  def parse(self):
    return self.get_device(self.root)

# -----------------------------------------------------------------------------
