# NetOwl_GeoProcessing
In order to run this demo, first download this GitHub repo.  

Once that is done, add the toolbox to your ArcGIS Pro Project.  
The toolbox currently has 3 items in it.  
  1.  Create Links (model) - This model is designed to be used after running the NetOwl Unstructured Processing script. This model creates        the necessary Relationship Classes to show the utility and power of linked data. 
  2. NetOwl Unstructured Processing (script) - This script is the first version of the NetOwl interaction with ArcGIS Pro.  It allows a         user to pass a folder containing documents (Word, text, PDF, HTML, etc...) to the NetOwl API and returns a series of JSON documents.       It outputs a Feature Class and 3 tables (NetOwl Events, NetOwl Entities, NetOwl Links). 
      In order to run this tool, there are 3 Inputs:
        Input 1:  Documents Path - the location of the source documents of which you want to run against the NetOwl API
        Input 2:  Output Directory - the location where the JSON Documents will be stored
        Input 3:  Output Workspace - The location of the output geodatabase where the feature classes and tables will be created
