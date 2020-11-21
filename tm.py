#!/usr/bin/env python3


# TM, Element, Server, ExternalEntity, Datastore, Actor, Process, SetOfProcesses, Dataflow, Boundary and Lambda.

from pytm.pytm import TM, Server, Datastore, Dataflow, Boundary, Actor, Lambda, Element, Process, ExternalEntity, Classification

tm = TM("LetterApp flow diagram")
tm.description = """LetterApp is a cloud-based and machine learning-powered document-management 
                    and workflow system which allow users to upload documents and access 
                    them from a Web client and a mobile client, as well as programtically 
                    through a group of Restful API's. Besides making the documents avaiable 
                    across devices, it also allows for flow management - users can group, tag, 
                    and track activities related to each document. Computer vision helps users
                    with automatic tagging and entity extraction. Users can also send letters, 
                    faxes na messages straight from the app. Since the nature of the data stored 
                    is sensitve, security is of heightened importance for the app's development."""

tm.isOrdered = True
tm.mergeResponses = True
tm

#Actors
#TODO add mobile client?  programtic user? anonymous user? 
#External Entities - out of control 
#Sendgrid 

#External Entities / Processes / Actors
web_user = ExternalEntity('Web User') 
administrator = ExternalEntity('Administrator')
mobile_client = ExternalEntity("Mobile Client")
direct_api = ExternalEntity("API programatic access")
browser = ExternalEntity("Web Browser")
sendgrid = ExternalEntity("Sendgrid Server")
sendgrid.inScope = False

# Servers
eureka_service_discovery = Server("Eureka Service Discovery")
nginx_backend_server = Server("Nginx Backend Reverse Proxy and Load Balancer")

# Processes
react_webapp = Process("Webserver - React Frontend")

identity_service = Process("Flask Identity Service")
image_service = Process("Flask Image Service")
resources_service = Process("Flask Resouces Service")
search_service = Process("Flask Search Service")

elastic_search_resources = Process("Flask Elastic Search Resources")


# Data Storages
identity_db = Datastore("Identity - Mongo Atlas DB")
token_blacklist_db = Datastore("Token Blacklist DB - Mongo Atlas DB")
resources_db = Datastore("Resources - Mongo Atlas DB")
s3_bucket = Datastore("AWS S3 Bucket - Persistent")



# Monitoring 
kibana = Process("Kibana Visualising Dashboard")
elastic_search_monitoring = Process("Elasticsearch Monitoring")
logstash = Process("Logstash")
heartbeat = Process("Heartbeat")
apm_server = Process("Apm Server")

# Boundraries
hosted_services = Boundary("LetterApp DMZ")
mongo_atlas = Boundary("Mongo Atlas Cluster")
aws = Boundary("AWS VPC")
external_services = Boundary("External Services")
internet = Boundary("Internet")
frontend = Boundary("Frontend")
backend = Boundary("Backend")
monitoring_vpc = Boundary("Monitoring VPC")
monitoring_vpc.inBoundary = hosted_services


# Add elements to boundraries
monitong_elements = [kibana, elastic_search_monitoring, logstash, heartbeat, apm_server]
for element in monitong_elements:
    element.inBoundary = monitoring_vpc


# internet_elements = [web_user, administrator, mobile_client, direct_api, browser]
# for service in internet_elements:
#     service.inBoundary = internet

# flask_services = [identity_service, image_service, resources_service, search_service]
# other_hosted_services = [elastic_search_resources, eureka_service_discovery, nginx_backend_server]
# for service in flask_services + other_hosted_services:
#     if service.name != "React Frontend Client":
#         service.inBoundary = backend
# for service in [backend, react_webapp]:
#     service.inBoundary = hosted_services

flask_services = [identity_service, image_service, resources_service, search_service]
other_hosted_services = [react_webapp, elastic_search_resources, eureka_service_discovery, nginx_backend_server]
for service in flask_services + other_hosted_services:
    service.inBoundary = hosted_services



aws_services = [s3_bucket]
for service in aws_services:
    service.inBoundary = aws

mongo_services = [identity_db, token_blacklist_db, resources_db]
for service in mongo_services:
    service.inBoundary = mongo_atlas
sendgrid.inBoundary = external_services
#TODO
# aws.inBoundary = external_services
# mongo_atlas.inBoundary = external_services


# Dataflows
user_browser = Dataflow(web_user, browser, "User Accesing Webapp")
browser_user = Dataflow(browser, web_user, "Responses to user")
browser_user.responseTo = user_browser


browser_webserver = Dataflow(browser, react_webapp, "User Accesing Webapp")
webserver_browser = Dataflow(react_webapp, browser, "Responses to user")
webserver_browser.responseTo = browser_webserver


for entity in [browser, mobile_client, direct_api]:
    to_webserver = Dataflow(entity, nginx_backend_server, "{} acessing api".format(entity.name))
    from_webserver = Dataflow(nginx_backend_server, entity, "Responses to {}".format(entity.name))
    from_webserver.responseTo = to_webserver

# web_user
# administrator
# mobile_client
# direct_api
# browser

webapp_to_nginx = Dataflow(react_webapp, nginx_backend_server, "Webclient to Gateway")
nginx_to_webapp = Dataflow(nginx_backend_server, react_webapp, "Gatway to Webclient")
nginx_to_webapp.responseTo = webapp_to_nginx
webapp_to_nginx.protocol = "https"
identity_to_sendgrid = Dataflow(identity_service, sendgrid, "Request to email server")

for service in flask_services:
    dataflow_request = Dataflow(nginx_backend_server, service, "Requests")
    dataflow_response = Dataflow(service, nginx_backend_server, "Responses")
    dataflow_request.protocol = "HTTPS"
    dataflow_response.protocol = "HTTPS"
    dataflow_request.dstPort = 80
    dataflow_response.dstPort = 540
    dataflow_request.data = "Requests and Responses"
    dataflow_response.data = "Requests and Responses"
    dataflow_response.responseTo = dataflow_request

search_to_elastic = Dataflow(search_service, elastic_search_resources, "Search Lookups")
elastic_to_search = Dataflow(elastic_search_resources, search_service, "Search Resulsts")
elastic_to_search.responseTo = search_to_elastic

eureka_to_nginx = Dataflow(eureka_service_discovery, nginx_backend_server, "Container Registration")

for service in flask_services:
    dataflow = Dataflow(service, eureka_service_discovery, "Container Registration")

for service in flask_services:
    if service.name == "Flask Identity Service": 
        to_db = Dataflow(service, token_blacklist_db, "CRUD Operations")
        to_service = Dataflow(token_blacklist_db, service, "CRUD Operation Results")
        to_db.respnseTo = to_service
    else:
        to_db = Dataflow(service, token_blacklist_db, "Read-only Queries")
        to_service = Dataflow(token_blacklist_db, service, "Operation Results")
        to_service.responseTo = to_db

identity_to_db = Dataflow(identity_service, identity_db, "CRUD Operations")
db_to_identity = Dataflow(identity_db, identity_service, "CRUD Operation Results")
db_to_identity.responseTo = identity_to_db

resources_to_db = Dataflow(resources_service, resources_db, "CRUD Operations")
db_to_resources = Dataflow(resources_db, resources_service, "CRUD Operation Results")
db_to_resources.responseTo = resources_to_db  


for service in [image_service, resources_service]:
    to_bucket = Dataflow(resources_service, s3_bucket, "Request for images in S3")
    from_bucket = Dataflow(s3_bucket, resources_service, "Response for images in S3")
    to_bucket.protocol = "HTTPS"
    from_bucket.protocol = "HTTPS"
    from_bucket.responseTo = to_bucket

for service in flask_services:
    to_apm_server = Dataflow(service, apm_server, "Api Monitoring Data")
    to_heartbeat = Dataflow(service, heartbeat, "Heartbeat Data")
    to_logstash = Dataflow(service, logstash, "Logstash Data")

for process in [heartbeat, logstash, apm_server]:
    to_elasticsearch = Dataflow(process, elastic_search_monitoring, "Elasticsearch Monitoring Data Ingestion")

elastic_to_kibana = Dataflow(elastic_search_monitoring, kibana, "Kibana Data Ingestion")
administrator_to_kibana = Dataflow(administrator, kibana, "Request Data")
kibana_to_administrator = Dataflow(kibana, administrator, "Display Data")
kibana_to_administrator.responseTo = administrator_to_kibana
# identity_db,  resources_db

#Define connections 
#ADD ALL PROTOCOLS 
#ADD authentication scheme used 


# User and Client
# user_to_web = Dataflow(user, web_client, "User enters comments (*)")
# user_to_web.protocol = "HTTP"
# user_to_web.dstPort = 80
# user_to_web.data = 'Comments in HTML or Markdown'

# web_to_user = Dataflow(web_client, user, "Comments saved (*)")
# web_to_user.protocol = "HTTP"
# web_to_user.data = 'Ack of saving or error message, in JSON'


# # Services
# apigw = Server("API Gateway - Reverse Proxy - Load Balancer - NGinx")
# apigw.port = 1337

# auth_service = Process("Auth Service")
# auth_service.authenticationScheme = "JWT Token"

# img_api = Server("Image Processing API")
# users_api = Server("Users and Documents API")
# search_service = Server("Search Serivice")




# # Data Flows
# # Gateways to API
# apigw_to_auth = Dataflow(apigw, auth_service, "HTTPS")
# apigw_to_img_api = Dataflow(apigw, img_api, "HTTPS")
# apigw_to_users_api = Dataflow(apigw, users_api, "HTTPS")
# apigw_to_search_services = Dataflow(apigw, search_service, "HTTPS")

# # Services to Storage
# auth_service_to_auth_db = Dataflow(auth_service, auth_db, "mongo connection")
# img_api_to_img_db = Dataflow(img_api, img_db, "mongo connection")
# users_api_to_users_db = Dataflow(users_api, users_db, "mongo connection")

# # Services to Buckets
# img_api_to_bucket_temp = Dataflow(img_api, bucket_temp, "aws https")
# users_api_to_bucket_persistent = Dataflow(users_api, bucket_persistent, "aws https")




# # Adding elements to boundraries
# clients_list = [mobile_client, web_client, direct_api]
# for client in clients_list:
#     client.inBoundary = clients

# #services boundrary 
# services_list = [apigw, auth_service, img_api,
#                 users_api, search_service]
# for service in services_list:
#     service.inBoundary = backend

# #aws boundrary
# aws_list = [bucket_temp, bucket_persistent]
# for service in aws_list:
#     service.inBoundary = aws

# # Mongo Boundary
# for db in [auth_db, users_db, img_db]:
#     db.inBoundary = mongo

# # Client - server
# for client in clients_list:
#     dataflow_request = Dataflow(client, apigw, "HTTPS Requests")
#     dataflow_response = Dataflow(apigw, client, "HTTPS Responses")
#     dataflow_request.implementsAuthenticationScheme = True




# User_Mobiile = Boundary("User/Mobile")
# Web_DB = Boundary("Web/DB")

# user = Actor("User")
# user.inBoundary = User_Web

# web = Server("Web Server")
# web.OS = "CloudOS"
# web.isHardened = True

# db = Datastore("Mongo Atlas Database (*)")
# db.OS = "CentOS"
# db.isHardened = True
# db.inBoundary = Web_DB
# db.isSql = False
# db.inScope = False

# my_lambda = Lambda("cleanDBevery6hours")
# my_lambda.hasAccessControl = True
# my_lambda.inBoundary = Web_DB

# my_lambda_to_db = Dataflow(my_lambda, db, "(&lambda;)Periodically cleans DB")
# my_lambda_to_db.protocol = "SQL"
# my_lambda_to_db.dstPort = 3306



# web_to_db = Dataflow(web, db, "Insert query with comments")
# web_to_db.protocol = "MySQL"
# web_to_db.dstPort = 3306
# web_to_db.data = 'MySQL insert statement, all literals'

# db_to_web = Dataflow(db, web, "Comments contents")
# db_to_web.protocol = "MySQL"
# db_to_web.data = 'Results of insert op'

tm.process()