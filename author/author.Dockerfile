FROM openjdk:8

# Copy required build media
COPY ./AEM_6.3_Quickstart.jar /opt/cq/AEM_6.3_Quickstart.jar
COPY ./license.properties /opt/cq/license.properties

# Extract AEM
WORKDIR /opt/cq
RUN java -Djava.awt.headless=true -Xms4096m -Xmx4096m -jar AEM_6.3_Quickstart.jar -unpack

EXPOSE 4502
CMD java -Xms4096m -Xmx4096m -jar AEM_6.3_Quickstart.jar -p 4502 -debug 30303 -r author -v