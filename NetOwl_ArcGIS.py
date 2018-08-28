"""MVO to create NetOwl integration GP tool."""
import json
import time
import arcpy
import string
import requests
import os


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


# necessary functions


def cleanup_text(intext):
    """Function to remove funky chars."""
    printable = set(string.printable)
    p = ''.join(filter(lambda x: x in printable, intext))
    g = p.replace('"', "")
    return g


def geocode_address(address):
    """Use World Geocoder to get XY for one address at a time."""
    querystring = {
        "f": "json",
        "singleLine": address}
    url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"  # noqa: E501
    response = requests.request("GET", url, params=querystring)
    p = response.text
    j = json.loads(p)
    location = j['candidates'][0]['location']  # returns first location as X, Y
    return location


def netowl_curl(infile, outpath, outextension):
    """Do James Jones code to query NetOwl API."""
    headers = {
        'accept': 'application/json',  # 'application/rdf+xml',
        'Authorization': 'netowl ff5e6185-5d63-459b-9765-4ebb905affc8',
    }

    if infile.endswith(".txt"):
        headers['Content-Type'] = 'text/plain'
    elif infile.endswith(".pdf"):
        headers['Content-Type'] = 'application/pdf'
    elif infile.endswith(".docx"):
        headers['Content-Type'] = 'application/msword'

    params = (
        ('language', 'english'),
    )

    data = open(infile, 'rb').read()
    response = requests.post('https://api.netowl.com/api/v2/_process',
                             headers=headers, params=params, data=data,
                             verify=False)
    r = response.text
    outpath = outpath
    filename = os.path.split(d)[1]
    if os.path.exists(outpath) is False:
        os.mkdir(outpath, mode=0o777, )
    outfile = os.path.join(outpath, filename + outextension)
    open(outfile, "w", encoding="utf-8").write(r)


def make_link_list(linklist):
    """Turn linklist into string."""
    l = ""
    for u in linklist:
        l = l + " " + u
    return l[1:len(l)]


# vars and setup - change to params
#docsPath = r'C:/temp/input'
# docsPath = r'C:/temp/testinput'
#rdfOutDir = r'C:/temp/output/'
# fileOutDir = r'C:/temp/output'
# rdfOutDir = r'C:/temp/test/' # for testing mahmud 10
rdfOutExt = ".json"
docsPath = arcpy.GetParameterAsText(0)
rdfOutDir = arcpy.GetParameterAsText(1)

# ---------------------------------------------closed for testing
# get the docs
docs = []
for root, dirs, files in os.walk(docsPath):
    for f in files:
        filePath = os.path.join(root, f)
        docs.append(filePath)

# build the JSON we work with
for d in docs:
    netowl_curl(d, rdfOutDir, rdfOutExt)
# ---------------------------------------------closed for testing

# 1. Build all the objects from all the files
# 2. Write all of the objects' data to fc or link table

# for each document in the output directory, create rdfobjs lists

# create empty lists for objects
rdfobjs = []
rdfobjsGeo = []
linkobjs = []

for j in os.listdir(rdfOutDir):
    fn = j[:-5]  # original filename to use as attribute
    # uniquets = str(time.time())  # unique time stamp for each doc
    with open(os.path.join(rdfOutDir, j), 'r', encoding="utf-8") as f:
        rdfstring = json.load(f)
        uniquets = str(time.time())  # unique time stamp for each doc
        doc = rdfstring['document'][0]  # gets main part
        ents = (doc['entity'])  # gets all entities
        for e in ents:

            # gather data from each entity
            rdfvalue = cleanup_text(e['value'])  # value (ie name)
            # rdfvalue = e['value']
            rdfid = e['id']  # rdfid (unique to each entity - with timestamp)  # noqa: E501

            # test for geo (decide which type of obj to make)
            if 'geodetic' in e:
                if 'entity-ref' in e:
                    # print("already plotted elsewhere...")
                    isGeo = False  # already plotted, relegate to rdfobj list  # noqa: E501
                    skiplinks = True
                else:
                    lat = float(e['geodetic']['latitude'])
                    longg = float(e['geodetic']['longitude'])
                    isGeo = True
                    skiplinks = False
            else:
                isGeo = False
                skiplinks = True

            # relationships
            # HACK - put into attribute table inside of fc rather than as link
            if 'link-ref' in e:
                refrels = []
                linkdescs = []  # add funct to describe link in attribute field
                if skiplinks is not True:  # is false, plotting the point in Feature Class
                    for k in e['link-ref']:  # every link-ref per entity
                        refrels.append(k['idref'])  # keep these - all references  # noqa: E501
                        if 'role-type' in k:  # test the role type is source
                            if k['role-type'] == "source":
                                linkdesc = rdfvalue + " is a " + k['role'] + " in " + k['entity-arg'][0]['value']  # noqa: E501
                                linkdescs.append(linkdesc)
                            else:
                                linkdescs.append("This item has parent links but no children")  # noqa: E501
                haslinks = True

            else:
                haslinks = False

            # check for addresses
            if e['ontology'] == "entity:address:mail":
                address = e['value']
                location = geocode_address(address)  # returns x,y
                isGeo = True
                # set lat long
                lat = location['y']
                longg = location['x']

            # build the objects
            if isGeo:

                if haslinks:
                    # add refrels to new obj
                    rdfobj = RDFitemGeo(rdfid, rdfvalue, longg, lat, uniquets, fn,  # noqa: E501
                                        refrels)
                    ld = str(linkdescs)
                    if len(ld) > 255:
                        ld = ld[:254]  # shorten long ones

                    rdfobj.set_link_details(ld)
                else:
                    rdfobj = RDFitemGeo(rdfid, rdfvalue, longg, lat, uniquets, fn)  # noqa: E501
                    rdfobj.set_link_details("No links for this point")

                # set type for symbology
                rdfobj.set_type("placename")  # default
                rdfobj.set_subtype("unknown")  # default
                if e['ontology'] == "entity:place:city":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("city")
                if e['ontology'] == "entity:place:country":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("country")
                if e['ontology'] == "entity:place:province":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("province")
                if e['ontology'] == "entity:place:continent":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("continent")
                if e['ontology'] == "entity:numeric:coordinate:mgrs":
                    rdfobj.set_type("coordinate")
                    rdfobj.set_subtype("MGRS")
                if e['ontology'] == "entity:numeric:coordinate:latlong":  # noqa: E501
                    rdfobj.set_type("coordinate")
                    rdfobj.set_subtype("latlong")
                if e['ontology'] == "entity:address:mail":
                    rdfobj.set_type("address")
                    rdfobj.set_subtype("mail")
                if e['ontology'] == "entity:place:other":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("descriptor")
                if e['ontology'] == "entity:place:landform":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("landform")
                if e['ontology'] == "entity:organization:facility":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("facility")
                if e['ontology'] == "entity:place:water":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("water")
                if e['ontology'] == "entity:place:county":
                    rdfobj.set_type("placename")
                    rdfobj.set_subtype("county")

                rdfobjsGeo.append(rdfobj)

            else:  # not geo
                ontology = e['ontology']
                if haslinks:
                    rdfobj = RDFitem(rdfid, rdfvalue, uniquets, fn, ontology, refrels)  # noqa: E501
                else:  # has neither links nor address
                    rdfobj = RDFitem(rdfid, rdfvalue, uniquets, fn, ontology)

                rdfobjs.append(rdfobj)

        # # get the link entities from doc
        # # and build objects
        if 'link' in doc:
            linksys = (doc['link'])
            for l in linksys:
                linkid = l['id']  # HOOCH
                if 'entity-arg' in l:
                    fromid = l['entity-arg'][0]['idref']
                    toid = l['entity-arg'][1]['idref']
                    fromvalue = l['entity-arg'][0]['value']
                    tovalue = l['entity-arg'][1]['value']
                    fromrole = l['entity-arg'][0]['role']
                    torole = l['entity-arg'][1]['role']
                    fromroletype = l['entity-arg'][0]['role-type']
                    toroletype = l['entity-arg'][1]['role-type']
                # build link objects -  ,uniquets
                linkobj = RDFlinkItem(linkid, fromid, toid, fromvalue, tovalue,
                                      fromrole, torole, fromroletype,
                                      toroletype, uniquets)
                linkobjs.append(linkobj)

        # for lo in linkobjs:
        #     print(lo.tovalue + " " + lo.fromvalue)

            # if 'entity-arg' in l:
            #     linkrels = []
            #     for h in l['entity-arg']:
            #         linkrels.append(h['idref'])


# ------------------------------------------------------------
# second part - write to fc and links table
# ------------------------------------------------------------

# now add all the rdfobjGeo to the map as featureclass
wk = arcpy.GetParameterAsText(2)
sr = arcpy.SpatialReference(4326)  # TODO: this may not be the correct sr
template_ws = r'C:\Users\jame9353\Documents\ArcGIS\Projects\Defense and Intel Forum\NetOwl_GeoProcessing-master\NetOwl_GeoProcessing-master\Template.gdb'

# # check to see if fc already exists
if arcpy.Exists(os.path.join(wk,"netowl_fc")) is False:
    arcpy.CreateFeatureclass_management(wk, "netowl_fc", "POINT", os.path.join(template_ws,"netowl_template_fc"), 'No', 'No', sr)  # noqa: E501

entslist = ["RDFID", "RDFVALUE", "TIMEST", "RDFLINKS", "TYPE", "SUBTYPE", "ORGDOC", "UNIQUEID", "LINKDETAILS", "SHAPE@XY"]   # noqa: E501
iCur = arcpy.da.InsertCursor("netowl_fc", entslist)

for r in rdfobjsGeo:
    fieldobjs = []
    fieldobjs.append(r.id)
    fieldobjs.append(r.value)
    fieldobjs.append(r.timest)
    # need less than 23 links or fc won't accept list (255 char max)
    if len(r.links) > 23:
        linkslist = r.links[0:22]
    else:
        linkslist = r.links
    ll = make_link_list(linkslist)
    fieldobjs.append(ll)
    fieldobjs.append(r.type)
    fieldobjs.append(r.subtype)
    fieldobjs.append(r.orgdoc)
    fieldobjs.append(r.id + str(r.timest))
    fieldobjs.append(r.linkdetails)
    fieldobjs.append((r.long, r.lat))
    iCur.insertRow(fieldobjs)

del iCur

# for nongeo table
if arcpy.Exists(os.path.join(wk,"netowl_nogeo")) is False:
    arcpy.CreateTable_management(wk, "netowl_nogeo", os.path.join(template_ws,"netowl_template_nogeo"))

iCur_links = arcpy.da.InsertCursor("netowl_nogeo", ["RDFID", "RDFVALUE", "TIMEST", "RDFLINKS", "ORGDOC", "UNIQUEID", "TYPE"])  # noqa: E501

for d in rdfobjs:
    fieldobjs = []
    fieldobjs.append(d.id)
    fieldobjs.append(d.value)
    fieldobjs.append(d.timest)
    ll = make_link_list(d.links)
    fieldobjs.append(ll)
    fieldobjs.append(d.orgdoc)
    fieldobjs.append(d.id + str(d.timest))
    fieldobjs.append(d.type)
    iCur_links.insertRow(fieldobjs)

# now get all the links -- HOOCH
ents = (doc['entity'])

del iCur_links

# ---------- relationship links table ----------
if arcpy.Exists(os.path.join(wk,"netowl_links")) is False:
    arcpy.CreateTable_management(wk, "netowl_links", os.path.join(template_ws,"netowl_template_links"))

iCur_links = arcpy.da.InsertCursor("netowl_links", ["LINKID", "FROMID", "TOID", "FROMVALUE", "TOVALUE", "FROMROLE", "TOROLE", "FROMROLETYPE", "TOROLETYPE", "UNIQUETS"])  # noqa: E501

for lo in linkobjs:
    fieldobjs = []
    fieldobjs.append(lo.linkid + str(lo.timest))
    fieldobjs.append(lo.fromid + str(lo.timest))
    fieldobjs.append(lo.toid + str(lo.timest))
    fieldobjs.append(lo.fromvalue)
    fieldobjs.append(lo.tovalue)
    fieldobjs.append(lo.fromrole)
    fieldobjs.append(lo.torole)
    fieldobjs.append(lo.fromroletype)
    fieldobjs.append(lo.toroletype)
    fieldobjs.append(lo.timest)

    iCur_links.insertRow(fieldobjs)

# now get all the links -- HOOCH
ents = (doc['entity'])

del iCur_links


print("Script completed")
