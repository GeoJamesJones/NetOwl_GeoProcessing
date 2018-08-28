"""MVO to create NetOwl integration GP tool."""

import time
import arcpy
import json
import os
from netowlmodels import RDFitem, RDFitemGeo, RDFlinkItem, RDFeventItem
import netowlfuncts as nof


# vars and setup - change to params
docsPath = r'C:/temp/input'
rdfOutDir = r'C:/temp/output/'
rdfOutExt = ".json"

# ---------------------------------------------closed for testing
# # get the docs
# docs = []
# for root, dirs, files in os.walk(docsPath):
#     for f in files:
#         filePath = os.path.join(root, f)
#         docs.append(filePath)

# # build the JSON we work with
# for d in docs:
#     nof.netowl_curl(d, rdfOutDir, rdfOutExt)
# ---------------------------------------------closed for testing


# create empty lists for objects
rdfobjs = []
rdfobjsGeo = []
linkobjs = []
eventobjs = []

for j in os.listdir(rdfOutDir):  # go through each file in output dir
    fn = j[:-5]  # original filename to use as attribute
    # uniquets = str(time.time())  # unique time stamp for each doc
    with open(rdfOutDir + j, 'r', encoding="utf-8") as f:
        rdfstring = json.load(f)
        uniquets = str(time.time())  # unique time stamp for each doc
        doc = rdfstring['document'][0]  # gets main part
        ents = (doc['entity'])  # gets all entities in doc

# ----------------------------------
#       Build entities objects
# ----------------------------------
        for e in ents:

            # gather data from each entity
            rdfvalue = nof.cleanup_text(e['value'])  # value (ie name)
            rdfid = e['id']  # rdfid (unique to each entity - with timestamp)  # noqa: E501

            # test for geo (decide which type of obj to make - geo or non-geo)
            if 'geodetic' in e:

                if 'link-ref' in e:
                    refrels = []
                    linkdescs = []
                    haslinks = True
                    for k in e['link-ref']:  # every link-ref per entity
                        refrels.append(k['idref'])  # keep these - all references  # noqa: E501
                        if 'role-type' in k:  # test the role type is source  # noqa: E501
                            if k['role-type'] == "source":
                                linkdesc = rdfvalue + " is a " + k['role'] + " in " + k['entity-arg'][0]['value']  # noqa: E501
                                linkdescs.append(linkdesc)
                            else:
                                linkdescs.append("This item has parent links but no children")  # noqa: E501
                else:
                    haslinks = False

                if 'entity-ref' in e:
                    isGeo = False  # already plotted, relegate to rdfobj list  # noqa: E501
                else:
                    lat = float(e['geodetic']['latitude'])
                    longg = float(e['geodetic']['longitude'])
                    isGeo = True

            else:
                isGeo = False

            # check for addresses
            if e['ontology'] == "entity:address:mail":
                address = e['value']
                location = nof.geocode_address(address)  # returns x,y
                isGeo = True
                # set lat long
                lat = location['y']
                longg = location['x']
                # check for links
                if 'link-ref' in e:
                    refrels = []
                    linkdescs = []
                    haslinks = True
                    for k in e['link-ref']:  # every link-ref per entity
                        refrels.append(k['idref'])  # keep these - all references  # noqa: E501
                        if 'role-type' in k:  # test the role type is source  # noqa: E501
                            if k['role-type'] == "source":
                                linkdesc = rdfvalue + " is a " + k['role'] + " in " + k['entity-arg'][0]['value']  # noqa: E501
                                linkdescs.append(linkdesc)
                            else:
                                linkdescs.append("This item has parent links but no children")  # noqa: E501
                else:
                    haslinks = False

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

# ----------------------------------
#        Build links objects
# ----------------------------------

        if 'link' in doc:
            linksys = (doc['link'])
            for l in linksys:
                linkid = l['id']
                if 'entity-arg' in l:
                    fromid = l['entity-arg'][0]['idref']
                    toid = l['entity-arg'][1]['idref']
                    fromvalue = l['entity-arg'][0]['value']
                    tovalue = l['entity-arg'][1]['value']
                    fromrole = l['entity-arg'][0]['role']
                    torole = l['entity-arg'][1]['role']
                    fromroletype = l['entity-arg'][0]['role-type']
                    toroletype = l['entity-arg'][1]['role-type']
                # build link objects
                linkobj = RDFlinkItem(linkid, fromid, toid, fromvalue, tovalue,
                                      fromrole, torole, fromroletype,
                                      toroletype, uniquets)
                linkobjs.append(linkobj)

# ----------------------------------
#        Build events objects
# ----------------------------------

        if 'event' in doc:
            events = doc['event']
            for e in events:
                evid = e['id']
                evvalue = e['value']
                if 'entity-arg' in e:
                    fromid = e['entity-arg'][0]['idref']
                    fromvalue = e['entity-arg'][0]['value']
                    fromrole = e['entity-arg'][0]['role']
                    if len(e['entity-arg']) > 1:
                        toid = e['entity-arg'][1]['idref']
                        tovalue = e['entity-arg'][1]['value']
                        torole = e['entity-arg'][1]['role']
                    else:
                        toid = None
                        tovalue = None
                        torole = None
                # build link objects
                eventobj = RDFeventItem(evvalue, evid, fromid, toid,
                                        fromvalue, tovalue, fromrole,
                                        torole, fn, uniquets)
                eventobjs.append(eventobj)

# ------------------------------------------------------------
# second part - write to items in ArcGIS Pro
# ------------------------------------------------------------

# now add all the rdfobjGeo to the map as featureclass
wk = arcpy.env.workspace = r"C:\Users\heat3463\Documents\ArcGIS\Projects\Jeff\test.gdb"  # noqa: E501
sr = arcpy.SpatialReference(4326)  # TODO: this may not be the correct sr

# ----------------------------------
#         Build featureclass
# ----------------------------------

fcname = "netowl_output"
# # check to see if fc already exists
if arcpy.Exists(fcname) is False:
    arcpy.CreateFeatureclass_management(wk, fcname, "POINT", "netowl_template_fc", 'No', 'No', sr)  # noqa: E501

entslist = ["RDFID", "RDFVALUE", "TIMEST", "RDFLINKS", "TYPE", "SUBTYPE", "ORGDOC", "UNIQUEID", "LINKDETAILS", "SHAPE@XY"]   # noqa: E501
iCur = arcpy.da.InsertCursor(fcname, entslist)

for r in rdfobjsGeo:

    fieldobjs = []
    fieldobjs.append(r.id)
    fieldobjs.append(r.value)
    fieldobjs.append(r.timest)
    ll = nof.make_link_list(r.links)
    fieldobjs.append(ll)
    fieldobjs.append(r.type)
    fieldobjs.append(r.subtype)
    fieldobjs.append(r.orgdoc)
    fieldobjs.append(r.id + str(r.timest))
    fieldobjs.append(r.linkdetails)
    fieldobjs.append((r.long, r.lat))

    iCur.insertRow(fieldobjs)

del iCur

# ----------------------------------
#   Build non-geo entities table
# ----------------------------------
nongeotablename = "netowl_entities"

if arcpy.Exists(nongeotablename) is False:
    arcpy.CreateTable_management(wk, nongeotablename, "netowl_template_nogeo")  # noqa: E501

iCur_links = arcpy.da.InsertCursor(nongeotablename, ["RDFID", "RDFVALUE", "TIMEST", "RDFLINKS", "ORGDOC", "UNIQUEID", "TYPE"])  # noqa: E501

for d in rdfobjs:

    fieldobjs = []
    fieldobjs.append(d.id)
    fieldobjs.append(d.value)
    fieldobjs.append(d.timest)
    ll = nof.make_link_list(d.links)
    fieldobjs.append(ll)
    fieldobjs.append(d.orgdoc)
    fieldobjs.append(d.id + str(d.timest))
    fieldobjs.append(d.type)
    iCur_links.insertRow(fieldobjs)

del iCur_links


# ----------------------------------
#   Build relationship links table
# ----------------------------------

linktablename = "netowl_links"
if arcpy.Exists(linktablename) is False:
    arcpy.CreateTable_management(wk, linktablename, "netowl_template_links")

iCur_links = arcpy.da.InsertCursor(linktablename, ["LINKID", "FROMID", "TOID", "FROMVALUE", "TOVALUE", "FROMROLE", "TOROLE", "FROMROLETYPE", "TOROLETYPE", "UNIQUETS"])  # noqa: E501

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

del iCur_links

# ----------------------------------
#         Build events table
# ----------------------------------

eventtablename = "netowl_events"
if arcpy.Exists(eventtablename) is False:
    arcpy.CreateTable_management(wk, eventtablename, "netowl_template_events")

iCur_events = arcpy.da.InsertCursor(eventtablename, ["LINKID", "FROMID", "TOID", "FROMVALUE", "TOVALUE", "FROMROLE", "TOROLE", "ORGDOC", "EVENTVALUE"])  # noqa: E501

for ev in eventobjs:

    fieldobjs = []
    fieldobjs.append(ev.eventid + str(ev.timest))
    fieldobjs.append(ev.fromid + str(ev.timest))
    if ev.toid is not None:  # account for events with no relationships
        fieldobjs.append(ev.toid + str(ev.timest))
    else:
        fieldobjs.append("None")
    fieldobjs.append(ev.fromvalue)
    fieldobjs.append(ev.tovalue)
    fieldobjs.append(ev.fromrole)
    fieldobjs.append(ev.torole)
    fieldobjs.append(ev.orgdoc)
    fieldobjs.append(ev.eventvalue)

    iCur_events.insertRow(fieldobjs)

del iCur_events

print("Script completed.")
