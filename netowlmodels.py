"""Models for Netowl link application."""


class RDFitem:
    """Model to hold non-geo or ready to geocode items."""

    def __init__(self, rdfid, rdfvalue, timest, orgdoc, ontology, rdflinks=None):  # noqa: E501
        """Docstring."""
        self.id = rdfid
        self.links = [] if rdflinks is None else rdflinks  # list - optional
        self.value = rdfvalue
        self.timest = timest
        self.orgdoc = orgdoc
        self.type = ontology


class RDFitemGeo(RDFitem):
    """Model to hold objs with lat/long already assigned."""

    def __init__(self, rdfid, rdfvalue, longt, latt, timest,
                 orgdoc, rdflinks=None):
        """Docstring."""
        self.id = rdfid
        self.links = [] if rdflinks is None else rdflinks  # list - optional
        self.value = rdfvalue
        self.lat = latt
        self.long = longt
        self.timest = timest
        self.orgdoc = orgdoc

    def set_type(self, typeofgeo):
        """Docstring."""
        self.type = typeofgeo

    def set_subtype(self, subtypegeo):
        """Docstring."""
        self.subtype = subtypegeo

    def set_link_details(self, details):
        """Docstring."""
        self.linkdetails = details


class RDFlinkItem():
    """Model to hold link objs."""

    def __init__(self, linkid, fromid, toid, fromvalue, tovalue,
                 fromrole, torole, fromroletype, toroletype, timest):
        """Docstring."""
        self.linkid = linkid
        self.fromid = fromid
        self.toid = toid
        self.fromvalue = fromvalue
        self.tovalue = tovalue
        self.fromrole = fromrole
        self.torole = torole
        self.fromroletype = fromroletype
        self.toroletype = toroletype
        self.timest = timest


class RDFeventItem():
    """Model to hold event objs."""

    def __init__(self, eventvalue, eventid, fromid, toid, fromvalue, tovalue,
                 fromrole, torole, orgdoc, uniquets):
        """Docstring."""
        self.eventvalue = eventvalue
        self.eventid = eventid
        self.fromid = fromid
        self.toid = toid
        self.fromvalue = fromvalue
        self.tovalue = tovalue
        self.fromrole = fromrole
        self.torole = torole
        self.orgdoc = orgdoc
        self.timest = uniquets
