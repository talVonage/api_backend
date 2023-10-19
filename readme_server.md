# neru configuration

Install Neru CLI

    curl -O https://api-eu.vonage.com/v1/neru/i/neru-59e69cd7-neru-cli-install-dist/neru-cli_linux_amd64/neru
    chmod +x ./neru 
    mv ./neru /usr/local/bin

Update Neru version

    neru assets get .neru/cli-releases/v0.8.27/neru_darwin_amd64.tar.gz ./ 		# download
    tar -zxf neru_darwin_amd64.tar.gz 							                # Extract
    mv neru_darwin_amd64 neru 							                        # rename
    chmod +x ./neru									                            # Pemmrions 
    sudo mv ./neru /usr/local/bin 								                # move 
    rm ./neru_darwin_amd64.tar.gz							                    # rm old file

Local debug :
    neru debug
    make deploy 

Workspace debug:
    vcr debug 
    make deploy 

Clear open ports:
    sudo apt install lsof
    lsof -ti:9229  [port number]
    




 



