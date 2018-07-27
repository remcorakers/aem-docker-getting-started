FROM aem-base

WORKDIR /opt/aem

COPY ./publisher/packages/* /opt/aem/packages/

RUN python aem_installer.py -i AEM_6.x_Quickstart.jar -r publish,nosamplecontent,local -p 4503

EXPOSE 4503
CMD java -Xms4g -Xmx4g -Djava.awt.headless=true -Xdebug -Xnoagent -agentlib:jdwp=transport=dt_socket,address=30304,server=y,suspend=n -jar AEM_6.x_Quickstart.jar -p 4503 -r publish,nosamplecontent,local -v -nofork