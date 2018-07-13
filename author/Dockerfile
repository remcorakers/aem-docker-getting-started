FROM aem-base

WORKDIR /opt/aem

COPY ./author/packages/* /opt/aem/packages/

RUN python aem_installer.py -i AEM_6.x_Quickstart.jar -r author,nosamplecontent -p 4502

EXPOSE 4502
CMD java -Xms4g -Xmx4g -Djava.awt.headless=true -jar AEM_6.x_Quickstart.jar -p 4502 -debug 30303 -r author,nosamplecontent -v -nofork