#!/bin/bash
################################################################################
# Author      : Seunghwan Shin 
# Create date : 2023-07-18 
# Description : 
#	    
# History     : 2023-07-18 Seunghwan Shin       # first create
################################################################################

RE="^[0-9]+$"               # Regular expression pattern to verify that input characters exist only as numbers
NODE_SELECT_BOOL=true
NODE_ADDR_PORT_INFO=true

#check for ROOT user
if [ "$(id -u)" -ne 0 ] ; 
then
        echo "You must run this script as root. Sorry!"
        exit 1
fi

echo "Welcome to the Elasticsearch Index Management"
echo "This script will help you easily managing index of elasticsearch"
echo

mkdir elasticsearch_index_clear

cd elasticsearch_index_clear

mkdir delete_log
mkdir server_log

touch server_info.json

## Elasticsearch cluster ip:port array to configure
declare -a CLUSTER_ARR

# Steps to enter elasticsearch cluster information
while [ $NODE_SELECT_BOOL = true ]
do
    # Gets the NUMBER OF NODES in the cluster.
    read -p "Please enter number of nodes in Elasticsearch Cluster :  " ELASTIC_NODE_CNT

    if ! [[ $ELASTIC_NODE_CNT =~ $RE ]]
    then
        echo "Please answer with numbers only."
        continue
    fi
    

    # Get IP address and PORT number of each node in elasticsearch cluster
    for ((i=1;i<=$ELASTIC_NODE_CNT;i++))
    do
        read -p "Please enter IP ADDRESS of [$i] nodes in Elasticsearch Cluster :  " ELASTIC_NODE_IP
        read -p "Please enter PORT NUMBER address of [$i] nodes in Elasticsearch Cluster :  " ELASTIC_NODE_PORT
        CLUSTER_ARR[$i]=$ELASTIC_NODE_IP':'$ELASTIC_NODE_PORT
    done


    # Get ACCOUNT information of elasticsearch cluster
    read -p "Please enter the ID of your Elasticsearch cluster account :  " ELASTIC_ID
    _ELASTIC_ID="elastic"

    if [ -z "$ELASTIC_ID" ] ; then
        ELASTIC_ID=$_ELASTIC_ID
        echo "Selected default - $ELASTIC_ID"
    fi
    
    read -p "Please enter the PW of your Elasticsearch cluster account :  " ELASTIC_PW
    _ELASTIC_PW="1234"
    
    if [ -z "$ELASTIC_PW" ] ; then
        ELASTIC_PW=$_ELASTIC_PW
        echo "Selected default - $ELASTIC_PW"
    fi

    read -p "Please enter the VERSION of your Elasticsearch cluster :  " ELASTIC_VERSION
    _ELASTIC_VERSION=7

    if [ -z "$ELASTIC_VERSION" ] ; then
        ELASTIC_VERSION=$_ELASTIC_VERSION
        echo "Selected default - $ELASTIC_VERSION"
    fi

    # Check the information configured by the user
    echo -e "\n"
    echo "=============================  Selected config  =================================="
    echo -e "\n"
    
    echo "[ NODE ip/addr info ]"
    for ((i=1;i<=$ELASTIC_NODE_CNT;i++))
    do
        echo "[$i] node ip address/port             : " ${CLUSTER_ARR[$i]}
    done
    
    echo -e "\n"
    echo "[ Elasticsearch Cluster Account info ]"
    echo "Cluster Account ID                      : $ELASTIC_ID"
    echo "Cluster Account PW                      : $ELASTIC_PW"
    echo "Cluster VERSION                         : $ELASTIC_VERSION"
    
    read -p "Is this ok? Then press ENTER to go on or Ctrl-C to abort." _UNUSED_

    NODE_SELECT_BOOL=false

done



# Process of writing ES node information in server_info.json file
SCRIPT=$(readlink -f $0)                    # Absolute path to this script
SCRIPTPATH=$(dirname $SCRIPT)               # Absolute path this script is in
JSON_FILE="$SCRIPTPATH/server_info.json"    # The path where the "server_info.json" file actually exists

# Check if server_info.json file exists
if [ -e $JSON_FILE ]
then
    
    echo '{' >> $JSON_FILE
    printf '\t"cluster_ip_port": [' >> $JSON_FILE

    for ((i=1;i<=$ELASTIC_NODE_CNT;i++))
    do  
        if [ $i -eq $ELASTIC_NODE_CNT ]
        then
            ES_IP_ADDR+='"'${CLUSTER_ARR[$i]}'"],'
        else
            ES_IP_ADDR+='"'${CLUSTER_ARR[$i]}'",'
        fi
    done
    
    echo $ES_IP_ADDR >> $JSON_FILE

    printf '\t"id": "'$ELASTIC_ID'",' >> $JSON_FILE

    echo >> $JSON_FILE
    printf '\t"pw": "'$ELASTIC_PW'",' >> $JSON_FILE

    echo >> $JSON_FILE
    printf '\t"ver": "'$ELASTIC_VERSION'"' >> $JSON_FILE

    echo >> $JSON_FILE
    echo '}' >> $JSON_FILE
fi
