FROM centos:7

# Install packages
RUN yum -y install epel-release && yum clean all
RUN yum -y --enablerepo=centosplus update \
    && yum install -y \
      tar \
      wget \
      java-1.8.0-openjdk \
      libselinux-devel \
      epel-release \
      ipython3 \
      python-pip \
      python-psutil \
      python-pycurl \
    && yum clean all \
    && rm -rf /var/cache/yum

# Copy required build media
COPY ./AEM_6.2_Quickstart.jar /opt/aem/AEM_6.2_Quickstart.jar
COPY ./license.properties /opt/aem/license.properties

# Extract AEM
WORKDIR /opt/aem
RUN java -Djava.awt.headless=true -Xms4096m -Xmx4096m -jar AEM_6.2_Quickstart.jar -unpack

# Install utility for AEM
COPY ./base/aemInstaller.py /opt/aem/aemInstaller.py