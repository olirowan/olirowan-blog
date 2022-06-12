#!/bin/bash

APPLICATION_ENVIRONMENT="production"
APPLICATION_PROJECT="olirowan-blog"
APPLICATION_DIRECTORY="olirowan-blog"

echo "" && echo "Parameters Set:" && echo ""

if [ ! -z "$APPLICATION_ENVIRONMENT" ] ; then
    echo "Environment set to: $APPLICATION_ENVIRONMENT"
else
    echo "Environment not set, exiting."
    exit 1
fi

if [ ! -z "$APPLICATION_PROJECT" ] ; then
    echo "Project set to: $APPLICATION_PROJECT"
else
    echo "Project not set, exiting."
    exit 1
fi

if [ ! -z "$APPLICATION_DIRECTORY" ] ; then
    echo "Directory set to: $APPLICATION_DIRECTORY"
else
    echo "Directory not set, exiting."
    exit 1
fi

echo ""

# Download archive from minio
# mc --config-dir /home/oli/.mc/ cp homelab/smart-irrigation-$APPLICATION_ENVIRONMENT/$APPLICATION_PROJECT.tgz /tmp/$APPLICATION_PROJECT.tgz || exit 1
tar -xzvf /tmp/$APPLICATION_PROJECT.tgz -C /app/shares/$APPLICATION_DIRECTORY/ --overwrite || exit 1

# Download environment file from minio
# mc --config-dir /home/oli/.mc/ cp homelab/smart-irrigation-$APPLICATION_ENVIRONMENT/$APPLICATION_PROJECT-worker.env /app/shares/$APPLICATION_DIRECTORY/.env || exit 1

# Set permissions and ownership on environment file
chown olirowanxyz:olirowanxyz /app/shares/$APPLICATION_DIRECTORY/.env
chmod 664 /app/shares/$APPLICATION_DIRECTORY/.env

# Set permissions and recursive owership on install directory
chown -R olirowanxyz:olirowanxyz /app/shares/$APPLICATION_DIRECTORY/
chmod 775 /app/shares/$APPLICATION_DIRECTORY/

# Remove temporary archive
rm /tmp/$APPLICATION_PROJECT.tgz

# Restart jobs
echo "" && echo "Restarting Supervisor Jobs" && echo ""
supervisorctl stop all
supervisorctl start all

echo "" && echo "Process complete" && echo ""

