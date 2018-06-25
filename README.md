# AEM & Docker getting started guide

Getting started guide for development with [Adobe Experience Manager](https://www.adobe.com/nl/marketing-cloud/experience-manager.html) together with Docker. The configuration contains an AEM author, publisher and dispatcher environment, running in three separate containers. Docker images also have support for installing AEM packages during build.

## Prerequisites

This tutorial assumes running on a Mac. Installation on Windows might differ for certain steps. The following items are required:

- [Docker](https://www.docker.com) with at least 8GB memory allocated
- AEM installation file, named `AEM_6.2_Quickstart.jar` or `AEM_6.3_Quickstart.jar` (other versions might work, but are not tested)
- AEM license file, named `license.properties`
- Recommended: [Homebrew](https://brew.sh) package manager

## Getting started: running AEM

1. Clone this repository to a local directory and put the AEM installation file and license file in the root.
2. Put AEM packages that need to be installed during build in `./author/packages/` and `./publisher/packages/`. Order of installation will be alphabetically, based on package file name.
3. Build the Docker images with `docker build -t aem-base -f base/Dockerfile . && docker-compose build`. This takes a couple of minutes, as the author and publisher are started during build to be able to install packages.
4. Start the Docker containers with `docker-compose up`. This will also mount the `./logs` directory on your local system to the containers, so you have easy access to the logs of all containers.
5. Wait until AEM has fully started. To check for the author, open the [bundles JSON page](http://localhost:4502/system/console/bundles.1.json) and when the total number of bundles is equal to the active bundles, the AEM environment has fully started.
6. Navigate to [http://localhost:4502](http://localhost:4502) and you'll see a login screen. Login with username `admin` and password `admin`. Navigate to [http://localhost](http://localhost) to see the published site via the dispatcher. The publisher runs on [http://localhost:4503](http://localhost:4503).

Starting and stopping containers preserves AEM content. Images need to be rebuild when changing packages in the `packages` directories. After stopping a container, or after a system reboot, you can be quickly up-and-running again by starting the containers with `docker-compose up`.

## Getting started: set-up development environment

1. Install Java 8 SDK: `brew cask install java8`.
2. Install Maven: `brew install maven`.
3. Download and install IntelliJ IDEA from [JetBrains](https://www.jetbrains.com/idea/download) or install with `brew cask install caskroom/cask/intellij-idea-ce`.
4. Clone the [AEM We.Retail sample](https://github.com/Adobe-Marketing-Cloud/aem-sample-we-retail) repository to a local directory.
5. Open the folder with the AEM We.Retail sample in IntelliJ. In IntelliJ, click on the right-top corner on the dropdown and select `Edit Configurations`. Add a `New Configuration` with the plus-icon on the top-left corner, select `Maven`. Set the name as `Deploy author`, set the working directory as `aem-sample-we-retail`, command line `clean install -e` and profiles `autoInstallPackage`. Now save the configuration.
6. Click on the play button on the top-right corner to run the `Deploy author` configuration. You might get an error that the Java JDK can't be found: `Project JDK is not specified`. When this occurs, click on `Configure` next to the error and specify the location of your Java SDK (for instance, `/Library/Java/JavaVirtualMachines/jdk1.8.0_162.jdk/`). Now try again to run the `Deploy author` configuration and you should see a success message.
7. Navigate to the [AEM Package Manager](http://localhost:4502/crx/packmgr/index.jsp) and you should see the `we.retail.*` packages on top of the list.

## Other tools

- [aem-front](https://github.com/kevinweber/aem-front) can be used to significantly speed-up your AEM front-end development workflow, as code changes will hot-reload in your browser.

## Credits

Inspiration and code examples are taken from the following projects:

- [https://github.com/AdobeAtAdobe/aem_6-1_docker](https://github.com/AdobeAtAdobe/aem_6-1_docker)
- [https://hub.docker.com/r/ggotti/aem-base](https://hub.docker.com/r/ggotti/aem-base)
- [https://github.com/adfinis-sygroup/aem-docker](https://github.com/adfinis-sygroup/aem-docker)
