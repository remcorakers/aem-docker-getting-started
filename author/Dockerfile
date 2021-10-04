FROM aem-base

WORKDIR /opt/aem

COPY ./author/packages/* /opt/aem/packages/

RUN python aem_installer.py -i AEM_6.x_Quickstart.jar -r author,nosamplecontent,local -p 4502

EXPOSE 4502
CMD java -Xms4g -Xmx4g -Djava.awt.headless=true -Xdebug -Xnoagent -agentlib:jdwp=transport=dt_socket,address=30303,server=y,suspend=n -jar AEM_6.x_Quickstart.jar -p 4502 -r author,nosamplecontent,local -v -nofork
