FROM openjdk:8

# Copy required build media
ADD AEM_6.3_Quickstart.jar /opt/cq/AEM_6.3_Quickstart.jar
ADD license.properties /opt/cq/license.properties

# Extract AEM
WORKDIR /opt/cq
RUN java -XX:MaxPermSize=256m -Xms6144m -Xmx6144m -jar AEM_6.3_Quickstart.jar -unpack -p 4502 -debug 30303 -r author -forkargs -- -Xms6144m -Xmx6144m

EXPOSE 4502
CMD crx-quickstart/bin/quickstart