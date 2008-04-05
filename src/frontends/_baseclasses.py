import communication as c

class BaseIndividual(object):
    """Parent-class for classes that represent individuals in dialogues."""
    def __del__(self):
        if __debug__:
            c.stderr(u"DEBUG: Individual %r garbage collected\n" % (self,))

class BaseGroup(object):
    """Parent-class for classes representing a group having a conversation."""
    def __del__(self):
        if __debug__:
            c.stderr(u"DEBUG: Group %r garbage collected\n" % (self,))

class BaseGroupMember(object):
    """Parent-class for classes representing a member of a Group chat."""
    def __del__(self):
        if __debug__:
            c.stderr(u"DEBUG: GroupMember %r garbage collected\n" % (self,))

class BaseConnection(object):
    """Connection with the medium in question."""
    def __del__(self):
        if __debug__:
            c.stderr(u"DEBUG: Connection %r garbage collected\n" % (self,))
