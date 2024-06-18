/*
This Terraform templates sets up the necessary resources needed to run this Agentic LLM application. 

The app can run either on your local laptop or on a virtual machine you setup (in my case, a AWS VM).

In the default setup, this app runs on your local laptop and only a Couchbase Capella cluster is created. Port Forwarding is needed to forward incoming Couchbase Eventing calls to your local machine. 

In the case where Port Forwarding is not, you can alternatively deploy the app on a VM. In this case, uncomment the AWS resource code code block below to get going. 
*/



#aws vm instance for running the chatbot
/*
provider "aws" {
    region = "ap-southeast-1"
    access_key = var.access_key
    secret_key = var.secret_key
}


resource "aws_instance" "web" {
  ami           = "ami-0b287aaaab87c114d"
  instance_type = "t3.2xlarge"
  vpc_security_group_ids = ["sg-0bf97419aaad88160"] // if no security group needs be specified, delete this line

  user_data = <<-EOF
                #!/bin/bash
                sudo yum update -y
                sudo yum install git -y
                sudo yum install python3 -y
                sudo yum install python3-pip -y
                git clone https://github.com/sillyjason/chatbot-cb-2
                cd chatbot-cb-2
                python3 -m venv venv
                source venv/bin/activate
                pip install -r requirements.txt
                cat > .env <<- EOF
                #EE Environment Variables
                

                #Capella Environment Variables
                

                #Chatbot Endpoint
                
                #CB User Credential

                #LLM Keys
                EOF

  tags = {
    Name = "rag-with-couchbase"
  }
}
*/

#capella setup 
terraform {
  required_providers {
    couchbase-capella = {
      source  = "registry.terraform.io/couchbasecloud/couchbase-capella"
    }
  }
}
 

provider "couchbase-capella" {
  authentication_token = var.auth_token
}


# Create  cluster resource
resource "couchbase-capella_cluster" "agentic-capella-cluster" {
  organization_id = var.organization_id
  project_id      = var.project_id
  name            = "Agentic Ticketing"
  description     = "Agentics Ticketing System with Couchbase Capella" 
  cloud_provider = {
    type   = "aws"
    region = "ap-southeast-1"
    cidr   = "10.0.42.0/23"
  }
  couchbase_server = {
    version = "7.6"
  }
  service_groups = [
    {
      node = {
        compute = {
          cpu = 8
          ram = 16
        }
        disk = {
          storage = 50
          type    = "gp3"
          iops    = 3000
        }
      }
      num_of_nodes = 3
      services     = ["data"]
    },
    {
      node = {
        compute = {
          cpu = 8
          ram = 16
        }
        disk = {
          storage = 50
          type    = "gp3"
          iops    = 3000
        }
      }
      num_of_nodes = 2
      services     = ["index", "query", "search"]
    },
    {
      node = {
        compute = {
          cpu = 8
          ram = 16
        }
        disk = {
          storage = 50
          type    = "gp3"
          iops    = 3000
        }
      }
      num_of_nodes = 2
      services     = ["eventing"]
    }
  ]
  availability = {
    "type" : "multi"
  }
  support = {
    plan     = "developer pro"
    timezone = "PT"
  }
}

# Create bucket main
resource "couchbase-capella_bucket" "main_bucket" {
  name                       = "main"
  organization_id            = var.organization_id
  project_id                 = var.project_id
  cluster_id                 = couchbase-capella_cluster.agentic-capella-cluster.id
  type                       = "couchbase"
  storage_backend            = "couchstore"
  memory_allocation_in_mb    = 10000
  bucket_conflict_resolution = "seqno"
  durability_level           = "none"
  replicas                   = 1
  flush                      = true
  time_to_live_in_seconds    = 0
  eviction_policy            = "fullEviction"
}

# Create bucket meta
resource "couchbase-capella_bucket" "meta_bucket" {
  name                       = "meta"
  organization_id            = var.organization_id
  project_id                 = var.project_id
  cluster_id                 = couchbase-capella_cluster.agentic-capella-cluster.id
  type                       = "couchbase"
  storage_backend            = "couchstore"
  memory_allocation_in_mb    = 1000
  bucket_conflict_resolution = "seqno"
  durability_level           = "none"
  replicas                   = 1
  flush                      = true
  time_to_live_in_seconds    = 0
  eviction_policy            = "fullEviction"
}



# Create scope data 
resource "couchbase-capella_scope" "scope_data" {
    scope_name           = "data" 
    organization_id      = var.organization_id
    project_id           = var.project_id
    cluster_id           = couchbase-capella_cluster.agentic-capella-cluster.id
    bucket_id            = couchbase-capella_bucket.main_bucket.id
}


resource "couchbase-capella_collection" "collection_policies" {
    collection_name      = "policies"
    organization_id      = var.organization_id
    project_id           = var.project_id
    cluster_id           = couchbase-capella_cluster.agentic-capella-cluster.id
    bucket_id            = couchbase-capella_bucket.main_bucket.id
    scope_name           = couchbase-capella_scope.scope_data.scope_name
}

resource "couchbase-capella_collection" "collection_messages" {
    collection_name      = "messages"
    organization_id      = var.organization_id
    project_id           = var.project_id
    cluster_id           = couchbase-capella_cluster.agentic-capella-cluster.id
    bucket_id            = couchbase-capella_bucket.main_bucket.id
    scope_name           = couchbase-capella_scope.scope_data.scope_name
}


resource "couchbase-capella_collection" "collection_products" {
    collection_name      = "products"
    organization_id      = var.organization_id
    project_id           = var.project_id
    cluster_id           = couchbase-capella_cluster.agentic-capella-cluster.id
    bucket_id            = couchbase-capella_bucket.main_bucket.id
    scope_name           = couchbase-capella_scope.scope_data.scope_name
}


resource "couchbase-capella_collection" "collection_orders" {
    collection_name      = "orders"
    organization_id      = var.organization_id
    project_id           = var.project_id
    cluster_id           = couchbase-capella_cluster.agentic-capella-cluster.id
    bucket_id            = couchbase-capella_bucket.main_bucket.id
    scope_name           = couchbase-capella_scope.scope_data.scope_name
}


resource "couchbase-capella_collection" "collection_refunds" {
    collection_name      = "refund_tickets"
    organization_id      = var.organization_id
    project_id           = var.project_id
    cluster_id           = couchbase-capella_cluster.agentic-capella-cluster.id
    bucket_id            = couchbase-capella_bucket.main_bucket.id
    scope_name           = couchbase-capella_scope.scope_data.scope_name
}


resource "couchbase-capella_collection" "collection_message_responses" {
    collection_name      = "message_responses"
    organization_id      = var.organization_id
    project_id           = var.project_id
    cluster_id           = couchbase-capella_cluster.agentic-capella-cluster.id
    bucket_id            = couchbase-capella_bucket.main_bucket.id
    scope_name           = couchbase-capella_scope.scope_data.scope_name
}

