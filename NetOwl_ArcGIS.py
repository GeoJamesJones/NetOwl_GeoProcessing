import os
import json
import arcpy
import requests
import glob
import zipfile
import pandas as pd

from rdflib import Graph
from gastrodon import LocalEndpoint, one, QName
from arcgis.gis import GIS

##Variables

docsPath = arcpy.GetParameterAsText(0)
rdfOutDir = arcpy.GetParameterAsText(1)
outBaseName = arcpy.GetParameterAsText(2)
fileOutDir = arcpy.GetParameterAsText(3)
userName = arcpy.GetParameterAsText(4)
passWord = arcpy.GetParameterAsText(5)

gis = GIS(fileOutDir, username=userName, password=passWord)

rdfOutExt = '.rdf'


# Defines a function that will pass documents derived from the list
# above to the NetOwl API.
# Function checks the type of document and makes necessary adjustment
# to the POST command.
# Function has three inputs:
#    1.  inFile:  This is the file that will be passed to the NetOwl API
#    2.  outPath: Path where the output file will be saved
#    3.  outExtension:  the file type that will be saved (RDF, etc..)

def netowlCurl(inFile, outPath, outExtension):
    headers = {
        'accept': 'application/rdf+xml',
        'Authorization': 'netowl ff5e6185-5d63-459b-9765-4ebb905affc8',
    }

    if inFile.endswith(".txt"):
        headers['Content-Type'] = 'text/text'
        print("Document is a text file...")
    elif inFile.endswith(".pdf"):
        headers['Content-Type'] = 'application/pdf'
        print("Document is a PDF...")
    elif inFile.endswith(".docx"):
        headers['Content-Type'] = 'application/msword'
        print("Document is a Word Document...")

    params = (
        ('language', 'english'),
    )

    data = open(inFile, 'rb').read()
    response = requests.post('https://api.netowl.com/api/v2/_process', headers=headers, params=params, data=data,
                             verify=False)
    r = response.text
    outPath = outPath
    fileName = os.path.split(d)[1]
    if os.path.exists(outPath) == False:
        os.mkdir(outPath, mode=0o777, )
    outFile = os.path.join(outPath, fileName + outExtension)
    # print(len(r))
    # print(outFile)
    open(outFile, "w", encoding="utf-8").write(r)


# Walks through the docsPath, identifying files, and appends them to a list.
docs = []
for root, dirs, files in os.walk(docsPath):
    for f in files:
        filePath = os.path.join(root, f)
        docs.append(filePath)

# Iterates though the docs list created previously and
# runs the function for each of the documents found.
# Passes the function a document derived from the list,
# and two variables created in a previous step.

for d in docs:
    netowlCurl(d, rdfOutDir, rdfOutExt)

# Creates a Graph Object that will store all the result of a parse operation
# in the next step.
g = Graph()

# Walks through output path from the netowlCurl function and parses all RDF/XML Documents
for root, dir, files in os.walk(rdfOutDir):
    for file in files:
        if file.endswith(rdfOutExt):
            filePath = os.path.join(root, file)
            print("Parsing " + file + "...")
            try:
                g.parse(filePath, format='xml')
            except Exception as ex:
                print(ex)

# Create Local SPARQL Endpoint on graph created in previous step
e = LocalEndpoint(g)

#Queries the SPARQL endpoint for the various addresses located in the documents
address=e.select("""
   SELECT ?s ?o ?label{
      ?s netowl:Entity.Address.Mail..name ?o .
      ?s rdfs:label ?label .
    }
""")
address.set_index("label")

#Geocodes the addresses and adds them to the map widget as a feature collection
locations = gis.content.import_data(address, {"Address" : "label"})

#Creates a hosted feature service from the feature
# collection created in the previous step
titleAdd  = outBaseName + "_Address"
loc_properties = {
    "title":titleAdd,
    "text": json.dumps({"featureCollection": {"layers": [dict(locations.layer)]}}),
    "type":"Feature Collection"}
loc = gis.content.add(loc_properties)

#Uses the SPARQL endpoint to query all of the relationship types and returns the top 10
triplesSel=e.select("""
   SELECT ?s ?p ?o ?label ?type{
      ?s ?p ?o .
      ?s rdfs:label ?label .
      ?s rdf:type ?type .
    }
""")
tripleList = os.path.join(rdfOutDir, 'triples.csv')
triplesSel.to_csv(tripleList, sep=',', encoding='utf-8')
df = pd.read_csv(tripleList)

#Queries the SPARQL endpoint for the various addresses located in the documents
address = df[df['p'].str.contains('Place')]

#Geocodes the addresses and adds them to the map widget as a feature collection
locations = gis.content.import_data(address, {"Address" : "label"})

#Creates a hosted feature service from the feature
# collection created in the previous step
titlePlace = outBaseName + "_Place"
loc_properties = {
    "title":titlePlace,
    "text": json.dumps({"featureCollection": {"layers": [dict(locations.layer)]}}),
    "type":"Feature Collection"}
loc = gis.content.add(loc_properties)

#Queries for the MGRS coordinates and writes them to a CSV file
mgrs=e.select("""
   SELECT ?s ?o ?label{
      ?s netowl:Entity.Numeric.Coordinate.Mgrs..name ?o .
      ?s rdfs:label ?label .
    }
""")

mgrs.set_index("o")
mgrs_file = os.path.join(rdfOutDir,'mgrs_coords.csv')
mgrs.to_csv(mgrs_file, sep=',', encoding='utf-8')

#Converts coordinates located in the MGRS CSV into Lat/Longs, turns this into a shapefile
outShpDir = os.path.join(rdfOutDir, 'OutShp')
outName = outBaseName + 'MGRS.shp'
if os.path.exists(outShpDir) == False:
    os.mkdir(outShpDir, mode=0o777,)
arcpy.ConvertCoordinateNotation_management(in_table=mgrs_file, out_featureclass=os.path.join(outShpDir,outName), x_field="o", y_field="o", input_coordinate_format="MGRS", output_coordinate_format="DD_NUMERIC", id_field="",
                                           spatial_reference="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119522E-09;0.001;0.001;IsHighPrecision",
                                           in_coor_system="GEOGCS['GCS_WGS_1984',DATUM['D_WGS_1984',SPHEROID['WGS_1984',6378137.0,298.257223563]],PRIMEM['Greenwich',0.0],UNIT['Degree',0.0174532925199433]]", exclude_invalid_records="INCLUDE_INVALID")

#Zips up the shapefile created in the previous step
outZip = fileOutDir

def zipShapefilesInDir(inDir, outDir):
    if not os.path.exists(inDir):
        arcpy.AddMessage("Input directory %s does not exist!" % inDir)
        return False

    if not os.path.exists(outDir):
        arcpy.AddMessage("Creating output directory %s" % outDir)
        os.mkdir(outDir)

    arcpy.AddMessage("Zipping shapefile(s) in folder %s to output folder %s" % (inDir, outDir))

    for inShp in glob.glob(os.path.join(inDir, "*.shp")):
        global outZip
        outZip = os.path.join(outDir, os.path.splitext(os.path.basename(inShp))[0] + ".zip")

        zipShapefile(inShp, outZip)
    return True


def zipShapefile(inShapefile, newZipFN):
    arcpy.AddMessage('Starting to Zip ' + (inShapefile) + ' to ' + (newZipFN))

    if not (os.path.exists(inShapefile)):
        arcpy.AddMessage(inShapefile + ' Does Not Exist')
        return False

    if (os.path.exists(newZipFN)):
        arcpy.AddMessage('Deleting ' + newZipFN)
        os.remove(newZipFN)

    if (os.path.exists(newZipFN)):
        arcpy.AddMessage('Unable to Delete' + newZipFN)
        return False

    zipobj = zipfile.ZipFile(newZipFN, 'w')

    for infile in glob.glob(inShapefile.lower().replace(".shp", ".*")):
        if os.path.splitext(infile)[1].lower() != ".zip":
            arcpy.AddMessage("Zipping %s" % (infile))
            zipobj.write(infile, os.path.basename(infile), zipfile.ZIP_DEFLATED)

    zipobj.close()
    return True

zipShapefilesInDir(outShpDir, rdfOutDir)

#Uploads the shapefile to ArcGIS Online and publishes it as a feature service
titleMGRS = outBaseName + '_MGRS'
tempItem = gis.content.add({"title":titleMGRS, "type":"Shapefile"}, outZip)
mgrsLyr = tempItem.publish()
