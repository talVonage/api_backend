# Build node modules 
cd  /Users/tshany/Documents/gmail_vonage/code/vonage_202309/api_backend/ui_assets
npm run dev

# VCR Configuration
https://developer.vonage.com/en/vcr/getting-started/working-locally?lang=macos

Install - MacOs 
open terminal
sudo chown -R $(whoami) /usr/local/bin
sudo curl -L https://raw.githubusercontent.com/Vonage/cloud-runtime-cli/main/script/install.sh | sh

vcr configure
    api key: 292e6c87
    api secret: e2IN2xM3Amwx0Ktg
vcr upgrade
vcr deply 


create new project:
cd /Users/tshany/Documents/gmail_vonage/code/vonage_202309/api_backend
vcr init


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

GitHub Repo:
    https://github.com/talVonage/api_backend


cd /Users/tshany/Documents/gmail_vonage/code/vonage_202309/api_backend
    Local debug :
        neru debug
        make deploy 

    Workspace debug:
        vcr debug 
        make deploy 

Clear open ports:
    sudo apt install lsof
    lsof -ti:9229  [port number]

Meta APIs 
Create a developer account : 
    https://developers.facebook.com/async/registration/dialog/?src=default
    https://developers.facebook.com/


Create certificate:
  - Used default properties. create cert.pem and key.pem under ssl_certificate folder 
cd /Users/tshany/Documents/gmail_vonage/code/vonage_202309/api_backend/backend/certs
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
   
