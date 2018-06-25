FROM aem-base

WORKDIR /opt/aem

COPY ./author/postInstallHook.py /opt/aem/postInstallHook.py
COPY ./author/packages/* /opt/aem/packages/

RUN python aemInstaller.py -i AEM_6.x_Quickstart.jar -r author -p 4502

EXPOSE 4502
CMD java -Xms4096m -Xmx4096m -Djava.awt.headless=true -jar AEM_6.x_Quickstart.jar -p 4502 -debug 30303 -r author -v