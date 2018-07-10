FROM aem-base

WORKDIR /opt/aem

COPY ./publisher/post_install_hook.py /opt/aem/post_install_hook.py
COPY ./publisher/packages/* /opt/aem/packages/

RUN python aem_installer.py -i AEM_6.x_Quickstart.jar -r publish,nosamplecontent -p 4503

EXPOSE 4503
CMD java -Xms4g -Xmx4g -Djava.awt.headless=true -jar AEM_6.x_Quickstart.jar -p 4503 -debug 30304 -r publish,nosamplecontent -v -nofork