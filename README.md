In order to run this demo, first download this GitHub repo.  



Once that is done, add the toolbox to your ArcGIS Pro Project.  
The toolbox currently has 3 items in it.  
  
	1.  Create Links (model) - This model is designed to be used after running the NetOwl Unstructured Processing script. This model creates the necessary Relationship Classes to show the utility and power of linked data. 
  

	2. NetOwl Unstructured Processing (script) - This script is the first version of the NetOwl interaction with ArcGIS Pro.  It allows a user to pass a folder containing 		documents (Word, text, PDF, HTML, etc...) to the NetOwl API and returns a series of JSON documents. It outputs a Feature Class, 2 tables (NetOwl Entities, NetOwl Links), and 5 Relationship Classes. 
      

	In order to run this tool, there are 3 inputs:
        

		Input 1:  Documents Path - the location of the source documents of which you want to run against the NetOwl API
        
		Input 2:  Output Directory - the location where the JSON Documents will be stored
        
		Input 3:  Output Workspace - The location of the output geodatabase where the feature classes and tables will be created

	3.  NetOwl Version 2 (script) - This is the current version of the NetOwl integration with ArcGIS Pro.  It allows a user to pass a folder containing documents (Word, text, PDF, HTML, etc...) to the NetOwl API and returns a series of JSON documents.  It creates an output feature class, 3 tables (NetOwl Events, NetOwl Entities, NetOwl Links), and 5 relationship classes.  
	
	In order to run this tool, there are 3 inputs:

		Input 1:  Documents Path - the location of the source documents of which you want to run against the NetOwl API
        
		Input 2:  Output Directory - the location where the JSON Documents will be stored
        
		Input 3:  Output Workspace - The location of the output geodatabase where the feature classes and tables will be created  

	
