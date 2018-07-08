FROM centos:7

# Install packages
# ld-linux.so.2, glibc.i686 and libuuid.i686 are added to enable XMP extraction and write-back on 64-bit RedHat Linux
# See https://helpx.adobe.com/experience-manager/kb/enable-xmp-write-back-64-bit-redhat.html.
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
      ld-linux.so.2 \
      glibc.i686 \
      libuuid.i686 \
    && yum clean all \
    && rm -rf /var/cache/yum

# Copy required build media
COPY ./AEM_6.*_Quickstart.jar /opt/aem/AEM_6.x_Quickstart.jar
COPY ./license.properties /opt/aem/license.properties

# Extract AEM
WORKDIR /opt/aem
RUN java -Djava.awt.headless=true -Xms4096m -Xmx4096m -jar AEM_6.x_Quickstart.jar -unpack

# Install utility for AEM
COPY ./base/aemInstaller.py /opt/aem/aemInstaller.py
COPY ./base/helpers.py /opt/aem/helpers.py